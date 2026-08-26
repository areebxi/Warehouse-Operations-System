"""
Settings management for Queue App application.

This module provides the SettingsManager class for handling application settings
persistence. Settings are stored in a JSON file and can be loaded and saved
between application sessions.

Settings include:
    - input_file: Path to input file (for single file processing)
    - input_folder_path: Path to input folder (for folder processing)
    - size_reference_file: Path to size reference Excel file
    - designs_folder: Path to designs folder (for standard processing)
    - single_designs_folder: Path to single designs folder (for personalised mode)
    - double_designs_folder: Path to double designs folder (for personalised mode)
    - dtf_queues_folder: Path to DTF queues folder (for RAR export)
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

from src.system.interfaces import ISettingsManager


def _get_project_root() -> str:
    """Resolve Queue app root from scripts/src/system module path."""
    return str(Path(__file__).resolve().parents[3])


def _warehouse_settings_path() -> Path:
    import sys

    app_root = Path(_get_project_root())
    warehouse = app_root.parent
    if str(warehouse) not in sys.path:
        sys.path.insert(0, str(warehouse))
    from shared import paths as wh

    return wh.queue_settings_path()


class SettingsManager(ISettingsManager):
    """Manages application settings persistence.
    
    Handles loading and saving of application settings to a JSON file.
    Settings are automatically loaded on initialization and can be saved
    using the save_settings method.
    
    Attributes:
        settings_file: Path to the settings JSON file
        saved_settings: Dictionary containing the current settings
    """
    
    def __init__(self, settings_file_path: Optional[str] = None) -> None:
        """Initialize settings manager.
        
        Args:
            settings_file_path: Path to settings file. If None, uses
                Config/queue/queue_app_settings.json.
        """
        if settings_file_path is None:
            settings_file_path = str(_warehouse_settings_path())
        
        self.settings_file: str = settings_file_path
        self._saved_settings: Dict[str, Optional[str]] = {}
        self.load_settings()
    
    @property
    def saved_settings(self) -> Dict[str, Optional[str]]:
        """Get current settings dictionary.
        
        Returns:
            Dictionary containing all current settings.
        """
        return self._saved_settings
    
    def load_settings(self) -> None:
        """Load saved settings from file.
        
        If the settings file exists, loads settings from it. Otherwise,
        initializes with default empty values for all settings.
        
        Note:
            If an error occurs while loading, prints an error message and
            continues with default settings.
        """
        self._saved_settings = {
            'input_file': None,
            'input_folder_path': None,
            'size_reference_file': None,
            'designs_folder': None,
            'single_designs_folder': None,
            'double_designs_folder': None,
            'dtf_queues_folder': None
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    self._saved_settings = json.load(f)
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def save_settings(
        self,
        input_file: Optional[str] = None,
        input_folder_path: Optional[str] = None,
        size_reference_file: Optional[str] = None,
        designs_folder: Optional[str] = None,
        single_designs_folder: Optional[str] = None,
        double_designs_folder: Optional[str] = None,
        dtf_queues_folder: Optional[str] = None
    ) -> None:
        """Save current settings to file.
        
        Args:
            input_file: Path to input file (if using file mode). If provided,
                input_folder_path will be cleared.
            input_folder_path: Path to input folder (if using folder mode). If
                provided, input_file will be cleared.
            size_reference_file: Path to size reference Excel file
            designs_folder: Path to designs folder (for standard processing)
            single_designs_folder: Path to single designs folder (for personalised mode)
            double_designs_folder: Path to double designs folder (for personalised mode)
            dtf_queues_folder: Path to DTF queues folder (for RAR export)
            
        Note:
            Only the active input method (file or folder) is saved. If both
            are provided, both are saved but typically only one should be used.
            If an error occurs while saving, prints an error message.
        """
        try:
            # Only save the active input method (file or folder), clear the other
            settings = {
                'input_file': input_file,
                'input_folder_path': input_folder_path,
                'size_reference_file': size_reference_file,
                'designs_folder': designs_folder,
                'single_designs_folder': single_designs_folder,
                'double_designs_folder': double_designs_folder,
                'dtf_queues_folder': dtf_queues_folder
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            # Update internal saved_settings
            self._saved_settings = settings
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.
        
        Args:
            key: Setting key (e.g., 'input_file', 'designs_folder')
            default: Default value to return if key is not found
            
        Returns:
            Setting value if key exists, otherwise the default value.
            
        Example:
            >>> manager = SettingsManager()
            >>> input_file = manager.get('input_file', 'default.xlsx')
        """
        return self._saved_settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value (in-memory only, does not save to file).
        
        Args:
            key: Setting key (e.g., 'input_file', 'designs_folder')
            value: Setting value to store
        
        Note:
            This method only updates the in-memory settings. To persist
            changes to disk, call save_settings() after setting values.
            
        Example:
            >>> manager = SettingsManager()
            >>> manager.set('input_file', 'path/to/file.xlsx')
            >>> manager.save_settings(input_file='path/to/file.xlsx')
        """
        self._saved_settings[key] = value
    
    def get_settings_file_path(self) -> str:
        """Get the path to the settings file.
        
        Returns:
            Path to the settings JSON file.
            
        Example:
            >>> manager = SettingsManager()
            >>> path = manager.get_settings_file_path()
        """
        return self.settings_file

