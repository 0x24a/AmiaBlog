import datetime
from typing import Optional

from markupsafe import escape
from core.models import Config
from core.posts import PostsManager
from core.system import get_amiablog_version


class RSSProvider:
    def __init__(self, config: Config, posts_manager: PostsManager):
        self.config = config
        self.posts_manager = posts_manager

    def _format_rfc822_date(self, dt: datetime.date) -> str:
        dt_datetime = datetime.datetime(dt.year, dt.month, dt.day, 12, 0, 0)
        return dt_datetime.strftime("%a, %d %b %Y %H:%M:%S GMT")

    def generate_rss(self, limit: Optional[int] = None, is_static: bool = False) -> str:
        site_settings = self.config.site_settings
        if site_settings.site_url is None:
            site_url = "https://example.com"
        else:
            site_url = site_settings.site_url.rstrip("/")

        posts = self.posts_manager.order_by(
            list(self.posts_manager.posts.values()), "modified_desc"
        )
        if limit is not None:
            posts = posts[:limit]

        # Build channel info
        channel_title = escape(site_settings.title)
        channel_description = escape(site_settings.description)
        channel_link = escape(site_url)

        # Use current time as lastBuildDate
        last_build_date = self._format_rfc822_date(datetime.date.today())

        # Start building RSS XML
        rss_parts = []
        rss_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
        rss_parts.append(
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:content="http://purl.org/rss/1.0/modules/content/">'
        )
        rss_parts.append("  <channel>")
        rss_parts.append(f"    <title>{channel_title}</title>")
        rss_parts.append(f"    <description>{channel_description}</description>")
        rss_parts.append(f"    <link>{channel_link}</link>")
        rss_parts.append(f"    <lastBuildDate>{last_build_date}</lastBuildDate>")
        rss_parts.append(
            f"    <generator>AmiaBlog {get_amiablog_version()}</generator>"
        )

        # Add atom:self link
        rss_parts.append(
            f'    <atom:link href="{channel_link}/feed" rel="self" type="application/rss+xml" />'
        )
        rss_parts.append(
            f"    <language>{escape(self.config.site_language)}</language>"
        )
        if self.config.copyright:
            rss_parts.append(
                f"    <copyright>{escape(self.config.copyright.name)} {escape(self.config.copyright.refer)}</copyright>"
            )

        # Add items for each post
        for post in posts:
            post_url = f"{site_url}/post/{post.slug}"
            if is_static:
                post_url += ".html"
            title = escape(post.metadata.title)
            description = escape(post.metadata.description)
            pub_date = self._format_rfc822_date(post.metadata.date)
            author = escape(post.metadata.author)
            guid = escape(post_url)

            rss_parts.append("    <item>")
            rss_parts.append(f"      <title>{title}</title>")
            rss_parts.append(f"      <link>{post_url}</link>")
            rss_parts.append(f"      <description>{description}</description>")
            rss_parts.append(f"      <pubDate>{pub_date}</pubDate>")
            rss_parts.append(f"      <guid>{guid}</guid>")
            rss_parts.append(f"      <author>{author}</author>")
            rss_parts.append(
                f'      <content:encoded xml:lang="{escape(self.config.site_language)}"><![CDATA[{post.content}]]></content:encoded>'
            )
            # Add categories (tags)
            for tag in post.metadata.tags:
                escaped_tag = escape(tag)
                rss_parts.append(f"      <category>{escaped_tag}</category>")
            rss_parts.append("    </item>")

        rss_parts.append("  </channel>")
        rss_parts.append("</rss>")

        return "\n".join(rss_parts)
