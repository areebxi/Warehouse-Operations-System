from __future__ import annotations
import os
from typing import Optional, Callable, Tuple, List, Any
from tkinter import filedialog, messagebox
from gui_helpers.common import gui_theme

def validate_and_update_numeric_var(
    gui,
    var_attr: str,
    min_val: float,
    max_val: float,
    gui_value_attr: str,
    update_func: Callable,
    error_message: str,
    invalid_number_message: str = "Please enter valid numbers"
) -> bool:
    """Validate and update a numeric variable.

    Args:
        gui: GUI object
        var_attr: Variable attribute name (e.g., 'canvas_width_var')
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        gui_value_attr: GUI attribute name storing the current value
        update_func: Function(new_value) to update the value if valid
        error_message: Error message for out-of-range values
        invalid_number_message: Error message for invalid number format

    Returns:
        True if validation passed (including unchanged value), False otherwise
    """
    try:
        var = getattr(gui, var_attr)
        new_value = float(var.get())
        current_value = getattr(gui, gui_value_attr)

        if min_val <= new_value <= max_val:
            # Skip update when value is unchanged (avoids no-op side effects)
            if float(new_value) == float(current_value):
                return True
            update_func(new_value)
            return True
        else:
            # Reset to current value
            current_value = getattr(gui, gui_value_attr)
            var.set(str(current_value))
            messagebox.showwarning("Invalid", error_message)
            return False
    except ValueError:
        # Reset to current value
        current_value = getattr(gui, gui_value_attr)
        var.set(str(current_value))
        messagebox.showwarning("Invalid", invalid_number_message)
        return False
def load_path_setting(
    gui,
    setting_key: str,
    gui_attr: str,
    label_attr: Optional[str] = None,
    loader_func: Optional[Callable] = None,
    default_value: Optional = None
) -> bool:
    """Load a path setting from saved_settings and update GUI.

    Args:
        gui: GUI object
        setting_key: Key in saved_settings
        gui_attr: GUI attribute name to set
        label_attr: Optional label attribute name to update
        loader_func: Optional function(path) to load/process the path
        default_value: Optional default value if path doesn't exist

    Returns:
        True if setting was loaded successfully, False otherwise
    """
    setting_value = gui.saved_settings.get(setting_key)

    if not setting_value:
        return False

    if not os.path.exists(setting_value):
        return False

    try:
        # Load/process the path if loader function provided
        if loader_func:
            loader_func(setting_value)
        else:
            setattr(gui, gui_attr, setting_value)

        # Update label if provided
        if label_attr:
            update_label_with_path(gui, label_attr, setting_value)

        return True
    except Exception as e:
        print(f"Error loading {setting_key}: {e}")
        return False
