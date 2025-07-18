"""
Utilities module for the example library.

This module demonstrates standard patterns for shared library modules.
"""


def example_function(text: str) -> str:
    """
    Convert text to uppercase.
    
    This is an example function demonstrating proper documentation
    and type hints for shared library functions.
    
    Args:
        text: The input text to convert to uppercase
        
    Returns:
        The uppercase version of the input text
        
    Example:
        >>> example_function("hello")
        'HELLO'
    """
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    
    return text.upper()