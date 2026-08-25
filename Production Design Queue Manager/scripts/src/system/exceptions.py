"""
Custom exception classes for Queue App application.

This module defines custom exceptions for better error handling and
more descriptive error messages throughout the application.
"""


class DesignArrangerError(Exception):
    """Base exception class for all Queue App errors.
    
    All custom exceptions in this module should inherit from this class
    to allow catching all Queue App errors with a single except clause.
    """
    pass


class DesignNotFoundError(DesignArrangerError):
    """Raised when a design file cannot be found.
    
    This exception should be raised when:
    - A design file is expected but cannot be located
    - Design file search fails after all strategies are exhausted
    
    Attributes:
        sku: SKU string that was being searched for
        design_code: Design code that was extracted from SKU (if applicable)
        search_paths: List of paths that were searched (optional)
        message: Error message
    """
    def __init__(self, message: str, sku: str = None, design_code: str = None, 
                 search_paths: list = None):
        super().__init__(message)
        self.sku = sku
        self.design_code = design_code
        self.search_paths = search_paths or []


class SizeReferenceError(DesignArrangerError):
    """Raised when size reference is missing or invalid.
    
    This exception should be raised when:
    - Size reference file is missing required columns
    - Size code cannot be found in size reference
    - Size reference data is invalid or corrupted
    
    Attributes:
        size_code: Size code that was being looked up (if applicable)
        message: Error message
    """
    def __init__(self, message: str, size_code: str = None):
        super().__init__(message)
        self.size_code = size_code


class FileProcessingError(DesignArrangerError):
    """Raised when file processing fails.
    
    This exception should be raised when:
    - File cannot be read
    - File format is invalid
    - File operations fail (read, write, etc.)
    
    Attributes:
        file_path: Path to the file that caused the error
        operation: Operation that was being performed (e.g., 'read', 'write')
        message: Error message
    """
    def __init__(self, message: str, file_path: str = None, operation: str = None):
        super().__init__(message)
        self.file_path = file_path
        self.operation = operation


class ConfigurationError(DesignArrangerError):
    """Raised when configuration is missing or invalid.
    
    This exception should be raised when:
    - Required configuration is missing
    - Configuration values are invalid
    - Settings cannot be loaded
    
    Attributes:
        setting_name: Name of the setting that caused the error (if applicable)
        message: Error message
    """
    def __init__(self, message: str, setting_name: str = None):
        super().__init__(message)
        self.setting_name = setting_name


class ImageProcessingError(DesignArrangerError):
    """Raised when image processing fails.
    
    This exception should be raised when:
    - Image cannot be loaded
    - Image format is not supported
    - Image operations fail (resize, save, etc.)
    
    Attributes:
        image_path: Path to the image file (if applicable)
        operation: Operation that was being performed (e.g., 'resize', 'save')
        message: Error message
    """
    def __init__(self, message: str, image_path: str = None, operation: str = None):
        super().__init__(message)
        self.image_path = image_path
        self.operation = operation


class CanvasArrangementError(DesignArrangerError):
    """Raised when canvas arrangement/packing fails.
    
    This exception should be raised when:
    - Designs cannot be packed on canvas
    - Canvas dimensions are invalid
    - Arrangement algorithm fails
    
    Attributes:
        message: Error message
    """
    def __init__(self, message: str):
        super().__init__(message)


class SizeCodeExtractionError(DesignArrangerError):
    """Raised when size code extraction fails.
    
    This exception should be raised when:
    - Size code cannot be extracted from SKU
    - Required patterns are missing from SKU (e.g., for pocket designs)
    
    Attributes:
        sku: SKU string that was being processed
        message: Error message
    """
    def __init__(self, message: str, sku: str = None):
        super().__init__(message)
        self.sku = sku

