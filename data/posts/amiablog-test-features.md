---
title: "Feature Test — Syntax, Declarations & Copyright"
date: 2024-01-01
last_modified: 2024-01-01
tags:
  - test
  - markdown
  - feature
description: "Testing AmiaBlog features: advanced Markdown rendering, declarations, and copyright"
published: true
author: "Tester"
declarations:
  - "本文由AI辅助生成"
  - "本文含推广链接"
copyright:
  name: "All Rights Reserved"
  refer: ""
keywords:
  - test
  - markdown
  - highlight.js
---

## Code Block Highlighting

### Python

```python
def fibonacci(n: int) -> list[int]:
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    return fib[:n]

result = fibonacci(10)
print(f"First 10 Fibonacci numbers: {result}")
```

### JavaScript

```javascript
async function fetchUserData(userId) {
    const response = await fetch(`https://api.example.com/users/${userId}`);
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
}

fetchUserData(42).then(console.log);
```

### Rust

```rust
use std::collections::HashMap;

#[derive(Debug)]
struct Config {
    host: String,
    port: u16,
    workers: u32,
}

fn main() {
    let cfg = Config {
        host: "127.0.0.1".to_string(),
        port: 8080,
        workers: 4,
    };
    println!("{:?}", cfg);
}
```

### Plain Text (no language tag)

```
This is a plain text block
No language specified
Should render without syntax coloring
```

## Table

| Feature             | Support | Notes                      |
| :------------------ | :-----: | :------------------------- |
| Syntax Highlighting |    ✅    | Python / JS / Rust         |
| Footnotes           |    ✅    | via markdown-it-footnote   |
| Tables              |    ✅    | Column alignment supported |

## Footnotes

This is a sentence with a footnote[^1], and this is another one[^2].

[^1]: The first footnote content, explaining some concept.
[^2]: A second footnote with **bold** and `inline code` formatting.

## Blockquotes

> This is a blockquote.
>
> > Nested blockquote.

---

## Image Rendering

![Test Image](/attachments/mizukichibi.png)

*Caption: Test image from the attachments directory*

## Inline Formatting

**Bold**, *Italic*, ~~Strikethrough~~, `inline code`, and combined: **bold with *italic* inside**.

## HTML Security Test

Expected: no alert popup.

```html
<script>alert('XSS')</script>
<img src="x" onerror="alert('XSS')">
```
