<p align="center">
  <img src="https://github.com/0x24a/AmiaBlog/blob/main/docs/mizukichibi.png?raw=true" alt="Mizuki Chibi" height="200" width="100"/>
  <h1>AmiaBlog</h1>
  A simple, lightweight blog system built with FastAPI & MDUIv2.
  
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128+-009688.svg?logo=fastapi)
![UV](https://img.shields.io/badge/UV-package%20manager-FFD343.svg?logo=python)
  
</p>

AmiaBlog is a simple blog system that emphasizes simplicity, customization, and speed. It uses Markdown for content, In-memory SQLite for search, and provides i18n support out of the box.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Writing Posts](#writing-posts)
- [Deployment](#deployment)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## Features

### Content & Writing
- Markdown Support: Write posts in Markdown with YAML frontmatter metadata
- Syntax Highlighting: Built-in highlight.js with automatic language bundle downloads
- Markdown Extensions: Supports footnotes and other Markdown extensions

### Design & UX
- Custom Color Scheme: Choose any HEX color for your blog's theme, a complete color palette will be generated automatically
- Dark/Light Mode: Automatically switch, or manually fix to `dark` or `light`, it's your choice.
- Responsive Design: Works seamlessly on.. basically everything (but not IE6 please)
- Material Design You: Material Design You UI using MDUIv2

### Performance
- High-Performance Search: In-memory SQLite database for lightning-fast queries
- Fuzzy Search: jieba-fast tokenizer for better fuzzy search results
- Multiple Search Methods: Choose between `fullmatch` (exact, better performance) or `jieba` (tokenized, better accuracy) search

### Customization
- Single-File Configuration: All settings in one `config.json` file
- I18n: Built-in support for English and Simplified Chinese (easily extensible, send pr if you are willing to add more!)
- RSS Feed: Automatic RSS feed generation
- Cloudflare Analytics: Easy integration with Cloudflare Analytics
- Copyright Footer: Flexible copyright/license display options

### Tech Stack
- FastAPI: Modern Python web framework with automatic OpenAPI documentation
- Jinja2: Flexible & safe templating system with template caching
- UV: Blazing fast, reliable dependency management
- Pydantic: Easy data validation

## Quick Start

### Prerequisites
- Python 3.11 or higher (only tested on 3.11.4, might work on older versions, try it out yourself)
- [UV](https://github.com/astral-sh/uv) package manager

### Installation

1. Clone the repo
   ```bash
   git clone https://github.com/0x24a/AmiaBlog.git
   cd AmiaBlog
   ```

2. Install dependencies
   ```bash
   uv sync
   ```

3. Configure your blog
   Edit `config.json` with your settings (see [Configuration](/docs/configuration.md)). The file already contains default values you can modify.

4. **Write your first post**
   Create a Markdown file in the `posts/` directory. See [Writing Posts](/docs/writing-posts.md).

5. **Start the server**
   ```bash
   uv run uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   Your blog will be available at http://localhost:8000

## Deployment

### Production Deployment

For production, consider using Gunicorn with Uvicorn Workers:
```bash
uv run gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## Contributing

Contributions are welcome! Since this is a side project, I may not be able to review every PR immediately, but I appreciate all contributions.

### Development Setup

1. Fork and clone the repository
2. Install development dependencies:
   ```bash
   uv sync
   ```
3. Make your changes

### Guidelines

- Code Style: Use [Black](https://github.com/psf/black) for code formatting
- Commit Messages: Follow [Conventional Commits](https://www.conventionalcommits.org/)
- Internationalization: When translating, use keyword formatting placeholders if there are 2+ placeholders in an i18n term, since the word order may vary depends on the language.
- Documentation: Update relevant documentation

## License

Under the MIT License, see [LICENSE](LICENSE) for details.

## Credits

- [FastAPI](https://fastapi.tiangolo.com/)
- [MDUIv2](https://www.mdui.org/)
- [jieba-fast](https://github.com/deepcs233/jieba_fast)

---

Made with ❤️ by [0x24a](https://github.com/0x24a)