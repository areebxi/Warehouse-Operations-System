"""
Common GUI utility functions for reducing code duplication.

This module contains shared helper functions used across multiple
GUI helper modules to reduce duplication and improve maintainability.
"""
import os
from typing import Optional, Callable, Tuple, List, Any
from tkinter import filedialog, messagebox
from gui_helpers.common import gui_theme


def get_initial_directory(
    gui,
    setting_key: str,
    fallback_attr: Optional[str] = None,
    use_dirname: bool = False
) -> Optional[str]:
    """Get initial directory for file/folder dialogs.

    Args:
        gui: GUI object with saved_settings attribute
        setting_key: Key in saved_settings to check
        fallback_attr: Optional GUI attribute name to use as fallback
        use_dirname: If True, use os.path.dirname of the setting value

    Returns:
        Initial directory path or None
    """
    initialdir = None

    # Check saved_settings first
    if gui.saved_settings.get(setting_key):
        value = gui.saved_settings[setting_key]
        if use_dirname and value:
            initialdir = os.path.dirname(value)
        else:
            initialdir = value if os.path.isdir(value) else os.path.dirname(value) if value else None

    # Fallback to GUI attribute if provided and initialdir not set
    if not initialdir and fallback_attr:
        fallback_value = getattr(gui, fallback_attr, None)
        if fallback_value:
            initialdir = fallback_value if os.path.isdir(fallback_value) else os.path.dirname(fallback_value)

    return initialdir


def update_label_with_path(
    gui,
    label_attr: Optional[str],
    path: str,
    foreground: Optional[str] = None,
    prefix: str = ""
) -> None:
    """Update a GUI label with a file/folder path.

    Args:
        gui: GUI object
        label_attr: Attribute name of the label widget (e.g., 'file_label'), or None to skip
        path: File or folder path to display
        foreground: Text color (default: theme FG)
        prefix: Optional prefix text (e.g., "Folder: ")
    """
    if label_attr is None:
        return
    label = getattr(gui, label_attr, None)
    if label:
        basename = os.path.basename(path)
        text = f"{prefix}{basename}" if prefix else basename
        label.config(text=text, foreground=foreground or gui_theme.FG)


def select_folder_common(
    gui,
    setting_key: str,
    gui_attr: str,
    label_attr: str,
    title: str,
    fallback_setting_key: Optional[str] = None,
    clear_attrs: Optional[List[Tuple[str, Any]]] = None
) -> Optional[str]:
    """Common function for folder selection dialogs.

    Args:
        gui: GUI object
        setting_key: Key in saved_settings to get initial directory
        gui_attr: GUI attribute name to store selected folder
        label_attr: Label attribute name to update
        title: Dialog title
        fallback_setting_key: Optional fallback setting key for initial directory
        clear_attrs: Optional list of (attr_name, clear_value) tuples to clear

    Returns:
        Selected folder path or None if cancelled
    """
    # Get initial directory
    initialdir = get_initial_directory(gui, setting_key)
    if not initialdir and fallback_setting_key:
        initialdir = get_initial_directory(gui, fallback_setting_key)

    # Show folder dialog
    folder_path = filedialog.askdirectory(title=title, initialdir=initialdir)

    if folder_path:
        # Clear other attributes if specified
        if clear_attrs:
            for attr_name, clear_value in clear_attrs:
                setattr(gui, attr_name, clear_value)

        # Set the selected folder
        setattr(gui, gui_attr, folder_path)

        # Update label
        update_label_with_path(gui, label_attr, folder_path)

        # Save settings
        gui.save_settings()

        return folder_path

    return None


def select_file_common(
    gui,
    setting_key: str,
    gui_attr: str,
    label_attr: Optional[str],
    title: str,
    filetypes: List[Tuple[str, str]],
    on_selected: Optional[Callable] = None,
    clear_attrs: Optional[List[Tuple[str, Any]]] = None
) -> Optional[str]:
    """Common function for file selection dialogs.

    Args:
        gui: GUI object
        setting_key: Key in saved_settings to get initial directory
        gui_attr: GUI attribute name to store selected file
        label_attr: Label attribute name to update, or None to skip label update
        title: Dialog title
        filetypes: List of (description, pattern) tuples for file types
        on_selected: Optional callback function(file_path) called after selection
        clear_attrs: Optional list of (attr_name, clear_value) tuples to clear

    Returns:
        Selected file path or None if cancelled
    """
    # Get initial directory
    initialdir = get_initial_directory(gui, setting_key, use_dirname=True)

    # Show file dialog
    file_path = filedialog.askopenfilename(
        title=title,
        filetypes=filetypes,
        initialdir=initialdir
    )

    if file_path:
        # Clear other attributes if specified
        if clear_attrs:
            for attr_name, clear_value in clear_attrs:
                setattr(gui, attr_name, clear_value)

        # Set the selected file
        setattr(gui, gui_attr, file_path)

        # Update label
        update_label_with_path(gui, label_attr, file_path)

        # Save settings
        gui.save_settings()

        # Call custom handler if provided
        if on_selected:
            try:
                on_selected(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to process file:\n{str(e)}")
                # Revert file path if handler failed
                setattr(gui, gui_attr, None)
                return None

        return file_path

    return None


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

