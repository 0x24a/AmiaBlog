import platform
from typing import Optional
import os


def get_amiablog_version():
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        content = f.read()
        for line in content.split("\n"):
            if line.startswith("version"):
                return line.split("=")[1].strip().strip('"')


def get_platform_string():
    os_name = platform.system().lower()
    os_map = {"darwin": "macos", "linux": "linux", "windows": "windows"}
    final_os = os_map.get(os_name, os_name)

    arch = platform.machine().lower()
    arch_map = {
        "arm64": "aarch64",
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "aarch64": "aarch64",
    }
    final_arch = arch_map.get(arch, arch)

    return f"{final_os}-{final_arch}-none"


def get_commit_hash(length: int = 7) -> Optional[str]:
    try:
        commit_hash = os.popen("git rev-parse HEAD").read().strip()
        if not commit_hash:
            return None
        assert all([char in "0123456789abcdef" for char in commit_hash])
        return commit_hash[:length] if length != 0 else commit_hash
    except Exception:
        return None
