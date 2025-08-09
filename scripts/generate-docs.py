#!/usr/bin/env python3
"""
Documentation generation script for Hoopstat Haus shared libraries.

This script automatically generates API documentation from docstrings
in shared libraries, creating markdown files for MkDocs.
"""

import ast
import inspect
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import textwrap


class DocstringExtractor:
    """Extract and format docstrings from Python modules."""
    
    def __init__(self, lib_path: Path):
        self.lib_path = lib_path
        self.lib_name = lib_path.name
        self.module_path = lib_path / self.lib_name.replace('-', '_')
    
    def extract_module_info(self) -> Dict[str, Any]:
        """Extract module information including docstrings and API."""
        if not self.module_path.exists():
            return self._get_basic_info()
        
        # Load module's __init__.py to get public API
        init_file = self.module_path / "__init__.py"
        if not init_file.exists():
            return self._get_basic_info()
        
        try:
            # Parse the __init__.py file
            with open(init_file, 'r') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            # Extract module docstring
            module_docstring = ast.get_docstring(tree) or ""
            
            # Extract version
            version = self._extract_version(tree)
            
            # Extract __all__ exports
            exports = self._extract_exports(tree)
            
            # Get functions and classes from the module files
            functions, classes = self._extract_api_elements()
            
            return {
                'name': self.lib_name,
                'version': version,
                'docstring': module_docstring,
                'exports': exports,
                'functions': functions,
                'classes': classes
            }
        
        except Exception as e:
            print(f"Warning: Could not parse {init_file}: {e}")
            return self._get_basic_info()
    
    def _get_basic_info(self) -> Dict[str, Any]:
        """Get basic info when module parsing fails."""
        # Try to read README for description
        readme_path = self.lib_path / "README.md"
        description = ""
        if readme_path.exists():
            with open(readme_path, 'r') as f:
                lines = f.readlines()
                # Extract first paragraph after title
                for i, line in enumerate(lines):
                    if line.strip() and not line.startswith('#'):
                        description = line.strip()
                        break
        
        return {
            'name': self.lib_name,
            'version': '0.1.0',
            'docstring': description,
            'exports': [],
            'functions': [],
            'classes': []
        }
    
    def _extract_version(self, tree: ast.AST) -> str:
        """Extract version from __version__ assignment."""
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and 
                len(node.targets) == 1 and
                isinstance(node.targets[0], ast.Name) and
                node.targets[0].id == '__version__'):
                if isinstance(node.value, ast.Constant):
                    return str(node.value.value)
        return "0.1.0"
    
    def _extract_exports(self, tree: ast.AST) -> List[str]:
        """Extract __all__ exports."""
        for node in ast.walk(tree):
            if (isinstance(node, ast.Assign) and 
                len(node.targets) == 1 and
                isinstance(node.targets[0], ast.Name) and
                node.targets[0].id == '__all__'):
                if isinstance(node.value, ast.List):
                    exports = []
                    for elt in node.value.elts:
                        if isinstance(elt, ast.Constant):
                            exports.append(str(elt.value))
                    return exports
        return []
    
    def _extract_api_elements(self) -> tuple:
        """Extract functions and classes from module files."""
        functions = []
        classes = []
        
        # Look for Python files in the module directory
        for py_file in self.module_path.glob("*.py"):
            if py_file.name.startswith('__'):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                        func_info = self._extract_function_info(node, py_file.stem)
                        if func_info:
                            functions.append(func_info)
                    elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                        class_info = self._extract_class_info(node, py_file.stem)
                        if class_info:
                            classes.append(class_info)
            
            except Exception as e:
                print(f"Warning: Could not parse {py_file}: {e}")
        
        return functions, classes
    
    def _extract_function_info(self, node: ast.FunctionDef, module: str) -> Optional[Dict[str, Any]]:
        """Extract function information including docstring and signature."""
        docstring = ast.get_docstring(node) or ""
        
        # Extract function signature
        args = []
        for arg in node.args.args:
            arg_name = arg.arg
            # Try to get type annotation
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    arg_type = arg.annotation.id
                elif isinstance(arg.annotation, ast.Constant):
                    arg_type = str(arg.annotation.value)
                else:
                    arg_type = "Any"
                args.append(f"{arg_name}: {arg_type}")
            else:
                args.append(arg_name)
        
        # Get return type annotation
        return_type = "Any"
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return_type = node.returns.id
            elif isinstance(node.returns, ast.Constant):
                return_type = str(node.returns.value)
        
        signature = f"{node.name}({', '.join(args)}) -> {return_type}"
        
        return {
            'name': node.name,
            'module': module,
            'signature': signature,
            'docstring': docstring
        }
    
    def _extract_class_info(self, node: ast.ClassDef, module: str) -> Optional[Dict[str, Any]]:
        """Extract class information including docstring and methods."""
        docstring = ast.get_docstring(node) or ""
        
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                method_info = self._extract_function_info(item, module)
                if method_info:
                    methods.append(method_info)
        
        return {
            'name': node.name,
            'module': module,
            'docstring': docstring,
            'methods': methods
        }


def generate_library_documentation(lib_path: Path, output_path: Path) -> None:
    """Generate markdown documentation for a single library."""
    extractor = DocstringExtractor(lib_path)
    info = extractor.extract_module_info()
    
    # Generate markdown content
    content = []
    
    # Title and basic info
    content.append(f"# {info['name']}")
    content.append("")
    content.append(f"**Version:** {info['version']}")
    content.append("")
    
    # Description from docstring
    if info['docstring']:
        content.append("## Description")
        content.append("")
        content.append(info['docstring'])
        content.append("")
    
    # Installation section
    content.append("## Installation")
    content.append("")
    content.append(f"Add to your application's `pyproject.toml`:")
    content.append("")
    content.append("```toml")
    content.append("[tool.poetry.dependencies]")
    content.append(f'{info["name"]} = {{path = "../libs/{info["name"]}", develop = true}}')
    content.append("```")
    content.append("")
    
    # Usage section
    if info['exports']:
        content.append("## Usage")
        content.append("")
        content.append("```python")
        module_name = info['name'].replace('-', '_')
        exports_str = ', '.join(info['exports'])
        content.append(f"from {module_name} import {exports_str}")
        content.append("```")
        content.append("")
    
    # API Reference
    if info['classes'] or info['functions']:
        content.append("## API Reference")
        content.append("")
        
        # Classes
        if info['classes']:
            content.append("### Classes")
            content.append("")
            for cls in info['classes']:
                content.append(f"#### {cls['name']}")
                content.append("")
                if cls['docstring']:
                    content.append(cls['docstring'])
                    content.append("")
                
                if cls['methods']:
                    content.append("**Methods:**")
                    content.append("")
                    for method in cls['methods']:
                        content.append(f"- `{method['signature']}`")
                        if method['docstring']:
                            # Extract first line of docstring for brief description
                            first_line = method['docstring'].split('\n')[0].strip()
                            content.append(f"  - {first_line}")
                    content.append("")
        
        # Functions
        if info['functions']:
            content.append("### Functions")
            content.append("")
            for func in info['functions']:
                content.append(f"#### {func['name']}")
                content.append("")
                content.append(f"```python")
                content.append(func['signature'])
                content.append("```")
                content.append("")
                if func['docstring']:
                    content.append(func['docstring'])
                    content.append("")
    
    # Examples section (extract from docstrings)
    examples = []
    for func in info['functions']:
        if 'Example:' in func['docstring'] or 'Examples:' in func['docstring']:
            # Extract example from docstring
            lines = func['docstring'].split('\n')
            in_example = False
            example_lines = []
            for line in lines:
                if 'Example:' in line or 'Examples:' in line:
                    in_example = True
                    continue
                if in_example:
                    if line.strip().startswith('>>>') or line.strip().startswith('...'):
                        example_lines.append(line.strip())
                    elif line.strip() and not line.strip().startswith(' '):
                        break
            if example_lines:
                examples.append({
                    'function': func['name'],
                    'code': '\n'.join(example_lines)
                })
    
    if examples:
        content.append("## Examples")
        content.append("")
        for example in examples:
            content.append(f"### {example['function']}")
            content.append("")
            content.append("```python")
            content.append(example['code'])
            content.append("```")
            content.append("")
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write('\n'.join(content))
    
    print(f"Generated documentation for {info['name']} -> {output_path}")


def main():
    """Main function to generate documentation for all shared libraries."""
    repo_root = Path(__file__).parent.parent
    libs_dir = repo_root / "libs"
    docs_output_dir = repo_root / "docs-src" / "libraries"
    
    # Ensure output directory exists
    docs_output_dir.mkdir(parents=True, exist_ok=True)
    
    if not libs_dir.exists():
        print(f"Error: {libs_dir} does not exist")
        return 1
    
    # Generate documentation for each library
    for lib_path in libs_dir.iterdir():
        if lib_path.is_dir() and not lib_path.name.startswith('.'):
            output_file = docs_output_dir / f"{lib_path.name}.md"
            try:
                generate_library_documentation(lib_path, output_file)
            except Exception as e:
                print(f"Error generating documentation for {lib_path.name}: {e}")
    
    print("Documentation generation complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())