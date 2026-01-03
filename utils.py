from typing import List, Literal, Tuple
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import yaml
import os

class SiteSettings(BaseModel):
    title: str
    description: str
    keywords: str
    color_scheme: str = "DDAACC"
    theme: Literal['auto', 'light', 'dark'] = "auto"

class Config(BaseModel):
    site_settings: SiteSettings
    site_language: str
    
    # Debug flags
    disable_template_cache: bool = False

class PostMetadata(BaseModel):
    title: str
    date: datetime
    last_modified: datetime
    tags: list[str]
    description: str
    published: bool
    author: str

def load_config(filename: str = "config.json") -> Config:
    with open(filename, "r") as f:
        return Config.model_validate_json(f.read())

class TemplateRenderer:
    def __init__(self, template_dir: str = "templates", disable_cache: bool = False) -> None:
        self.template_dir = template_dir
        self.disable_cache = disable_cache
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.templates = {}
    
    def render(self, template_name: str, **context) -> HTMLResponse:
        if self.disable_cache or template_name not in self.templates:
            self.templates[template_name] = self.env.get_template(template_name)
        return HTMLResponse(self.templates[template_name].render(**context))

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
        self.posts = {}
    
    def load_posts(self) -> None:
        for filename in os.listdir(self.posts_dir):
            if filename.endswith(".md"):
                with open(os.path.join(self.posts_dir, filename), "r") as f:
                    content = f.read()
                metadata, content = parse_post(content)
                self.posts[".".join(filename.split(".")[:-1])] = metadata, content
    
    def recent_posts(self, n: int = 5) -> List[Tuple[str, PostMetadata, str]]:
        sorted_items = sorted(self.posts.items(), key=lambda x: x[1][0].last_modified, reverse=True)[:n]
        return [(key, metadata, content) for key, (metadata, content) in sorted_items]
