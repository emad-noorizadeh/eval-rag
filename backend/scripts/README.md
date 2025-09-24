# Development Scripts

This directory contains utility scripts for development and maintenance.

## Available Scripts

### `new_python_file.py`
Creates new Python files with Apache 2.0 license header automatically.

**Usage:**
```bash
# From the backend directory
python scripts/new_python_file.py my_module "My awesome module description"
```

**Features:**
- Automatically adds Apache 2.0 license header
- Includes module description template
- Prevents overwriting existing files
- Creates files in the current directory

**Example:**
```bash
python scripts/new_python_file.py data_processor "Data processing utilities"
# Creates: data_processor.py with proper license header
```

## VS Code Integration

For automatic license header insertion in VS Code:

1. Open a new Python file
2. Type `apache-header` and press Tab
3. Fill in the module description
4. Start coding!

## License Compliance

All new Python files should include the Apache 2.0 license header. Use the provided tools to ensure compliance:

- **Script**: `python scripts/new_python_file.py <filename>`
- **VS Code**: Type `apache-header` and press Tab
- **Template**: Copy from `templates/python_template.py`
