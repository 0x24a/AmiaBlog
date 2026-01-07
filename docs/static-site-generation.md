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

## Limitations
- Search functionality will be disabled.
- The option to select the sort order in the "All Posts" page will be disabled.