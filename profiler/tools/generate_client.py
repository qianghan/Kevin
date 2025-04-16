#!/usr/bin/env python3
"""
Generate TypeScript client from OpenAPI specification.
This tool generates TypeScript interface definitions and
a client class from the OpenAPI specification.
"""

import os
import sys
import yaml
import json
from typing import Dict, Any, List
import argparse

def camel_to_pascal(name: str) -> str:
    """Convert camelCase to PascalCase."""
    return name[0].upper() + name[1:]

def format_ts_property(name: str, prop: Dict[str, Any], required: List[str]) -> str:
    """Format a TypeScript property."""
    ts_type = get_ts_type(prop)
    optional = "" if name in required else "?"
    description = f" // {prop.get('description')}" if "description" in prop else ""
    return f"  {name}{optional}: {ts_type};{description}"

def get_ts_type(prop: Dict[str, Any]) -> str:
    """Convert OpenAPI type to TypeScript type."""
    if "$ref" in prop:
        ref = prop["$ref"]
        return ref.split("/")[-1]  # Extract the type name from the reference
    
    prop_type = prop.get("type", "any")
    
    if prop_type == "array":
        items = prop.get("items", {})
        item_type = get_ts_type(items)
        return f"{item_type}[]"
    
    if prop_type == "object":
        if "additionalProperties" in prop and prop["additionalProperties"] is True:
            return "Record<string, any>"
        return "Record<string, any>"  # Default for object without properties
    
    if prop_type == "integer":
        return "number"
    
    if prop_type == "number":
        return "number"
    
    if prop_type == "boolean":
        return "boolean"
    
    if prop_type == "string":
        if "enum" in prop:
            enum_values = [f"'{v}'" for v in prop["enum"]]
            return " | ".join(enum_values)
        format_type = prop.get("format")
        if format_type == "date-time":
            return "string"  # Could use Date, but string is more common for transport
        return "string"
    
    # Default case
    return "any"

def generate_ts_interface(name: str, schema: Dict[str, Any]) -> str:
    """Generate TypeScript interface from schema."""
    lines = [f"export interface {name} {{"]
    
    # Handle allOf (inheritance and composition)
    if "allOf" in schema:
        extended_props = {}
        parent_interfaces = []
        
        for subschema in schema["allOf"]:
            if "$ref" in subschema:
                parent_name = subschema["$ref"].split("/")[-1]
                parent_interfaces.append(parent_name)
            else:
                # Merge properties from subschema
                if "properties" in subschema:
                    extended_props.update(subschema.get("properties", {}))
        
        # Add parent interfaces as extends
        if parent_interfaces:
            lines = [f"export interface {name} extends {', '.join(parent_interfaces)} {{"]
        
        # Properties
        required = next((s.get("required", []) for s in schema["allOf"] if "required" in s), [])
        for prop_name, prop in extended_props.items():
            lines.append(format_ts_property(prop_name, prop, required))
    else:
        # Regular object with properties
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        for prop_name, prop in properties.items():
            lines.append(format_ts_property(prop_name, prop, required))
    
    lines.append("}")
    return "\n".join(lines)

def generate_client_class(api_spec: Dict[str, Any]) -> str:
    """Generate WebSocket client class."""
    # Extract endpoints and message types
    endpoints = []
    for path, path_item in api_spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method == "get" and "101" in operation.get("responses", {}):
                # This is a WebSocket endpoint
                endpoints.append({
                    "path": path,
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "parameters": path_item.get("parameters", [])
                })
    
    # Extract messages from components
    message_schemas = [
        schema_name for schema_name in api_spec.get("components", {}).get("schemas", {})
        if "Message" in schema_name
    ]
    
    # Generate client class
    lines = [
        "import { WebSocketMessage } from '../shared/types';",
        "",
        "/**",
        " * Auto-generated WebSocket client for the Profile API",
        " */",
        "export class ProfileApiClient {",
        "  private ws: WebSocket | null = null;",
        "  private messageHandlers: Map<string, ((data: any) => void)[]> = new Map();",
        "  private baseUrl: string;",
        "  private apiKey: string;",
        "",
        "  /**",
        "   * Create a new ProfileApiClient",
        "   * @param baseUrl The base URL of the API",
        "   * @param apiKey API key for authentication",
        "   */",
        "  constructor(baseUrl: string, apiKey: string) {",
        "    this.baseUrl = baseUrl;",
        "    this.apiKey = apiKey;",
        "  }",
        ""
    ]
    
    # Connect method
    for endpoint in endpoints:
        # Extract path parameters
        path_params = [
            param for param in endpoint.get("parameters", [])
            if param.get("in") == "path"
        ]
        
        # Extract query parameters
        query_params = [
            param for param in endpoint.get("parameters", [])
            if param.get("in") == "query"
        ]
        
        # Generate parameter list for connect method
        param_list = ", ".join([
            f"{param.get('name')}: string" for param in path_params
        ])
        
        lines.extend([
            f"  /**",
            f"   * {endpoint.get('summary', 'Connect to the WebSocket API')}",
            f"   * {endpoint.get('description', '').replace('\n', '\n   * ')}",
        ])
        
        for param in path_params:
            lines.append(f"   * @param {param.get('name')} {param.get('description', '')}")
        
        lines.extend([
            f"   * @returns Promise that resolves when connected",
            f"   */",
            f"  connect({param_list}): Promise<void> {{",
            f"    return new Promise((resolve, reject) => {{",
            f"      if (this.ws) {{",
            f"        console.warn('WebSocket already connected');",
            f"        resolve();",
            f"        return;",
            f"      }}",
            f"",
        ])
        
        # Build URL with path parameters
        url_parts = []
        path = endpoint.get("path", "")
        for param in path_params:
            param_name = param.get("name")
            path = path.replace(f"{{{param_name}}}", f"${{{param_name}}}")
        
        # Add query parameters
        query_string = ""
        if query_params:
            query_parts = []
            for param in query_params:
                param_name = param.get("name")
                if param_name == "x-api-key":
                    query_parts.append(f"x-api-key=${{encodeURIComponent(this.apiKey)}}")
            
            if query_parts:
                query_string = f"?{'+'.join(query_parts)}"
        
        lines.extend([
            f"      const wsUrl = `${{this.baseUrl}}{path}{query_string}`;",
            f"      console.log('Connecting to WebSocket:', wsUrl);",
            f"      this.ws = new WebSocket(wsUrl);",
            f"",
            f"      this.ws.onopen = () => {{",
            f"        console.log('WebSocket connected');",
            f"        resolve();",
            f"      }};",
            f"",
            f"      this.ws.onmessage = (event: MessageEvent) => {{",
            f"        try {{",
            f"          const message: WebSocketMessage = JSON.parse(event.data);",
            f"          console.log('Received WebSocket message:', message);",
            f"          this.handleMessage(message);",
            f"        }} catch (error) {{",
            f"          console.error('Error parsing WebSocket message:', error);",
            f"          this.notifyErrorHandlers('Error parsing message');",
            f"        }}",
            f"      }};",
            f"",
            f"      this.ws.onclose = (event: CloseEvent) => {{",
            f"        console.log('WebSocket disconnected:', event.code, event.reason);",
            f"        this.ws = null;",
            f"        this.notifyErrorHandlers(`Connection closed: ${{event.reason}}`);",
            f"      }};",
            f"",
            f"      this.ws.onerror = (error: Event) => {{",
            f"        console.error('WebSocket error:', error);",
            f"        reject(error);",
            f"      }};",
            f"    }});",
            f"  }}",
            f"",
        ])
    
    # Message handling methods
    lines.extend([
        "  /**",
        "   * Send a message to the WebSocket",
        "   * @param type Message type",
        "   * @param data Message data",
        "   */",
        "  sendMessage(type: string, data: any): void {",
        "    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {",
        "      console.error('WebSocket is not connected');",
        "      this.notifyErrorHandlers('WebSocket is not connected');",
        "      return;",
        "    }",
        "",
        "    const message: WebSocketMessage = {",
        "      type,",
        "      data,",
        "      timestamp: new Date().toISOString()",
        "    };",
        "",
        "    this.ws.send(JSON.stringify(message));",
        "  }",
        "",
        "  /**",
        "   * Register a handler for a specific message type",
        "   * @param type Message type to handle",
        "   * @param handler Handler function",
        "   * @returns Unsubscribe function",
        "   */",
        "  onMessage(type: string, handler: (data: any) => void): () => void {",
        "    if (!this.messageHandlers.has(type)) {",
        "      this.messageHandlers.set(type, []);",
        "    }",
        "    this.messageHandlers.get(type)?.push(handler);",
        "",
        "    // Return unsubscribe function",
        "    return () => {",
        "      const handlers = this.messageHandlers.get(type) || [];",
        "      const index = handlers.indexOf(handler);",
        "      if (index !== -1) {",
        "        handlers.splice(index, 1);",
        "      }",
        "    };",
        "  }",
        "",
        "  /**",
        "   * Disconnect from the WebSocket",
        "   */",
        "  disconnect(): void {",
        "    if (this.ws) {",
        "      this.ws.close();",
        "      this.ws = null;",
        "    }",
        "  }",
        "",
        "  private handleMessage(message: WebSocketMessage): void {",
        "    const handlers = this.messageHandlers.get(message.type);",
        "    if (handlers) {",
        "      handlers.forEach(handler => handler(message.data || message));",
        "    }",
        "  }",
        "",
        "  private notifyErrorHandlers(errorMessage: string): void {",
        "    const handlers = this.messageHandlers.get('error');",
        "    if (handlers) {",
        "      handlers.forEach(handler => handler({ error: errorMessage }));",
        "    }",
        "  }",
    ])
    
    # Generate convenience methods for specific message types
    for schema_name in message_schemas:
        if schema_name.endswith("ResponseMessage"):
            continue  # Skip response messages
        
        # Get the message type from the schema
        schema = api_spec.get("components", {}).get("schemas", {}).get(schema_name, {})
        message_type = None
        
        if "allOf" in schema:
            for subschema in schema["allOf"]:
                if "properties" in subschema and "type" in subschema["properties"]:
                    if "enum" in subschema["properties"]["type"]:
                        message_type = subschema["properties"]["type"]["enum"][0]
        
        if not message_type:
            continue
        
        # Generate convenience method
        method_name = message_type.replace("_", "")
        lines.extend([
            "",
            f"  /**",
            f"   * Send a {message_type} message",
            f"   * @param data Message data",
            f"   */",
            f"  {method_name}(data: any): void {{",
            f"    this.sendMessage('{message_type}', data);",
            f"  }}",
        ])
    
    lines.extend([
        "}",
        ""
    ])
    
    return "\n".join(lines)

def generate_ts_client(openapi_file: str, output_dir: str) -> None:
    """Generate TypeScript client from OpenAPI spec."""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Read OpenAPI spec
    with open(openapi_file, 'r') as f:
        api_spec = yaml.safe_load(f)
    
    # Generate interfaces
    interfaces = []
    for name, schema in api_spec.get("components", {}).get("schemas", {}).items():
        interfaces.append(generate_ts_interface(name, schema))
    
    # Write interfaces
    interfaces_file = os.path.join(output_dir, "api-interfaces.ts")
    with open(interfaces_file, 'w') as f:
        f.write("// Auto-generated TypeScript interfaces for API\n")
        f.write("// Generated from OpenAPI spec\n\n")
        f.write("\n\n".join(interfaces))
    
    # Generate client
    client = generate_client_class(api_spec)
    client_file = os.path.join(output_dir, "api-client.ts")
    with open(client_file, 'w') as f:
        f.write("// Auto-generated TypeScript client for API\n")
        f.write("// Generated from OpenAPI spec\n\n")
        f.write(client)
    
    print(f"Generated TypeScript interfaces: {interfaces_file}")
    print(f"Generated TypeScript client: {client_file}")

def main() -> None:
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate TypeScript client from OpenAPI spec")
    parser.add_argument("openapi_file", help="Path to OpenAPI spec (YAML)")
    parser.add_argument("output_dir", help="Output directory for generated files")
    args = parser.parse_args()
    
    generate_ts_client(args.openapi_file, args.output_dir)

if __name__ == "__main__":
    main() 