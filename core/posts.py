import os
import sqlite3
import threading
import time
import jieba_fast
from typing import Callable, Dict, List, Literal, Optional, Tuple, Union
from hashlib import md5

from jieba_fast.finalseg import sys
import yaml
from loguru import logger
from core.models import PostMetadata, Post, Tag


def parse_post(filename: str, content: str) -> Tuple[PostMetadata, str]:
    """
    Parses a post from its content.

    Supports both formats:
    - Standard YAML front matter: content starting with "---", metadata, then "---"
    - Legacy format: metadata without delimiters at the start

    Args:
        filename (str): The filename of the post.
        content (str): The content of the post.

    Returns:
        Tuple[PostMetadata, str]: A tuple containing the metadata and the rest content of the post in markdown.
    """
    lines = content.split("\n")

    if lines and lines[0].strip() == "---":
        metadata_lines = []
        content_start_idx = None

        # Find the closing "---"
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                content_start_idx = i + 1
                break
            metadata_lines.append(line)

        if content_start_idx is None:
            logger.warning(
                f"Post '{filename}' starts with '---' but no closing delimiter found. "
                "Treating as legacy format. Please use proper YAML frontmatter: "
                "---\\nmetadata\\n---\\ncontent"
            )
            return _parse_legacy_format(content)

        metadata = yaml.safe_load("\n".join(metadata_lines))
        content_lines = lines[content_start_idx:]

    else:
        logger.warning(
            f"Post '{filename}' uses legacy format without YAML frontmatter delimiters. "
            "Please migrate to standard format: ---\\nmetadata\\n---\\ncontent"
        )
        return _parse_legacy_format(content)

    if isinstance(metadata.get("tags"), list):
        metadata["tags"] = [str(tag) for tag in metadata["tags"]]

    metadata = PostMetadata.model_validate(metadata)
    return metadata, "\n".join(content_lines)


def _parse_legacy_format(content: str) -> Tuple[PostMetadata, str]:
    """
    Parses post in legacy format (metadata without delimiters).

    Args:
        content (str): The content of the post.

    Returns:
        Tuple[PostMetadata, str]: A tuple containing the metadata and the rest content.
    """
    metadata_lines = []
    content_lines = []
    metadata_end = False
    for line in content.split("\n"):
        if line.strip() == "---":
            metadata_end = True
            continue
        if not metadata_end:
            metadata_lines.append(line)
        else:
            content_lines.append(line)
    metadata = yaml.safe_load("\n".join(metadata_lines))
    if isinstance(metadata.get("tags"), list):
        metadata["tags"] = [str(tag) for tag in metadata["tags"]]
    metadata = PostMetadata.model_validate(metadata)
    return metadata, "\n".join(content_lines)


class PostsManager:
    def __init__(
        self,
        posts_dir: str = "data/posts",
        search_method: Literal["fullmatch", "jieba"] = "fullmatch",
        build_search_index: bool = False,
        hot_reload: bool = True,
        hot_reload_interval: Union[int, float] = 1,
    ) -> None:
        self.posts_dir = posts_dir
        self.posts: Dict[str, Post] = {}
        self.tags: Dict[str, Tag] = {}
        self.build_search_index = build_search_index
        self.search_index: Optional[sqlite3.Connection] = None
        self.search_method: Literal["fullmatch", "jieba"] = search_method
        self.hot_reload: bool = hot_reload
        self.hot_reload_interval: Union[int, float] = hot_reload_interval
        self.reloading: bool = True
        self._post_reload_hook: Optional[
            Callable[[str, Optional[Post], Post], None]
        ] = None
        if self.search_method == "jieba":
            logger.info("Initializing jieba predix dict")
            jieba_fast.initialize()
        elif self.search_method == "fullmatch":
            pass
        else:
            raise ValueError("Invalid search method.")
        self.load_posts(build_search_index)
        if hot_reload:
            self.reload_thread = threading.Thread(target=self._reload_thread)
            self.reload_thread.start()

    def calculate_posts_signature(self) -> str:
        crypto = md5()
        for filename in os.listdir(self.posts_dir):
            if filename.endswith(".md"):
                crypto.update(filename.encode())
                with open(os.path.join(self.posts_dir, filename), "rb") as f:
                    crypto.update(f.read())
        return crypto.hexdigest()

    def _reload_thread(self):
        logger.info(
            f"Listening for changes every {self.hot_reload_interval} second(s)..."
        )
        last_signature = self.calculate_posts_signature()
        last_reload_time = time.time()
        while self.reloading:
            time.sleep(
                min(0.1, self.hot_reload_interval)
            )  # Avoid not being interrupted by the flag
            if (time.time() - last_reload_time) <= self.hot_reload_interval:
                continue
            current_signature = self.calculate_posts_signature()
            if current_signature != last_signature:
                logger.info("Post changes detected, reloading...")
                self.load_posts(self.build_search_index)
                last_signature = current_signature

    def load_posts(self, build_search_index: bool = True) -> None:
        posts_before = None
        if self._post_reload_hook:
            posts_before = {slug: post for slug, post in self.posts.items()}
        # Clear posts & db
        self.posts.clear()
        self.tags.clear()
        if self.search_index:
            del self.search_index
            self.search_index = None
        logger.info("Loading posts")
        start_time = time.time()
        try:
            files = os.listdir(self.posts_dir)
        except FileNotFoundError as _:
            if self.posts_dir == "data/posts" and os.path.isdir("posts"):
                logger.error(
                    "...\nError: the default posts directory has been changed to data/posts (in commit 647887d).\nPlease do a migration."
                )
                sys.exit(1)
            else:
                raise

        for filename in files:
            if filename.endswith(".md"):
                with open(os.path.join(self.posts_dir, filename), "r") as f:
                    file_content = f.read()
                try:
                    metadata, content = parse_post(filename, file_content)
                except Exception as e:
                    logger.error(f"Error parsing post {filename}, ignoring: {e}")
                    continue
                if not metadata.published:
                    continue
                slug = ".".join(filename.split(".")[:-1])
                self.posts[slug] = Post(
                    metadata=metadata,
                    content=content,
                    slug=slug,
                    original_content=file_content,
                )
        end_time = time.time()
        logger.info(
            f"Loaded {len(self.posts)} posts in {(end_time - start_time)*1000:.4f}ms"
        )
        logger.info("Building tag index")
        start_time = time.time()
        self._build_tag_index()
        end_time = time.time()
        logger.info(f"Built tag index in {(end_time - start_time)*1000000:.4f}us")
        if build_search_index:
            logger.info("Building search index")
            start_time = time.time()
            self._build_search_index()
            end_time = time.time()
            logger.info(f"Built search index in {(end_time - start_time)*1000:.4f}ms")
        logger.info("Finished loading posts")
        if self._post_reload_hook:
            # Yes! I know this is NOT graceful! But since it's a dev-environment-only feature,
            #   and it just works, I don't see any problem.
            logger.debug("Invoking post reload hook")
            assert posts_before is not None
            for slug, post in self.posts.items():
                if slug not in posts_before:
                    self._post_reload_hook(slug, None, post)
                else:
                    self._post_reload_hook(slug, posts_before[slug], post)

    def _build_tag_index(self):
        for post in self.posts.values():
            for tag in post.metadata.tags:
                if tag not in self.tags:
                    self.tags[tag] = Tag(name=tag, count=1)
                else:
                    self.tags[tag].count += 1

    def _build_search_index(self):
        db = sqlite3.connect(":memory:")
        cursor = db.cursor()
        cursor.execute(
            "CREATE TABLE posts (id INTEGER PRIMARY KEY, slug TEXT, title TEXT, tags TEXT, content TEXT, keywords TEXT)"
        )
        for post in self.posts.values():
            cursor.execute(
                "INSERT INTO posts (slug, title, tags, content, keywords) VALUES (?, ?, ?, ?, ?)",
                (
                    post.slug,
                    post.metadata.title.lower(),
                    ",".join(post.metadata.tags).lower(),
                    post.content.lower(),
                    ",".join(post.metadata.keywords).lower(),
                ),
            )
        db.commit()
        self.search_index = db

    def list_tags(
        self, order_by: Literal["default", "post_count"] = "default"
    ) -> List[Tag]:
        if order_by == "default":
            return list(self.tags.values())
        elif order_by == "post_count":
            return sorted(
                list(self.tags.values()), key=lambda tag: tag.count, reverse=True
            )

    def recent_posts(self, n: int = 5) -> List[Post]:
        return self.order_by(list(self.posts.values()), "modified_desc")[:n]

    def get_posts(self, selector: Callable[[Post], bool]) -> List[Post]:
        return [post for post in self.posts.values() if selector(post)]

    def search(self, keyword: str) -> List[Post]:
        if self.search_index is None:
            raise ValueError("Search index not built.")
        logger.info(
            f"Performing '{self.search_method}' search within {len(self.posts)} post(s)"
        )
        start_time = time.time()
        if self.search_method == "fullmatch":
            cursor = self.search_index.cursor()
            keyword = keyword.lower()
            cursor.execute(
                "SELECT slug FROM posts WHERE slug LIKE ? OR title LIKE ? OR tags LIKE ? OR keywords LIKE ?",
                (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"),
            )
            results = [self.posts[row[0]] for row in cursor.fetchall()]
        elif self.search_method == "jieba":
            keywords = jieba_fast.lcut(keyword.lower())
            cursor = self.search_index.cursor()
            hits: Dict[str, int] = {}
            for kw in keywords:
                cursor.execute(
                    "SELECT slug FROM posts WHERE title LIKE ? OR tags LIKE ? OR content LIKE ? OR keywords LIKE ?",
                    (f"%{kw}%", f"%{kw}%", f"%{kw}%", f"%{kw}%"),
                )
                for row in cursor.fetchall():
                    slug = row[0]
                    hits[slug] = hits.get(slug, 0) + 1
            sorted_slugs = sorted(
                hits.keys(), key=lambda slug: hits[slug], reverse=True
            )
            results = [self.posts[slug] for slug in sorted_slugs]
        else:
            raise ValueError("Invalid search method.")
        end_time = time.time()
        logger.info(
            f"Search completed in {(end_time - start_time)*1000:.4f} milliseconds returning {len(results)} result(s)"
        )
        return results

    def get_posts_by_tag(self, tag: str, limit: Optional[int] = None) -> List[Post]:
        results = self.get_posts(
            lambda post: tag.lower() in [tag.lower() for tag in post.metadata.tags]
        )
        if limit is not None:
            results = results[:limit]
        return results

    def order_by(
        self,
        posts: List[Post],
        key: Literal["date", "date_desc", "modified", "modified_desc"],
    ):
        if key == "date":
            return sorted(posts, key=lambda x: x.metadata.date)
        elif key == "date_desc":
            return sorted(posts, key=lambda x: x.metadata.date, reverse=True)
        elif key == "modified":
            return sorted(posts, key=lambda x: x.metadata.last_modified)
        elif key == "modified_desc":
            return sorted(posts, key=lambda x: x.metadata.last_modified, reverse=True)
        else:
            raise ValueError(f"Invalid key: {key}")
