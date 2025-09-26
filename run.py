#!/usr/bin/env python3
"""
Translation System - Main Entry Point
Multi-Modal Document Translation System
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        workers=1
    )
