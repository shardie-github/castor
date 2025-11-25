#!/usr/bin/env python3
"""
API Documentation Generator

Extracts API endpoints from FastAPI routes and generates comprehensive documentation.
"""

import ast
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Endpoint:
    path: str
    methods: List[str] = field(default_factory=list)
    handler: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    summary: str = ""
    response_model: str = ""

def extract_routes_from_file(file_path: Path) -> List[Endpoint]:
    """Extract route definitions from a Python file"""
    endpoints = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return endpoints
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Look for route decorators
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Attribute):
                        # @router.get(), @router.post(), etc.
                        method = decorator.func.attr.upper()
                        if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS']:
                            endpoint = Endpoint(
                                handler=node.name,
                                methods=[method]
                            )
                            
                            # Extract path from decorator arguments
                            if decorator.args:
                                path_arg = decorator.args[0]
                                if isinstance(path_arg, ast.Constant):
                                    endpoint.path = path_arg.value
                                elif isinstance(path_arg, ast.Str):  # Python < 3.8
                                    endpoint.path = path_arg.s
                            
                            # Extract docstring
                            if ast.get_docstring(node):
                                endpoint.description = ast.get_docstring(node)
                            
                            # Extract summary and tags from decorator keywords
                            for keyword in decorator.keywords:
                                if keyword.arg == 'summary' and isinstance(keyword.value, ast.Constant):
                                    endpoint.summary = keyword.value.value
                                elif keyword.arg == 'tags' and isinstance(keyword.value, ast.List):
                                    endpoint.tags = [elt.value for elt in keyword.value.elts if isinstance(elt, ast.Constant)]
                            
                            endpoints.append(endpoint)
    
    return endpoints

def find_api_files(src_dir: Path) -> List[Path]:
    """Find all API route files"""
    api_files = []
    api_dir = src_dir / 'api'
    
    if not api_dir.exists():
        return api_files
    
    for file_path in api_dir.glob('*.py'):
        if file_path.name != '__init__.py' and file_path.name != 'route_registration.py':
            api_files.append(file_path)
    
    return api_files

def extract_router_prefix(file_path: Path) -> str:
    """Extract router prefix from route registration"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return ""
    
    # Look for app.include_router calls
    pattern = r'app\.include_router\((\w+)\.router,\s*prefix=["\']([^"\']+)["\']'
    matches = re.findall(pattern, content)
    
    for module_name, prefix in matches:
        if file_path.stem == module_name:
            return prefix
    
    return ""

def generate_markdown_docs(endpoints_by_module: Dict[str, List[Endpoint]], base_url: str = "http://localhost:8000") -> str:
    """Generate Markdown documentation"""
    md = f"""# API Documentation

**Base URL:** `{base_url}`

This document provides a comprehensive reference for all API endpoints.

## Table of Contents

"""
    
    # Generate TOC
    for module_name in sorted(endpoints_by_module.keys()):
        anchor = module_name.lower().replace('_', '-')
        md += f"- [{module_name.title()}](#{anchor})\n"
    
    md += "\n---\n\n"
    
    # Generate endpoint documentation
    for module_name, endpoints in sorted(endpoints_by_module.items()):
        if not endpoints:
            continue
        
        md += f"## {module_name.title()}\n\n"
        
        for endpoint in endpoints:
            methods_str = ', '.join(endpoint.methods)
            full_path = endpoint.path
            
            md += f"### `{methods_str} {full_path}`\n\n"
            
            if endpoint.summary:
                md += f"**Summary:** {endpoint.summary}\n\n"
            
            if endpoint.description:
                md += f"{endpoint.description}\n\n"
            
            if endpoint.tags:
                md += f"**Tags:** {', '.join(endpoint.tags)}\n\n"
            
            md += "---\n\n"
    
    return md

def main():
    """Main function"""
    src_dir = Path(__file__).parent.parent / 'src'
    
    if not src_dir.exists():
        print(f"Error: {src_dir} does not exist")
        return
    
    # Read route registration to get prefixes
    route_registration = src_dir / 'api' / 'route_registration.py'
    prefixes = {}
    
    if route_registration.exists():
        with open(route_registration, 'r') as f:
            content = f.read()
            # Extract prefixes
            pattern = r'app\.include_router\((\w+)\.router,\s*prefix=["\']([^"\']+)["\']'
            for match in re.findall(pattern, content):
                module_name, prefix = match
                prefixes[module_name] = prefix
    
    # Find all API files
    api_files = find_api_files(src_dir)
    
    endpoints_by_module = {}
    
    for api_file in api_files:
        module_name = api_file.stem
        endpoints = extract_routes_from_file(api_file)
        
        # Add prefix to paths
        prefix = prefixes.get(module_name, '')
        for endpoint in endpoints:
            if prefix and not endpoint.path.startswith(prefix):
                endpoint.path = prefix + endpoint.path
        
        if endpoints:
            endpoints_by_module[module_name] = endpoints
    
    # Generate documentation
    docs_dir = Path(__file__).parent.parent / 'docs'
    docs_dir.mkdir(exist_ok=True)
    
    md_content = generate_markdown_docs(endpoints_by_module)
    
    output_file = docs_dir / 'api.md'
    with open(output_file, 'w') as f:
        f.write(md_content)
    
    print(f"✅ Generated API documentation: {output_file}")
    print(f"   Found {sum(len(eps) for eps in endpoints_by_module.values())} endpoints across {len(endpoints_by_module)} modules")

if __name__ == '__main__':
    main()
