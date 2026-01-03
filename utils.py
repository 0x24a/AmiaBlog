from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

class SiteSettings(BaseModel):
    title: str
    description: str
    keywords: str
    color_scheme: str = "DDAACC"

class Config(BaseModel):
    site_settings: SiteSettings
    site_language: str
    
    # Debug flags
    disable_template_cache: bool = False

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
    