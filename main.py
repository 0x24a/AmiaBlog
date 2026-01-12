from typing import Literal, Optional
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from utils import (
    load_config,
    get_amiablog_version,
    TemplateRenderer,
    PostsManager,
    I18nProvider,
    HLJSLanguageManager,
    RSSProvider,
)
import time

__VERSION__ = get_amiablog_version()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

config = load_config()
hljs_manager = HLJSLanguageManager(config.site_settings.hljs_languages)
posts_manager = PostsManager(search_method=config.search_method)
i18n = I18nProvider(config.site_language)
renderer = TemplateRenderer(
    disable_cache=config.disable_template_cache,
    static_params={
        "config": config,
        "i18n": i18n,
        "backend_version": __VERSION__,
        "total_posts": len(posts_manager.posts),
        "copyright": config.copyright,
    },
)
rss_provider = RSSProvider(config, posts_manager)


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/")
async def mainpage():
    return renderer.render("index.html", recent_posts=posts_manager.recent_posts())


@app.get("/feed")
async def rss():
    return Response(
        rss_provider.generate_rss(),
        media_type="application/rss+xml; charset=utf-8",
    )


@app.get("/post/{slug}")
async def view_post(slug: str):
    post = posts_manager.posts.get(slug)
    if post is None:
        return renderer.render(
            "error.html", status_code=404, error=i18n.error_post_not_found
        )
    hljs_languages = hljs_manager.get_markdown_languages(post.content)
    available_languages = [
        i for i in hljs_languages if i in hljs_manager.available_languages
    ]
    return renderer.render("post.html", post=post, hljs_languages=available_languages)


@app.get("/posts")
async def view_posts(
    order: Optional[Literal["date", "date_desc", "modified", "modified_desc"]] = None
):
    if not order:
        order = "modified_desc"
    posts = posts_manager.order_by(list(posts_manager.posts.values()), order)
    return renderer.render("posts.html", posts=posts, order=order)


@app.get("/tag/{tag:str}")
async def view_tag(tag: str):
    posts = posts_manager.order_by(posts_manager.get_posts_by_tag(tag), "modified_desc")
    if len(posts) == 0:
        return renderer.render(
            "error.html", status_code=404, error=i18n.error_tag_not_found
        )
    return renderer.render("tag.html", posts=posts, tag=tag)


@app.get("/tags")
async def view_tags():
    tags = posts_manager.list_tags(order_by="post_count")
    return renderer.render("tags.html", tags=tags, n_tags=len(tags))


@app.get("/search")
async def view_search(
    query: Optional[str] = None,
    order: Optional[
        Literal["relevance", "modified", "modified_desc", "date", "date_desc"]
    ] = None,
):
    if query is None or not order:
        return renderer.render(
            "search.html",
            finished=False,
            order="relevance" if config.search_method == "jieba" else "modified_desc",
        )
    if order == "relevance" and config.search_method == "fullmatch":
        return renderer.render(
            "error.html", status_code=400, error=i18n.error_relevance_in_fullmatch
        )
    query = query.strip()
    if len(query) < 1 or len(query) > 50:
        return renderer.render(
            "error.html", status_code=400, error=i18n.error_invalid_query
        )
    start_time = time.time()
    search_results = posts_manager.search(query)
    end_time = time.time()
    if order != "relevance":
        search_results = posts_manager.order_by(search_results, order)
    return renderer.render(
        "search.html",
        finished=True,
        query=query,
        posts=search_results,
        n_posts=len(search_results),
        order=order,
        search_time=round((end_time - start_time) * 1000, 4),
    )

@app.get("/friend-links")
async def view_friend_links():
    if not config.friend_links:
        return renderer.render("error.html", status_code=404, error=i18n.error_not_found)
    return renderer.render("friend_links.html", friend_links=config.friend_links)

@app.get("/api/health")
async def root():
    return {"status": "ok", "server": "AmiaBlog", "version": __VERSION__}
