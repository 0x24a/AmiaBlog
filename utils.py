from typing import Callable, List, Literal, Optional, Tuple, Dict
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
import datetime
import yaml
import os
import htmlmin
import httpx
import json
from urllib.parse import quote


class SiteSettings(BaseModel):
    title: str
    description: str
    keywords: str
    color_scheme: str = "DDAACC"
    theme: Literal["auto", "light", "dark"] = "auto"
    hljs_languages: List[str] = []


class CopyrightSettings(BaseModel):
    name: str
    refer: str


class Config(BaseModel):
    site_settings: SiteSettings
    site_language: str
    copyright: Optional[CopyrightSettings] = None

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


class Post(BaseModel):
    metadata: PostMetadata
    content: str
    slug: str


def load_config(filename: str = "config.json") -> Config:
    with open(filename, "r") as f:
        return Config.model_validate_json(f.read())


class TemplateRenderer:
    def __init__(
        self, template_dir: str = "templates", disable_cache: bool = False
    ) -> None:
        self.template_dir = template_dir
        self.disable_cache = disable_cache
        self.env = Environment(
            loader=FileSystemLoader(template_dir), autoescape=select_autoescape()
        )
        self.env.filters["urlencode"] = lambda s: quote(s, safe="")
        self.templates = {}

    def render(self, template_name: str, **context) -> HTMLResponse:
        if self.disable_cache or template_name not in self.templates:
            self.templates[template_name] = self.env.get_template(template_name)
        rendered_html = self.templates[template_name].render(**context)
        return HTMLResponse(htmlmin.minify(rendered_html))


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
    metadata = PostMetadata.model_validate(yaml.safe_load("\n".join(metadata_lines)))
    return metadata, "\n".join(content_lines)


class PostsManager:
    def __init__(self, posts_dir: str = "posts") -> None:
        self.posts_dir = posts_dir
        self.posts: Dict[str, Post] = {}

    def load_posts(self) -> None:
        for filename in os.listdir(self.posts_dir):
            if filename.endswith(".md"):
                with open(os.path.join(self.posts_dir, filename), "r") as f:
                    content = f.read()
                metadata, content = parse_post(content)
                slug = ".".join(filename.split(".")[:-1])
                self.posts[slug] = Post(metadata=metadata, content=content, slug=slug)

    def recent_posts(self, n: int = 5) -> List[Post]:
        return self.order_by(
            self.get_posts(lambda post: post.metadata.published), "modified_desc"
        )[:n]

    def get_posts(self, selector: Callable[[Post], bool]) -> List[Post]:
        return [post for post in self.posts.values() if selector(post)]

    def search(self, keyword: str, limit: Optional[int] = None) -> List[Post]:
        results = self.get_posts(
            lambda post: keyword.lower() in post.metadata.title.lower()
            or keyword.lower() in [tag.lower() for tag in post.metadata.tags]
            or keyword.lower() in post.content.lower()
            and post.metadata.published
        )
        if limit is not None:
            results = results[:limit]
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
        print(f"[AmiaBlog] Downloading {len(undownloaded_languages)} HLJS languages...")
        for language in undownloaded_languages:
            try:
                response = httpx.get(f"{url_prefix}{language}.min.js")
                response.raise_for_status()
                with open(os.path.join(prefix, f"{language}.min.js"), "wb") as f:
                    f.write(response.content)
            except Exception as e:
                print(
                    f"[AmiaBlog] Failed to download {language}.min.js: {e}, skipping."
                )
            else:
                print(f"[AmiaBlog] Successfully downloaded {language}.min.js")
                self.available_languages.append(language)
        print("[AmiaBlog] Download complete!")

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
