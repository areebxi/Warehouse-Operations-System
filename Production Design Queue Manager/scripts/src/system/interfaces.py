"""Abstract interfaces used across Queue App services."""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class ISettingsManager(ABC):
    """Contract for loading, saving, and querying settings."""

    @abstractmethod
    def load_settings(self) -> None:
        """Load settings from persistent storage."""
        pass  # pragma: no cover

    @abstractmethod
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
        """Save settings to persistent storage."""
        pass  # pragma: no cover

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        pass  # pragma: no cover

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set a setting value in memory."""
        pass  # pragma: no cover

    @property
    @abstractmethod
    def saved_settings(self) -> Dict[str, Optional[str]]:
        """Get current settings dictionary."""
        pass  # pragma: no cover
