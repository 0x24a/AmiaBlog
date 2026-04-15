import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel
from loguru import logger


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


class ICPSettings(BaseModel):
    description: str
    url: str


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
    icp: Optional[ICPSettings] = None

    # Debug flags
    disable_template_cache: bool = False
    live_preview: bool = False


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
    original_content: str
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
        config.site_settings.site_url = "https://example.com/"
    if not config.site_settings.site_url.endswith("/"):
        config.site_settings.site_url += "/"
    return config
