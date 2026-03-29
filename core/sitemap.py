from core.posts import PostsManager
from core.models import Config


class SitemapProvider:
    def __init__(self, posts_manager: PostsManager, config: Config, is_static: bool):
        self.posts_manager = posts_manager
        self.config = config
        self.is_static = is_static

    def generate_sitemap(self) -> str:
        assert self.config.site_settings.site_url  # actually not necessary
        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]

        parts.append("  <url>")
        parts.append("    <loc>{}</loc>".format(self.config.site_settings.site_url))
        parts.append("  </url>")

        top_level_pages = ["posts", "tags"]
        if not self.is_static:
            top_level_pages.append("search")
        if self.config.friend_links:
            top_level_pages.append("friend-links")
        for page in top_level_pages:
            parts.append("  <url>")
            parts.append(
                "    <loc>{}</loc>".format(
                    self.config.site_settings.site_url
                    + page
                    + (".html" if self.is_static else "")
                )
            )
            parts.append("  </url>")

        for slug, post in self.posts_manager.posts.items():
            if not post.metadata.published:
                continue
            parts.append("  <url>")
            parts.append(
                "    <loc>{}</loc>".format(
                    self.config.site_settings.site_url
                    + "post/"
                    + slug
                    + (".html" if self.is_static else "")
                )
            )
            parts.append(
                "    <lastmod>{}</lastmod>".format(
                    post.metadata.last_modified.strftime("%Y-%m-%d")
                )
            )
            parts.append("  </url>")

        for name, _ in self.posts_manager.tags.items():
            posts = self.posts_manager.get_posts_by_tag(name)
            last_modified = max(post.metadata.last_modified for post in posts)
            parts.append("  <url>")
            parts.append(
                "    <loc>{}</loc>".format(
                    self.config.site_settings.site_url
                    + "tag/"
                    + name
                    + (".html" if self.is_static else "")
                )
            )
            parts.append(
                "    <lastmod>{}</lastmod>".format(last_modified.strftime("%Y-%m-%d"))
            )
            parts.append("  </url>")

        parts.append("</urlset>")

        return "\n".join(parts)
