# Configuration

All AmiaBlog configuration is stored in a single `config.json` file. This makes it easy to customize your blog without modifying code.

## Configuration File Location

AmiaBlog looks for `config.json` in the root directory of the project.

## Complete Configuration Example

Here's a complete example with all available options:

```json
{
  "site_settings": {
    "title": "My Awesome Blog",
    "description": "A blog about technology and programming",
    "keywords": "blog, programming, technology, python",
    "site_url": "https://blog.example.com",
    "color_scheme": "#39C5BB",
    "theme": "auto",
    "hljs_languages": ["python", "javascript", "rust", "go", "bash"]
  },
  "site_language": "en",
  "copyright": {
    "name": "CC-BY-SA 4.0",
    "refer": "https://creativecommons.org/licenses/by-sa/4.0/"
  },
  "search_method": "jieba",
  "cloudflare_analytics_token": "00112233445566778899deadbeef114514",
  "disable_template_cache": false
}
```

## Configuration Options

### Site Settings (`site_settings`)

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `title` | string | Required | Your blog's title, displayed in the header and browser tab |
| `description` | string | Required | Brief description of your blog, used for SEO and social media previews |
| `keywords` | string | Required | Comma-separated keywords for SEO optimization |
| `site_url` | string/null | `null` | Full URL of your site (including protocol). Required for RSS feed generation. If not set, `https://example.com/` will be used as a fallback. |
| `color_scheme` | string | `"DDAACC"` | HEX color code for your blog's theme. This color is used to generate dynamic color scheme. |
| `theme` | string | `"auto"` | Theme mode: `"auto"` (respects user's system preference), `"light"`, or `"dark"`. |
| `hljs_languages` | array | `[]` | List of programming languages for syntax highlighting. Highlight.js bundles for these languages will be automatically downloaded. |

### Language

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `site_language` | string | `"en"` | Default language for the blog interface. Currently supported: `"en"` (English) and `"zh-CN"` (Simplified Chinese). You can add more languages by creating additional files in the `languages/` directory. |

### Copyright

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `copyright` | object/null | `null` | Optional copyright/license information. If provided, it will be displayed in the footer. |
| `copyright.name` | string | Required if `copyright` set | Name of the license (e.g., `"CC-BY-SA 4.0"`, `"MIT License"`). |
| `copyright.refer` | string | Required if `copyright` set | URL to the license details. |

### Search Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `search_method` | string | `"fullmatch"` | Search algorithm: `"fullmatch"` for exact string matching, or `"jieba"` for tokenized search (recommended, especially for Chinese content). Using jieba could make queries slower but more accurate, and the time usage will still be within milliseconds, totally worth it. |

### Analytics & Monitoring

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `cloudflare_analytics_token` | string/null | `null` | Cloudflare Analytics token. If provided, Cloudflare Analytics will be included in your pages. |

### Development & Debugging

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `disable_template_cache` | boolean | `false` | Disable Jinja2 template caching. **Only enable this during development or when modifying templates.** In production, keep this `false` for optimal performance. |

## Validation

AmiaBlog uses Pydantic to validate your configuration file. If there are any errors (missing required fields, invalid values, etc.), the application will fail to start.

---

[← Back to README](../README.md)