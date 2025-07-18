#!/usr/bin/env python3
"""
Local Dependency Setup Script for Hoopstat Haus

This script helps developers easily add shared libraries as local path dependencies
to their applications with proper configuration for hot reloading.
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List

try:
    import toml
except ImportError:
    print("Error: toml package is required. Install with: pip install toml")
    sys.exit(1)


def find_project_root() -> Path:
    """Find the project root directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / ".git").exists():
            # Check if this is the monorepo root
            if (current / "apps").exists() and (current / "libs").exists():
                return current
        current = current.parent
    raise RuntimeError("Could not find project root directory")


def get_available_libraries(libs_dir: Path) -> List[str]:
    """Get list of available shared libraries."""
    libraries = []
    for lib_path in libs_dir.iterdir():
        if lib_path.is_dir() and (lib_path / "pyproject.toml").exists():
            libraries.append(lib_path.name)
    return sorted(libraries)


def get_available_apps(apps_dir: Path) -> List[str]:
    """Get list of available applications."""
    apps = []
    for app_path in apps_dir.iterdir():
        if app_path.is_dir() and (app_path / "pyproject.toml").exists():
            apps.append(app_path.name)
    return sorted(apps)


def calculate_relative_path(from_path: Path, to_path: Path) -> str:
    """Calculate relative path from one directory to another."""
    return str(os.path.relpath(to_path, from_path))


def add_local_dependency(app_path: Path, lib_name: str, lib_path: Path, version_constraint: str = None) -> bool:
    """Add a local dependency to an application's pyproject.toml."""
    pyproject_path = app_path / "pyproject.toml"
    
    if not pyproject_path.exists():
        print(f"Error: {pyproject_path} does not exist")
        return False
    
    try:
        # Load the current pyproject.toml
        with open(pyproject_path, 'r') as f:
            pyproject = toml.load(f)
        
        # Ensure dependencies section exists
        if 'tool' not in pyproject:
            pyproject['tool'] = {}
        if 'poetry' not in pyproject['tool']:
            pyproject['tool']['poetry'] = {}
        if 'dependencies' not in pyproject['tool']['poetry']:
            pyproject['tool']['poetry']['dependencies'] = {}
        
        # Calculate relative path
        rel_path = calculate_relative_path(app_path, lib_path)
        
        # Create dependency specification
        dep_spec = {
            "path": rel_path,
            "develop": True
        }
        
        if version_constraint:
            dep_spec["version"] = version_constraint
        
        # Add the dependency
        pyproject['tool']['poetry']['dependencies'][lib_name] = dep_spec
        
        # Write back to file
        with open(pyproject_path, 'w') as f:
            toml.dump(pyproject, f)
        
        print(f"✓ Added {lib_name} as local dependency to {app_path.name}")
        print(f"  Path: {rel_path}")
        if version_constraint:
            print(f"  Version: {version_constraint}")
        print(f"  Hot reloading: enabled")
        
        return True
        
    except Exception as e:
        print(f"Error updating {pyproject_path}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add shared libraries as local path dependencies to applications",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a library to an application
  python scripts/setup-local-deps.py --app my-app --lib shared-utils
  
  # Add multiple libraries
  python scripts/setup-local-deps.py --app my-app --lib shared-utils --lib data-utils
  
  # Add with version constraint
  python scripts/setup-local-deps.py --app my-app --lib shared-utils --version "^1.0.0"
  
  # List available apps and libraries
  python scripts/setup-local-deps.py --list
        """
    )
    
    parser.add_argument(
        "--app",
        help="Application name (in apps/ directory)"
    )
    
    parser.add_argument(
        "--lib",
        action="append",
        help="Library name (in libs/ directory). Can be specified multiple times."
    )
    
    parser.add_argument(
        "--version",
        help="Version constraint (e.g., '^1.0.0', '>=1.0.0,<2.0.0')"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available applications and libraries"
    )
    
    args = parser.parse_args()
    
    try:
        # Find project root
        project_root = find_project_root()
        apps_dir = project_root / "apps"
        libs_dir = project_root / "libs"
        
        if not apps_dir.exists() or not libs_dir.exists():
            print("Error: Could not find apps/ and libs/ directories")
            sys.exit(1)
        
        # List mode
        if args.list:
            available_apps = get_available_apps(apps_dir)
            available_libs = get_available_libraries(libs_dir)
            
            print("Available Applications:")
            for app in available_apps:
                print(f"  - {app}")
            
            print("\nAvailable Libraries:")
            for lib in available_libs:
                print(f"  - {lib}")
            
            return
        
        # Validate arguments
        if not args.app or not args.lib:
            print("Error: Both --app and --lib are required (or use --list)")
            parser.print_help()
            sys.exit(1)
        
        # Check if app exists
        app_path = apps_dir / args.app
        if not app_path.exists():
            print(f"Error: Application '{args.app}' not found in apps/")
            available_apps = get_available_apps(apps_dir)
            print(f"Available apps: {', '.join(available_apps)}")
            sys.exit(1)
        
        # Process each library
        success_count = 0
        for lib_name in args.lib:
            lib_path = libs_dir / lib_name
            if not lib_path.exists():
                print(f"Error: Library '{lib_name}' not found in libs/")
                available_libs = get_available_libraries(libs_dir)
                print(f"Available libraries: {', '.join(available_libs)}")
                continue
            
            if add_local_dependency(app_path, lib_name, lib_path, args.version):
                success_count += 1
        
        if success_count > 0:
            print(f"\n✓ Successfully added {success_count} local dependencies")
            print("\nNext steps:")
            print(f"1. cd apps/{args.app}")
            print("2. poetry lock     # Update lock file")
            print("3. poetry install  # Install dependencies")
            print("4. Start developing with hot reloading!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()