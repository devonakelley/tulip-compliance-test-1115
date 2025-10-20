"""
Basic Kalibr SDK Example - Function-level API integration
This demonstrates the original function-level capabilities of Kalibr.
"""

from kalibr import Kalibr

# Create a basic Kalibr instance
sdk = Kalibr(title="Basic Kalibr Demo", base_url="http://localhost:8000")

@sdk.action("greet", "Greet someone with a personalized message")
def greet_user(name: str, greeting: str = "Hello"):
    """Simple greeting function"""
    return {"message": f"{greeting}, {name}! Welcome to Kalibr SDK."}

@sdk.action("calculate", "Perform basic mathematical operations")
def calculate(operation: str, a: float, b: float):
    """Basic calculator functionality"""
    operations = {
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else None
    }
    
    result = operations.get(operation)
    if result is None:
        return {"error": f"Invalid operation '{operation}' or division by zero"}
    
    return {
        "operation": operation,
        "operands": [a, b],
        "result": result
    }

@sdk.action("validate_email", "Check if an email address is valid")
def validate_email(email: str):
    """Simple email validation"""
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    is_valid = bool(re.match(pattern, email))
    
    return {
        "email": email,
        "is_valid": is_valid,
        "message": "Valid email address" if is_valid else "Invalid email format"
    }

@sdk.action("text_stats", "Get statistics about a text string")
def text_statistics(text: str):
    """Analyze text and return statistics"""
    words = text.split()
    sentences = text.split('.') + text.split('!') + text.split('?')
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return {
        "character_count": len(text),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "average_word_length": sum(len(word) for word in words) / len(words) if words else 0,
        "longest_word": max(words, key=len) if words else None
    }

# The SDK instance is automatically discovered by the Kalibr CLI
# To run this: kalibr serve basic_kalibr_example.py