import sys
from utils import (
    load_config,
    get_amiablog_version,
    get_platform_string,
    TemplateRenderer,
    PostsManager,
    I18nProvider,
    HLJSLanguageManager,
    RSSProvider,
)
import os
import time
import shutil
import argparse
from loguru import logger

__VERSION__ = get_amiablog_version()
DESTINATION = "dist/"


class AmiaBlogStaticGenerator:
    def __init__(self, destination: str, remove_existing: bool = False):
        self.destination = destination
        self.remove_existing = remove_existing

    def load_data(self):
        self.config = load_config()
        self.hljs_manager = HLJSLanguageManager(
            self.config.site_settings.hljs_languages
        )
        self.posts_manager = PostsManager(
            search_method="fullmatch", build_search_index=False
        )
        self.i18n = I18nProvider(self.config.site_language)
        self.renderer = TemplateRenderer(
            disable_cache=True,
            static_params={
                "config": self.config,
                "i18n": self.i18n,
                "backend_version": (
                    (__VERSION__ if __VERSION__ else "unknown") + "-static"
                ),
                "total_posts": len(self.posts_manager.posts),
                "copyright": self.config.copyright,
                "is_static": True,
            },
        )
        self.rss_provider = RSSProvider(self.config, self.posts_manager)

    def init_dist_dir(self):
        if os.path.exists(self.destination):
            if not self.remove_existing:
                remove = input("Remove existing destination directory? (y/n): ")
                if remove.lower() != "y":
                    logger.info("Terminating static site generation process.")
                    exit(1)
            logger.warning("Removing existing destination directory")
            shutil.rmtree(self.destination)
        os.makedirs(self.destination)

    def init_static_assets(self):
        shutil.copytree("static", os.path.join(self.destination, "static"))
        shutil.copyfile(
            os.path.join(self.destination, "static", "favicon.ico"),
            os.path.join(self.destination, "favicon.ico"),
        )
        os.remove(os.path.join(self.destination, "static", "favicon.ico"))

    def render_top_layers(self):
        logger.info("\tRendering: RSS Feed")
        with open(os.path.join(self.destination, "feed.xml"), "w+") as f:
            f.write(self.rss_provider.generate_rss(is_static=True))
        logger.info("\tRendering: index.html")
        self.renderer.render_static(
            os.path.join(self.destination, "index.html"),
            "index.html",
            recent_posts=self.posts_manager.recent_posts(),
        )
        logger.info("\tRendering: posts.html")
        self.renderer.render_static(
            os.path.join(self.destination, "posts.html"),
            "posts.html",
            posts=self.posts_manager.order_by(
                list(self.posts_manager.posts.values()), "modified_desc"
            ),
        )
        logger.info("\tRendering: tags.html")
        tags = self.posts_manager.list_tags(order_by="post_count")
        self.renderer.render_static(
            os.path.join(self.destination, "tags.html"),
            "tags.html",
            tags=tags,
            n_tags=len(tags),
        )
        logger.info("\tRendering: 404.html (need extra configuration to work)")
        self.renderer.render_static(
            os.path.join(self.destination, "404.html"),
            "error.html",
            error=self.i18n.error_page_not_found,
        )

    def render_posts(self):
        if not self.posts_manager.posts:
            logger.warning("No posts found. Skipping.")
        else:
            os.mkdir(os.path.join(self.destination, "post"))
            for slug, post in self.posts_manager.posts.items():
                logger.info(f"\tRendering: post/{slug}.html")
                hljs_languages = self.hljs_manager.get_markdown_languages(post.content)
                available_languages = [
                    i
                    for i in hljs_languages
                    if i in self.hljs_manager.available_languages
                ]
                with open(
                    os.path.join(self.destination, f"post/{slug}.html"), "w+"
                ) as f:
                    f.write(
                        self.renderer.render_to_plain_text(
                            "post.html", post=post, hljs_languages=available_languages
                        )
                    )

    def render_tags(self):
        tags = self.posts_manager.list_tags()
        if not tags:
            logger.warning("No tags found. Skipping.")
        else:
            os.mkdir(os.path.join(self.destination, "tag"))
            for tag in tags:
                logger.info(f"\tRendering: tag/{tag.name}.html")
                posts = self.posts_manager.order_by(
                    self.posts_manager.get_posts_by_tag(tag.name), "modified_desc"
                )
                with open(
                    os.path.join(self.destination, f"tag/{tag.name}.html"), "w+"
                ) as f:
                    f.write(
                        self.renderer.render_to_plain_text(
                            "tag.html", tag=tag.name, posts=posts
                        )
                    )

    def write_build_info(self, build_time, build_time_usage):
        with open(os.path.join(self.destination, "amiablog_build_info.txt"), "w+") as f:
            f.write(
                f"software: AmiaBlog\nversion: {__VERSION__}\npython_version: {sys.version}\nplatform: {get_platform_string()}\nbuild_time: {build_time}\nbuild_time_usage: {round(build_time_usage,2)}ms\n"
            )

    def render(self):
        build_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        generate_start_time = time.time()
        logger.info(
            f"Generating static site with AmiaBlog v{__VERSION__} to {self.destination}"
        )
        logger.info("Loading site data")
        self.load_data()
        logger.info("Site data loaded successfully.")
        self.renderer.static_params.update({"static_build_time": build_time})
        self.init_dist_dir()
        logger.info("Copying static assets")
        self.init_static_assets()
        logger.info("Rendering top-layer pages")
        self.render_top_layers()
        logger.info("Rendering posts")
        self.render_posts()
        logger.info("Rendering tags")
        self.render_tags()
        generate_end_time = time.time()
        logger.info(
            f"Generation completed in {(generate_end_time - generate_start_time)*1000:.2f} ms. Writing amiablog_build_info.txt"
        )
        self.write_build_info(
            build_time, round((generate_end_time - generate_start_time) * 1000, 2)
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate AmiaBlog static site")
    parser.add_argument(
        "--destination", help="Destination directory", default="dist", required=False
    )
    parser.add_argument(
        "--remove-existing",
        action="store_true",
        help="Overwrite existing destination directory",
        default=False,
        required=False,
    )
    args = parser.parse_args()
    AmiaBlogStaticGenerator(args.destination, args.remove_existing).render()
