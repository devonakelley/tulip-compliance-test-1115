# Enhanced Kalibr SDK Examples

This directory contains examples demonstrating both the original function-level Kalibr capabilities and the new enhanced app-level features.

## Examples Included

### 1. Basic Kalibr Example (`basic_kalibr_example.py`)
Demonstrates the original Kalibr SDK capabilities:
- Simple function decoration with `@sdk.action()`
- Basic parameter handling and type inference
- Compatible with GPT Actions and Claude MCP
- Simple API endpoints

**Features shown:**
- Text processing functions
- Mathematical calculations  
- Email validation
- Text statistics

**To run:**
```bash
kalibr serve basic_kalibr_example.py
```

**Test endpoints:**
- `POST /proxy/greet` - Greeting function
- `POST /proxy/calculate` - Basic calculator
- `POST /proxy/validate_email` - Email validation
- `POST /proxy/text_stats` - Text analysis

### 2. Enhanced Kalibr Example (`enhanced_kalibr_example.py`)
Demonstrates the new enhanced app-level capabilities:
- File upload handling
- Session management
- Streaming responses
- Complex workflows
- Multi-model schema generation

**Features shown:**
- File upload and analysis
- Session-based note taking
- Real-time streaming data
- Multi-step workflows
- Advanced parameter handling

**To run:**
```bash
kalibr serve enhanced_kalibr_example.py --app-mode
```

**Test endpoints:**
- `POST /upload/analyze_document` - File upload analysis
- `POST /session/save_note` - Session-based note saving
- `GET /stream/count_with_progress` - Streaming counter
- `POST /workflow/process_text_analysis` - Complex text workflow

## Multi-Model Integration

Both examples automatically generate schemas for multiple AI models:

### Available Schema Endpoints:
- **Claude MCP**: `/mcp.json`
- **GPT Actions**: `/openapi.json` 
- **Gemini Extensions**: `/schemas/gemini`
- **Microsoft Copilot**: `/schemas/copilot`

### Management Endpoints:
- **Health Check**: `/health`
- **Supported Models**: `/models/supported`
- **API Documentation**: `/docs`

## Usage Examples

### Basic Function Call:
```bash
curl -X POST http://localhost:8000/proxy/greet \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "greeting": "Hi"}'
```

### File Upload:
```bash
curl -X POST http://localhost:8000/upload/analyze_document \
  -F "file=@example.txt"
```

### Session Management:
```bash
# Save a note (creates session)
curl -X POST http://localhost:8000/session/save_note \
  -H "Content-Type: application/json" \
  -d '{"note_title": "My Note", "note_content": "This is a test note"}'

# Get notes (use session ID from previous response)
curl -X POST http://localhost:8000/session/get_notes \
  -H "Content-Type: application/json" \
  -H "x-session-id: <session-id-here>" \
  -d '{}'
```

### Streaming Data:
```bash
curl http://localhost:8000/stream/count_with_progress?max_count=5&delay_seconds=1
```

### Complex Workflow:
```bash
curl -X POST http://localhost:8000/workflow/process_text_analysis \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a sample text for analysis. It contains multiple sentences and words for testing the workflow capabilities."}'
```

## Integration with AI Models

### GPT Actions Setup:
1. Copy the OpenAPI schema from `/openapi.json`
2. Create a new GPT Action in ChatGPT
3. Paste the schema and set the base URL

### Claude MCP Setup:
1. Add the MCP server configuration:
```json
{
  "mcp": {
    "servers": {
      "kalibr": {
        "command": "curl",
        "args": ["http://localhost:8000/mcp.json"]
      }
    }
  }
}
```

### Gemini Extensions:
1. Use the schema from `/schemas/gemini`
2. Configure according to Gemini's extension documentation

### Microsoft Copilot:
1. Use the schema from `/schemas/copilot`  
2. Follow Microsoft's plugin development guidelines

## Advanced Features

### Authentication (Optional):
Uncomment the authentication line in enhanced example:
```python
app.enable_auth("your-secret-jwt-key-here")
```

### Custom Schema Generation:
The framework supports extensible schema generation for future AI models through the `CustomModelSchemaGenerator` class.

### Error Handling:
All endpoints include comprehensive error handling with meaningful error messages.

### Type Safety:
Full support for Python type hints with automatic schema generation.

## Development Notes

- The enhanced framework is backward compatible with original Kalibr apps
- Session data is stored in memory (use external storage for production)
- File uploads are handled in memory (implement persistent storage as needed)
- Streaming uses Server-Sent Events (SSE) format
- All examples include proper async/await handling where needed

## Next Steps

1. Try the examples with different AI models
2. Modify the examples to fit your specific use case
3. Explore the source code in `/app/backend/kalibr/` for advanced customization
4. Build your own enhanced Kalibr applications!