"""
Enhanced Kalibr App Example - App-level capabilities
This demonstrates the new enhanced capabilities including file uploads,
sessions, streaming, workflows, and multi-model schema generation.
"""

from kalibr import KalibrApp
from kalibr.types import FileUpload, Session, StreamingResponse, WorkflowState, AuthenticatedUser
import asyncio
import json
from datetime import datetime
from typing import List

# Create an enhanced KalibrApp instance
app = KalibrApp(title="Enhanced Kalibr Demo", base_url="http://localhost:8000")

# Basic action (compatible with original Kalibr)
@app.action("hello", "Say hello with enhanced capabilities")
def hello_enhanced(name: str = "World", include_timestamp: bool = False):
    """Enhanced hello function with optional timestamp"""
    message = f"Hello, {name}! This is Enhanced Kalibr v2.0"
    
    response = {"message": message}
    if include_timestamp:
        response["timestamp"] = datetime.now().isoformat()
    
    return response

# File upload handler
@app.file_handler("analyze_document", [".txt", ".md", ".py", ".js", ".json"])
async def analyze_document(file: FileUpload):
    """Analyze uploaded document and return insights"""
    try:
        # Decode file content
        content = file.content.decode('utf-8')
        
        # Basic analysis
        lines = content.split('\n')
        words = content.split()
        
        # Language detection based on file extension
        language = "text"
        if file.filename.endswith('.py'):
            language = "python"
        elif file.filename.endswith('.js'):
            language = "javascript"
        elif file.filename.endswith('.json'):
            language = "json"
            try:
                json_data = json.loads(content)
                return {
                    "upload_id": file.upload_id,
                    "filename": file.filename,
                    "analysis": {
                        "type": "json",
                        "valid_json": True,
                        "keys": list(json_data.keys()) if isinstance(json_data, dict) else None,
                        "size_bytes": file.size
                    }
                }
            except json.JSONDecodeError:
                pass
        
        return {
            "upload_id": file.upload_id,
            "filename": file.filename,
            "analysis": {
                "language": language,
                "line_count": len(lines),
                "word_count": len(words),
                "character_count": len(content),
                "size_bytes": file.size,
                "non_empty_lines": len([line for line in lines if line.strip()]),
                "estimated_reading_time_minutes": len(words) / 200  # Average reading speed
            }
        }
    except UnicodeDecodeError:
        return {
            "upload_id": file.upload_id,
            "filename": file.filename,
            "error": "File is not text-readable (binary file)",
            "size_bytes": file.size
        }

# Session-aware action
@app.session_action("save_note", "Save a note to user session")
async def save_note(session: Session, note_title: str, note_content: str):
    """Save a note to the user's session"""
    
    # Initialize notes if not exists
    if 'notes' not in session.data:
        session.data['notes'] = []
    
    # Create note object
    note = {
        "id": len(session.data['notes']) + 1,
        "title": note_title,
        "content": note_content,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    
    session.data['notes'].append(note)
    session.set('last_note_id', note['id'])
    
    return {
        "status": "saved",
        "note": note,
        "total_notes": len(session.data['notes']),
        "session_id": session.session_id
    }

@app.session_action("get_notes", "Retrieve all notes from session")
async def get_notes(session: Session):
    """Get all notes from the user's session"""
    notes = session.get('notes', [])
    
    return {
        "notes": notes,
        "count": len(notes),
        "session_id": session.session_id,
        "last_note_id": session.get('last_note_id')
    }

# Streaming action
@app.stream_action("count_with_progress", "Stream counting with progress updates")
async def count_with_progress(max_count: int = 10, delay_seconds: float = 1.0):
    """Stream counting numbers with progress indication"""
    
    for i in range(max_count + 1):
        progress_percent = (i / max_count) * 100
        
        yield {
            "count": i,
            "max_count": max_count,
            "progress_percent": progress_percent,
            "message": f"Counting: {i}/{max_count}",
            "timestamp": datetime.now().isoformat(),
            "is_complete": (i == max_count)
        }
        
        if i < max_count:  # Don't delay after the last item
            await asyncio.sleep(delay_seconds)

@app.stream_action("generate_fibonacci", "Stream Fibonacci sequence")
async def generate_fibonacci(count: int = 20, delay_seconds: float = 0.5):
    """Generate Fibonacci sequence as a stream"""
    
    a, b = 0, 1
    for i in range(count):
        yield {
            "position": i + 1,
            "fibonacci_number": a,
            "sequence_so_far": f"F({i+1}) = {a}",
            "timestamp": datetime.now().isoformat()
        }
        
        a, b = b, a + b
        await asyncio.sleep(delay_seconds)

# Complex workflow
@app.workflow("process_text_analysis", "Complete text analysis workflow")
async def text_analysis_workflow(text: str, workflow_state: WorkflowState):
    """Multi-step text analysis workflow"""
    
    # Step 1: Validation
    workflow_state.step = "validation"
    workflow_state.status = "processing"
    
    if not text or len(text.strip()) < 10:
        workflow_state.status = "error"
        return {"error": "Text must be at least 10 characters long"}
    
    await asyncio.sleep(1)  # Simulate processing time
    
    # Step 2: Basic analysis
    workflow_state.step = "basic_analysis"
    workflow_state.data["validation_passed"] = True
    
    words = text.split()
    sentences = [s.strip() for s in text.replace('!', '.').replace('?', '.').split('.') if s.strip()]
    
    basic_stats = {
        "character_count": len(text),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "paragraph_count": len([p for p in text.split('\n\n') if p.strip()])
    }
    
    workflow_state.data["basic_stats"] = basic_stats
    await asyncio.sleep(1)
    
    # Step 3: Advanced analysis
    workflow_state.step = "advanced_analysis"
    
    # Word frequency
    word_freq = {}
    for word in words:
        clean_word = word.lower().strip('.,!?";:')
        word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
    
    # Top words
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    advanced_stats = {
        "unique_words": len(word_freq),
        "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
        "longest_word": max(words, key=len) if words else None,
        "top_words": top_words,
        "readability_score": min(100, max(0, 100 - (len(words) / len(sentences) if sentences else 1) * 2))
    }
    
    workflow_state.data["advanced_stats"] = advanced_stats
    await asyncio.sleep(1)
    
    # Step 4: Final compilation
    workflow_state.step = "compilation"
    
    result = {
        "workflow_id": workflow_state.workflow_id,
        "analysis_type": "complete_text_analysis",
        "input_text_preview": text[:100] + "..." if len(text) > 100 else text,
        "basic_statistics": basic_stats,
        "advanced_statistics": advanced_stats,
        "processing_steps": ["validation", "basic_analysis", "advanced_analysis", "compilation"],
        "completed_at": datetime.now().isoformat()
    }
    
    workflow_state.step = "completed"
    workflow_state.status = "success"
    workflow_state.data["final_result"] = result
    
    return result

# Data processing workflow
@app.workflow("batch_text_processor", "Process multiple texts in batch")
async def batch_text_processor(texts: List[str], workflow_state: WorkflowState):
    """Process multiple texts as a batch workflow"""
    
    workflow_state.step = "initialization"
    workflow_state.status = "processing"
    
    if not texts or len(texts) == 0:
        workflow_state.status = "error"
        return {"error": "No texts provided for processing"}
    
    results = []
    workflow_state.data["total_texts"] = len(texts)
    
    for i, text in enumerate(texts):
        workflow_state.step = f"processing_text_{i+1}"
        workflow_state.data["current_text"] = i + 1
        workflow_state.data["progress_percent"] = ((i + 1) / len(texts)) * 100
        
        # Process each text
        words = text.split()
        analysis = {
            "text_id": i + 1,
            "text_preview": text[:50] + "..." if len(text) > 50 else text,
            "word_count": len(words),
            "character_count": len(text),
            "sentence_count": len([s for s in text.split('.') if s.strip()])
        }
        
        results.append(analysis)
        await asyncio.sleep(0.5)  # Simulate processing time
    
    # Final aggregation
    workflow_state.step = "aggregation"
    
    total_words = sum(r["word_count"] for r in results)
    total_chars = sum(r["character_count"] for r in results)
    
    final_result = {
        "workflow_id": workflow_state.workflow_id,
        "batch_summary": {
            "total_texts_processed": len(results),
            "total_words": total_words,
            "total_characters": total_chars,
            "average_words_per_text": total_words / len(results) if results else 0,
            "average_chars_per_text": total_chars / len(results) if results else 0
        },
        "individual_results": results,
        "completed_at": datetime.now().isoformat()
    }
    
    workflow_state.step = "completed"
    workflow_state.status = "success"
    workflow_state.data["final_result"] = final_result
    
    return final_result

# Advanced action with multiple parameters
@app.action("advanced_search", "Perform advanced search with multiple filters")
def advanced_search(
    query: str,
    category: str = "all",
    min_score: float = 0.0,
    max_results: int = 10,
    include_metadata: bool = False,
    sort_by: str = "relevance"
):
    """Advanced search function demonstrating complex parameter handling"""
    
    # Simulate search results
    mock_results = [
        {"id": 1, "title": f"Result matching '{query}'", "score": 0.95, "category": category},
        {"id": 2, "title": f"Another match for '{query}'", "score": 0.87, "category": category},
        {"id": 3, "title": f"Related to '{query}'", "score": 0.73, "category": category},
    ]
    
    # Filter by score
    filtered_results = [r for r in mock_results if r["score"] >= min_score]
    
    # Limit results
    filtered_results = filtered_results[:max_results]
    
    # Sort results
    if sort_by == "score":
        filtered_results.sort(key=lambda x: x["score"], reverse=True)
    
    response = {
        "query": query,
        "filters": {
            "category": category,
            "min_score": min_score,
            "max_results": max_results,
            "sort_by": sort_by
        },
        "results": filtered_results,
        "result_count": len(filtered_results)
    }
    
    if include_metadata:
        response["metadata"] = {
            "search_performed_at": datetime.now().isoformat(),
            "processing_time_ms": 45,
            "total_available": len(mock_results)
        }
    
    return response

# Enable authentication (optional)
# app.enable_auth("your-secret-jwt-key-here")

# The app instance is automatically discovered by the Kalibr CLI
# To run this: kalibr serve enhanced_kalibr_example.py --app-mode