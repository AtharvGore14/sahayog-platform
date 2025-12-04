"""
Startup script for the Automated Waste Financial Ledger API server.
Run this from the project root directory.
"""
import uvicorn
import sys
import os

# Ensure we're running from the project root
if __name__ == "__main__":
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Set UTF-8 encoding for Windows console
    import sys
    if sys.platform == 'win32':
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    print("Starting Automated Waste Financial Ledger API Server...")
    print("API will be available at http://localhost:8000")
    print("API Documentation at http://localhost:8000/docs")
    print("\nPress CTRL+C to stop the server.\n")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

