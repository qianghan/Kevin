#!/bin/bash

# Generate TypeScript client from OpenAPI spec
echo "Generating TypeScript client from OpenAPI spec..."

# Set directory paths
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OPENAPI_SPEC="${ROOT_DIR}/docs/api/websocket_api.yaml"
OUTPUT_DIR="${ROOT_DIR}/app/ui/src/api-client"

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# Run the generator
python "${ROOT_DIR}/tools/generate_client.py" "${OPENAPI_SPEC}" "${OUTPUT_DIR}"

# Make the generated files part of the UI package
cd "${ROOT_DIR}/app/ui"
npm install

echo "Client generation complete!" 