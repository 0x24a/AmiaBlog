import os.path
import sys
from loguru import logger


def check_attachment_migration() -> None:
    if not os.path.isdir("data/attachments") and os.path.isdir("attachments"):
        logger.error(
            "...\nError: the default attachments directory has been changed to data/attachments (in commit 647887d).\nPlease do a migration."
        )
        sys.exit(1)
