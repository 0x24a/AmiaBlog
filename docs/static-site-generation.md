# Static Site Generation

To generate your AmiaBlog instance into a static site, you can use the `staticify` command:
Example: 
```bash
uv run staticify.py --destination dist/ --remove-existing
```
This will generate a static site in the `dist/` directory, and clear the directory first if there is one already.

## Command Params
|Param|Type|Default|Description|
|-----|----|-------|-----------|
|`--destination`|`str`|`dist/`|The directory to generate the static site into.|
|`--remove-existing`|`bool`|`False`|Whether to remove the destination directory if it already exists.|

## Build info
An `amiablog_build_info.txt` file will be generated in the destination directory containing information about the build.
Example:
```
software: AmiaBlog
version: 1.1.0
python_version: 3.11.4 (v3.11.4:d2340ef257, Jun  6 2023, 19:15:51) [Clang 13.0.0 (clang-1300.0.29.30)]
platform: macos-aarch64-none
build_time: 2026-01-12 12:22:33
build_time_usage: 48.19ms
```

## Limitations
- Search functionality will be disabled. (Will be implemented in the future)
- The option to select the sort order in the "All Posts" page will be disabled.

[← Back to README](../README.md)