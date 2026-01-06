# Writing Posts

AmiaBlog uses Markdown files with YAML frontmatter for blog posts.

## Post Location

All blog posts are stored in the `posts/` directory, and each post is a separate `.md` (Markdown) file.

## File Naming

Use descriptive filenames for better readability that include the post slug. For example:

- `my-first-post.md`
- `introducing-amiablog.md`

The filename becomes the URL slug for your post. For example, the URL of `posts/my-first-post.md` will be `/posts/my-first-post`.

## Post Structure

Each post file has two parts:
1. YAML Frontmatter: Metadata about the post (title, date, tags, etc.)
2. Markdown Content: The actual post content

A complete example:

```markdown
title: My First AmiaBlog Post
date: 2026-01-06
last_modified: 2026-01-06
tags: [Python, FastAPI, Blogging]
keywords: [additional, keywords, for, seo, optimization]
description: A brief description of this post.
published: true
author: Your Name
---
# Welcome to My Blog

...
```

## Frontmatter Fields Reference

| Key | Type | Default | Description |
|-------|----------|---------|-------------|
| `title` | string | Required | Post title |
| `date` | string | Required | Publication date in `YYYY-MM-DD` format. |
| `last_modified` | string | Required | Last modification date in `YYYY-MM-DD` format. |
| `tags` | array | Required | Array of tags. Example: `[Python, FastAPI, Blogging]` |
| `keywords` | array | `[]` | Array of keywords. Used for SEO optimization. Example: `[additional, keywords, for, seo, optimization]` |
| `description` | string | Required | Brief description used for SEO meta tags and social media previews. |
| `published` | boolean | Required | Boolean flag. Set to `false` to hide the post if you're still working on it. Unpublished posts won't be loaded. |
| `author` | string | Required | Author name. Displayed in the post metadata. |

---

[← Back to README](../README.md)