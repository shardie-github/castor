#!/usr/bin/env bash
# Generate OpenAPI Specification
# Exports OpenAPI spec from FastAPI application to JSON and YAML formats

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Generating OpenAPI Specification ===${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3.11+"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q -r requirements.txt
else
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d ".venv" ]; then
        source .venv/bin/activate
    fi
fi

# Set environment variables for OpenAPI generation
export SKIP_ENV_VALIDATION="true"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/test"
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
export JWT_SECRET="test_secret_key_min_32_chars_long_for_openapi_generation"
export ENCRYPTION_KEY="test_encryption_key_min_32_chars_long_for_openapi"

# Generate OpenAPI JSON
echo -e "${BLUE}Generating OpenAPI JSON...${NC}"
python3 scripts/export_openapi.py --output docs/openapi.json

# Convert JSON to YAML if pyyaml is available
if python3 -c "import yaml" 2>/dev/null; then
    echo -e "${BLUE}Generating OpenAPI YAML...${NC}"
    python3 -c "
import json
import yaml
from pathlib import Path

json_path = Path('docs/openapi.json')
yaml_path = Path('docs/openapi.yaml')

with open(json_path) as f:
    data = json.load(f)

with open(yaml_path, 'w') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

print(f'✅ OpenAPI YAML exported to {yaml_path}')
"
else
    echo "⚠️  PyYAML not installed, skipping YAML generation"
    echo "   Install with: pip install pyyaml"
fi

# Count endpoints and schemas
ENDPOINTS=$(python3 -c "import json; data = json.load(open('docs/openapi.json')); print(len(data.get('paths', {})))")
SCHEMAS=$(python3 -c "import json; data = json.load(open('docs/openapi.json')); print(len(data.get('components', {}).get('schemas', {})))")

echo ""
echo -e "${GREEN}✅ OpenAPI specification generated successfully${NC}"
echo "   - Endpoints: $ENDPOINTS"
echo "   - Schemas: $SCHEMAS"
echo "   - JSON: docs/openapi.json"
if [ -f "docs/openapi.yaml" ]; then
    echo "   - YAML: docs/openapi.yaml"
fi
echo ""
echo "View interactive docs at: http://localhost:8000/api/docs"
