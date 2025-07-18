"""Tests for test_utils library."""

from test_utils import add_numbers, greet


def test_add_numbers():
    """Test the add_numbers function."""
    assert add_numbers(2, 3) == 5
    assert add_numbers(-1, 1) == 0
    assert add_numbers(0, 0) == 0


def test_greet():
    """Test the greet function."""
    assert greet("World") == "Hello, World!"
    assert greet("Alice") == "Hello, Alice!"


def test_greet_empty_string():
    """Test greet with empty string."""
    assert greet("") == "Hello, !"
