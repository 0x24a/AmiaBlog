import os
from typing import List

import httpx
from loguru import logger


class HLJSLanguageManager:
    def __init__(self, languages: List[str]):
        self.languages = languages
        self.available_languages = []
        self.download()

    def download(
        self,
        prefix: str = "static/hljs_11.1.1",
        url_prefix: str = "https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.11.1/build/languages/",
    ):
        undownloaded_languages = []
        files = os.listdir(prefix)
        for language in self.languages:
            if f"{language}.min.js" not in files:
                undownloaded_languages.append(language)
            else:
                self.available_languages.append(language)
        if not undownloaded_languages:
            return
        logger.info(f"Downloading {len(undownloaded_languages)} HLJS languages...")
        for language in undownloaded_languages:
            try:
                response = httpx.get(f"{url_prefix}{language}.min.js")
                response.raise_for_status()
                with open(os.path.join(prefix, f"{language}.min.js"), "wb") as f:
                    f.write(response.content)
            except Exception as e:
                logger.warning(f"Failed to download {language}.min.js: {e}, skipping.")
            else:
                logger.info(f"Successfully downloaded {language}.min.js")
                self.available_languages.append(language)
        logger.info("Download complete!")

    def get_markdown_languages(self, markdown_text: str):
        languages = []
        lines = markdown_text.splitlines()

        for line in lines:
            clean_line = line.lstrip()
            if clean_line.startswith("```"):
                language_tag = clean_line[3:].strip()
                if language_tag:
                    lang = language_tag.split()[0]
                    languages.append(lang)

        return languages
