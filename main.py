from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from utils import load_config, TemplateRenderer, PostsManager, I18nProvider, HLJSLanguageManager

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

config = load_config()
renderer = TemplateRenderer(disable_cache=config.disable_template_cache)
hljs_manager = HLJSLanguageManager(config.site_settings.hljs_languages)
posts_manager = PostsManager()
posts_manager.load_posts()

i18n = I18nProvider(config.site_language)

__VERSION__ = "0.1.0"


@app.get("/")
async def mainpage():
    return renderer.render(
        "index.html", config=config, recent_posts=posts_manager.recent_posts(), i18n=i18n, backend_version=__VERSION__, total_posts=len(posts_manager.posts)
    )

@app.get("/post/{slug}")
async def view_post(slug: str):
    post = posts_manager.posts.get(slug)
    if post is None:
        return {"error": "Post not found"}
    hljs_languages = hljs_manager.get_markdown_languages(post.content)
    available_languages = [i for i in hljs_languages if i in hljs_manager.available_languages]
    return renderer.render(
        "post.html", config=config, post=post, i18n=i18n, backend_version=__VERSION__, total_posts=len(posts_manager.posts), hljs_languages=available_languages, copyright=config.copyright
    )


@app.get("/tag/{tag}")
async def view_tag(tag: str):
    posts = posts_manager.order_by(posts_manager.get_posts_by_tag(tag), "modified_desc")
    return renderer.render(
        "tag.html", config=config, posts=posts, i18n=i18n, backend_version=__VERSION__, total_posts=len(posts_manager.posts), tag=tag, copyright=config.copyright
    )

@app.get("/api/health")
async def root():
    return {"status": "ok", "server": "AmiaBlog", "version": __VERSION__}
