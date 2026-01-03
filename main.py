from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from utils import load_config, TemplateRenderer, PostsManager, I18nProvider

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

config = load_config()
renderer = TemplateRenderer(disable_cache=config.disable_template_cache)
posts_manager = PostsManager()
posts_manager.load_posts()

i18n = I18nProvider(config.site_language)

__VERSION__ = "0.1.0"


@app.get("/")
async def mainpage():
    return renderer.render(
        "index.html", config=config, recent_posts=posts_manager.recent_posts(), i18n=i18n
    )


@app.get("/api/health")
async def root():
    return {"status": "ok", "server": "AmiaBlog", "version": __VERSION__}
