"""
Tests to validate the shared library versioning strategy implementation.

These tests verify that the versioning documentation and templates
are properly configured and accessible.
"""

import os
import re
from pathlib import Path


def test_adr_exists():
    """Test that the versioning ADR exists and has required content."""
    adr_path = Path("meta/adr/ADR-016-shared_library_versioning.md")
    assert adr_path.exists(), "ADR-016 for shared library versioning should exist"
    
    content = adr_path.read_text()
    assert "Semantic Versioning" in content, "ADR should mention Semantic Versioning"
    assert "MAJOR.MINOR.PATCH" in content, "ADR should define version format"
    assert "status: \"Proposed\"" in content, "ADR should have Proposed status"


def test_versioning_guide_exists():
    """Test that the comprehensive versioning guide exists."""
    guide_path = Path("docs/SHARED_LIBRARY_VERSIONING.md")
    assert guide_path.exists(), "Shared library versioning guide should exist"
    
    content = guide_path.read_text()
    
    # Check for key sections
    assert "## Overview" in content, "Guide should have overview section"
    assert "## Semantic Versioning Format" in content, "Guide should explain SemVer format"
    assert "## Version Management Process" in content, "Guide should describe process"
    assert "## Dependency Management" in content, "Guide should cover dependencies"
    assert "poetry version" in content, "Guide should reference Poetry commands"


def test_library_template_includes_versioning():
    """Test that the library template includes versioning information."""
    template_readme = Path("templates/python-lib-template/README.md")
    assert template_readme.exists(), "Library template README should exist"
    
    content = template_readme.read_text()
    assert "## Versioning" in content, "Template should include versioning section"
    assert "Semantic Versioning" in content, "Template should mention SemVer"
    assert "poetry version" in content, "Template should show version commands"


def test_libs_readme_references_versioning():
    """Test that the libs README references the versioning strategy."""
    libs_readme = Path("libs/README.md")
    assert libs_readme.exists(), "Libs README should exist"
    
    content = libs_readme.read_text()
    assert "Versioning" in content, "Libs README should mention versioning"
    assert "SHARED_LIBRARY_VERSIONING.md" in content, "Should reference versioning guide"


def test_library_template_pyproject_has_version():
    """Test that the library template pyproject.toml has version field."""
    pyproject_path = Path("templates/python-lib-template/pyproject.toml")
    assert pyproject_path.exists(), "Library template pyproject.toml should exist"
    
    content = pyproject_path.read_text()
    
    # Check for version field
    version_pattern = r'version\s*=\s*"[\d\.]+"'
    assert re.search(version_pattern, content), "Template should have version field"
    
    # Check that it starts with 0.1.0 as per documentation
    assert 'version = "0.1.0"' in content, "Template should start at version 0.1.0"


def test_documentation_cross_references():
    """Test that documentation files properly cross-reference each other."""
    # Check ADR references
    adr_content = Path("meta/adr/ADR-016-shared_library_versioning.md").read_text()
    
    # Check guide references ADR
    guide_content = Path("docs/SHARED_LIBRARY_VERSIONING.md").read_text()
    assert "ADR-016" in guide_content, "Guide should reference ADR-016"
    
    # Check libs README references guide
    libs_content = Path("libs/README.md").read_text()
    assert "../docs/SHARED_LIBRARY_VERSIONING.md" in libs_content, "Libs README should reference guide with correct path"
    
    # Check template references guide
    template_content = Path("templates/python-lib-template/README.md").read_text()
    assert "../../docs/SHARED_LIBRARY_VERSIONING.md" in template_content, "Template should reference guide with correct path"


if __name__ == "__main__":
    # Change to repository root for relative path tests
    os.chdir(Path(__file__).parent.parent)
    
    # Run all tests
    test_functions = [
        test_adr_exists,
        test_versioning_guide_exists,
        test_library_template_includes_versioning,
        test_libs_readme_references_versioning,
        test_library_template_pyproject_has_version,
        test_documentation_cross_references,
    ]
    
    for test_func in test_functions:
        try:
            test_func()
            print(f"✓ {test_func.__name__}")
        except AssertionError as e:
            print(f"✗ {test_func.__name__}: {e}")
        except Exception as e:
            print(f"✗ {test_func.__name__}: Unexpected error: {e}")
    
    print("\nVersioning strategy validation complete.")