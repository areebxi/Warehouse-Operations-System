# Source Code Package (`src/`)

This directory contains all the core modules for the Queue App application.

## Modules

### Core Processing
- **`design_processor.py`** - Design processing logic (single and personalised modes)
- **`canvas_arranger.py`** - Canvas packing and arrangement algorithms
- **`image_utils.py`** - Image operations (resizing, canvas creation, size calculations)

### File Operations
- **`file_handlers.py`** - File operations (finding designs, loading databases, extracting codes)
- **`rar_utils.py`** - RAR archive creation and management

### Utilities
- **`settings_manager.py`** - Application settings management
- **`logging_utils.py`** - Error logging and size determination logging
- **`gui_components.py`** - GUI component functions (preview drawing)
- **`exceptions.py`** - Custom exception classes

## Usage

All modules are imported from the `src` package:

```python
from src.file_handlers import find_design_file
from src.design_processor import process_single_design
from src.image_utils import resize_image_with_constraints
# etc.
```

The main entry point (`queue_app.py`) is located in the project root directory.

