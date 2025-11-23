#!/usr/bin/env python3
"""
Export OpenAPI Specification

Exports the OpenAPI specification from the FastAPI application.
"""

import json
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import app


def export_openapi(output_file: str = "openapi.json"):
    """Export OpenAPI specification"""
    openapi_schema = app.openapi()
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"✅ OpenAPI specification exported to {output_path}")
    print(f"   - {len(openapi_schema.get('paths', {}))} endpoints")
    print(f"   - {len(openapi_schema.get('components', {}).get('schemas', {}))} schemas")
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Export OpenAPI specification")
    parser.add_argument(
        "--output",
        default="docs/openapi.json",
        help="Output file path (default: docs/openapi.json)"
    )
    
    args = parser.parse_args()
    
    try:
        export_openapi(args.output)
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error exporting OpenAPI: {e}", file=sys.stderr)
        sys.exit(1)
