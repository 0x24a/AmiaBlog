from fastapi import FastAPI
from utils import load_config, TemplateRenderer

app = FastAPI()
config = load_config()
renderer = TemplateRenderer(disable_cache=config.disable_template_cache)

__VERSION__ = "0.1.0"

@app.get("/")
async def mainpage():
    return renderer.render("index.html", config=config)

@app.get("/api/health")
async def root():
    return {"status": "ok", "server": "AmiaBlog", "version": __VERSION__}
