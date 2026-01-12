import datetime
import json
import os
import sqlite3
import time
import jieba_fast
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple
from urllib.parse import quote

import htmlmin
import httpx
import yaml
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape
from pydantic import BaseModel
from loguru import logger
import platform


class SiteSettings(BaseModel):
    title: str
    description: str
    keywords: str
    site_url: Optional[str] = None
    color_scheme: str = "DDAACC"
    theme: Literal["auto", "light", "dark"] = "auto"
    hljs_languages: List[str] = []


class CopyrightSettings(BaseModel):
    name: str
    refer: str

class FriendLinkItem(BaseModel):
    name: str
    url: str
    description: str


class Config(BaseModel):
    site_settings: SiteSettings
    site_language: str
    copyright: Optional[CopyrightSettings] = None
    search_method: Literal["fullmatch", "jieba"] = "fullmatch"
    cloudflare_analytics_token: Optional[str] = None
    friend_links: Optional[List[FriendLinkItem]] = None

    # Debug flags
    disable_template_cache: bool = False


class PostMetadata(BaseModel):
    title: str
    date: datetime.date
    last_modified: datetime.date
    tags: list[str]
    description: str
    published: bool
    author: str
    keywords: list[str] = []


class Post(BaseModel):
    metadata: PostMetadata
    content: str
    slug: str


class Tag(BaseModel):
    name: str
    count: int


def load_config(filename: str = "config.json") -> Config:
    with open(filename, "r") as f:
        config = Config.model_validate_json(f.read())
    if config.site_settings.site_url is None:
        logger.warning(
            "config.site_settings.site_url is not set. RSS feed might break. Using https://example.com/"
        )
    return config


class TemplateRenderer:
    def __init__(
        self,
        template_dir: str = "templates",
        disable_cache: bool = False,
        static_params: Dict[str, Any] = {},
    ) -> None:
        self.template_dir = template_dir
        self.disable_cache = disable_cache
        self.env = Environment(
            loader=FileSystemLoader(template_dir), autoescape=select_autoescape()
        )
        self.env.filters["urlencode"] = lambda s: quote(s, safe="")
        self.templates = {}
        self.static_params = static_params

    def render_to_plain_text(self, template_name: str, **context) -> str:
        if self.disable_cache or template_name not in self.templates:
            self.templates[template_name] = self.env.get_template(template_name)
        context.update(self.static_params)
        rendered_text = self.templates[template_name].render(**context)
        return htmlmin.minify(rendered_text)

    def render(
        self, template_name: str, status_code: int = 200, **context
    ) -> HTMLResponse:
        rendered_html = self.render_to_plain_text(template_name, **context)
        return HTMLResponse(rendered_html, status_code=status_code)

    def render_static(self, destination: str, template_name: str, **context) -> str:
        with open(destination, "w+") as f:
            f.write(self.render_to_plain_text(template_name, **context))
        return destination


def parse_post(content: str) -> Tuple[PostMetadata, str]:
    """
    Parses a post from its content.

    Args:
        content (str): The content of the post.

    Returns:
        Tuple[PostMetadata, str]: A tuple containing the metadata and the rest content of the post (hopefully) in markdown.
    """
    metadata_lines = []
    content_lines = []
    metadata_end = False
    for line in content.split("\n"):
        if line == "---":
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


def get_amiablog_version():
    with open("pyproject.toml", "r") as f:
        content = f.read()
        for line in content.split("\n"):
            if line.startswith("version"):
                return line.split("=")[1].strip().strip('"')


def get_platform_string():
    os_name = platform.system().lower()
    os_map = {"darwin": "macos", "linux": "linux", "windows": "windows"}
    final_os = os_map.get(os_name, os_name)

    arch = platform.machine().lower()
    arch_map = {
        "arm64": "aarch64",
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "aarch64": "aarch64",
    }
    final_arch = arch_map.get(arch, arch)

    return f"{final_os}-{final_arch}-none"


class PostsManager:
    def __init__(
        self,
        posts_dir: str = "posts",
        search_method: Literal["fullmatch", "jieba"] = "fullmatch",
        build_search_index: bool = True,
    ) -> None:
        self.posts_dir = posts_dir
        self.posts: Dict[str, Post] = {}
        self.tags: Dict[str, Tag] = {}
        self.search_index: Optional[sqlite3.Connection] = None
        self.search_method: Literal["fullmatch", "jieba"] = search_method
        if self.search_method == "jieba":
            logger.info("Initializing jieba predix dict")
            jieba_fast.initialize()
        elif self.search_method == "fullmatch":
            pass
        else:
            raise ValueError("Invalid search method.")
        self.load_posts(build_search_index)

    def load_posts(self, build_search_index: bool = True) -> None:
        # Clear posts & db
        self.posts.clear()
        self.tags.clear()
        if self.search_index:
            self.search_index.close()
            self.search_index = None
        logger.info("Loading posts")
        start_time = time.time()
        for filename in os.listdir(self.posts_dir):
            if filename.endswith(".md"):
                with open(os.path.join(self.posts_dir, filename), "r") as f:
                    content = f.read()
                try:
                    metadata, content = parse_post(content)
                except Exception as e:
                    logger.error(f"Error parsing post {filename}, ignoring: {e}")
                    continue
                if not metadata.published:
                    continue
                slug = ".".join(filename.split(".")[:-1])
                self.posts[slug] = Post(metadata=metadata, content=content, slug=slug)
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


class I18nTerm:
    def __init__(self, key: str, term: Optional[str]):
        self.key = key
        self.term = term

    def __str__(self):
        return self.term if self.term is not None else f"<untranslated {self.key}>"

    def __repr__(self):
        return f"I18nTerm({self.key}, {self.term})"

    def format(self, *args, **kwargs):
        if self.term is None:
            return f"<untranslated {self.key}>"
        # Use Markup.format which automatically escapes arguments
        return Markup(self.term).format(*args, **kwargs)


class I18nProvider:
    def __init__(self, language: str = "en") -> None:
        self.language = language
        self.translations = {}
        self.load_translations()

    def load_translations(self) -> None:
        with open(f"languages/{self.language}.json", "r") as f:
            terms = json.load(f)
        self.translations = {key: I18nTerm(key, term) for key, term in terms.items()}

    def __getattr__(self, key: str) -> I18nTerm:
        return self.translations.get(key, I18nTerm(key, None))


class HLJSLanguageManager:
    def __init__(self, languages: List[str]):
        self.languages = languages
        self.available_languages = []
        self.download()

    def download(
        self,
        prefix: str = "static/hljs_11.1.1",
        url_prefix: str = "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.11.1/build/languages/",
    ):
        undownloaded_languages = []
        files = os.listdir(prefix)
        for language in self.languages:
            if f"{language}.min.js" not in files:
                undownloaded_languages.append(language)
            else:
                self.available_languages.append(language)
        if not undownloaded_languages:
            return
        logger.info(f"Downloading {len(undownloaded_languages)} HLJS languages...")
        for language in undownloaded_languages:
            try:
                response = httpx.get(f"{url_prefix}{language}.min.js")
                response.raise_for_status()
                with open(os.path.join(prefix, f"{language}.min.js"), "wb") as f:
                    f.write(response.content)
            except Exception as e:
                logger.warning(f"Failed to download {language}.min.js: {e}, skipping.")
            else:
                logger.info(f"Successfully downloaded {language}.min.js")
                self.available_languages.append(language)
        logger.info("Download complete!")

    def get_markdown_languages(self, markdown_text: str):
        languages = []
        lines = markdown_text.splitlines()

        for line in lines:
            clean_line = line.lstrip()
            if clean_line.startswith("```"):
                language_tag = clean_line[3:].strip()
                if language_tag:
                    lang = language_tag.split()[0]
                    languages.append(lang)

        return languages


class RSSProvider:
    def __init__(self, config: Config, posts_manager: PostsManager):
        self.config = config
        self.posts_manager = posts_manager

    def _format_rfc822_date(self, dt: datetime.date) -> str:
        dt_datetime = datetime.datetime(dt.year, dt.month, dt.day, 12, 0, 0)
        return dt_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")

    def generate_rss(self, limit: Optional[int] = None, is_static: bool = False) -> str:
        site_settings = self.config.site_settings
        if site_settings.site_url is None:
            site_url = "https://example.com"
        else:
            site_url = site_settings.site_url.rstrip("/")

        posts = self.posts_manager.order_by(
            list(self.posts_manager.posts.values()), "modified_desc"
        )
        if limit is not None:
            posts = posts[:limit]

        # Build channel info
        channel_title = escape(site_settings.title)
        channel_description = escape(site_settings.description)
        channel_link = escape(site_url)

        # Use current time as lastBuildDate
        last_build_date = self._format_rfc822_date(datetime.date.today())

        # Start building RSS XML
        rss_parts = []
        rss_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
        rss_parts.append(
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">'
        )
        rss_parts.append("  <channel>")
        rss_parts.append(f"    <title>{channel_title}</title>")
        rss_parts.append(f"    <description>{channel_description}</description>")
        rss_parts.append(f"    <link>{channel_link}</link>")
        rss_parts.append(f"    <lastBuildDate>{last_build_date}</lastBuildDate>")
        rss_parts.append(
            f"    <generator>AmiaBlog {get_amiablog_version()}</generator>"
        )

        # Add atom:self link
        rss_parts.append(
            f'    <atom:link href="{channel_link}/feed" rel="self" type="application/rss+xml" />'
        )
        rss_parts.append(
            f"    <language>{escape(self.config.site_language)}</language>"
        )
        if self.config.copyright:
            rss_parts.append(
                f"    <copyright>{escape(self.config.copyright.name)} {escape(self.config.copyright.refer)}</copyright>"
            )

        # Add items for each post
        for post in posts:
            post_url = f"{site_url}/post/{post.slug}"
            if is_static:
                post_url += ".html"
            title = escape(post.metadata.title)
            description = escape(post.metadata.description)
            pub_date = self._format_rfc822_date(post.metadata.date)
            author = escape(post.metadata.author)
            guid = escape(post_url)

            rss_parts.append("    <item>")
            rss_parts.append(f"      <title>{title}</title>")
            rss_parts.append(f"      <link>{post_url}</link>")
            rss_parts.append(f"      <description>{description}</description>")
            rss_parts.append(f"      <pubDate>{pub_date}</pubDate>")
            rss_parts.append(f"      <guid>{guid}</guid>")
            rss_parts.append(f"      <author>{author}</author>")
            rss_parts.append(
                f'      <content:encoded xml:lang="{escape(self.config.site_language)}"><![CDATA[{post.content}]]></content:encoded>'
            )
            # Add categories (tags)
            for tag in post.metadata.tags:
                escaped_tag = escape(tag)
                rss_parts.append(f"      <category>{escaped_tag}</category>")
            rss_parts.append("    </item>")

        rss_parts.append("  </channel>")
        rss_parts.append("</rss>")

        return "\n".join(rss_parts)
