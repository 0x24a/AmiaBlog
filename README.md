# AmiaBlog
A simple blog built with FastAPI & MDUIv2.

# Features
- Markdown support ( LaTeX wip )
- Custom color scheme
- Light/Dark mode auto switch
- Responsive design
- Strong customizability
- Single-file configuration
- High-performance search with in-memory sqlite database and jieba-fast tokenizer
- Cloudflare Analytics support
- ...And more in the future, try it out!

# Usage
1. Clone the repository
```
git clone https://github.com/0x24a/AmiaBlog.git && cd AmiaBlog
```
2. Install dependencies
```
uv sync
```
3. Change the configuration file
```json
// config.json
{
  "site_settings": {
    "title": "<The name of your site>",
    "description": "<Description of your site>",
    "keywords": "<Keywords separated by commas, used for SEO>",
    "color_scheme": "<HEX color code, like #DDAACC or #39C5BB>",
    "theme": "<auto OR light OR dark, auto as default>",
    "hljs_languages": [
      // Languages to be highlighted with hljs, will be automatically downloaded, e.g python, rust, javascript etc.
      "python",
      "rust",
      "javascript"
    ]
  },
  "site_language": "<Site default language. Currently only English(en) and Simpified Chinese(zh-CN) are supported>",
  "copyright": { // Optional
    "name": "<Name of the license. e.g CC-BY-SA 4.0>",
    "refer": "<URL of the license>"
  },
  "search_method": "<fullmatch OR jieba, fullmatch as default but jieba is recommended and provides better results>",
  "cloudflare_analytics_token": "<Cloudflare Analytics Token>",  // Optional
  "disable_template_cache": false // Do not enable this, unless you're debugging/modifying the frontend.
}
```
4. Write some articles. Refer to `posts/amiablog-test-hello.md` for example.
5. Start the server using any ASGI server, such as uvicorn or hypercorn. For example, uvicorn:
```
uv run uvicorn main:app
```

# Contributing
- This is my side project, feel free to contribute but I can't guarantee that I'll have time to review and accept every PR.
- Please use `black` as the code formatter.
- Please use conventional commit messages.
- Use keyword formatting placeholders when translating if 2 or more placeholders are in the i18n term. This is because different languages may have different word orders.

Under MIT License. See [LICENSE](LICENSE) for details.
Made with ❤️ by [0x24a](https://github.com/0x24a)