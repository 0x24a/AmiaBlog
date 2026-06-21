from typing import Any, Dict
from urllib.parse import quote

import htmlmin
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape


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
        with open(destination, "w+", encoding="utf-8") as f:
            f.write(self.render_to_plain_text(template_name, **context))
        return destination
