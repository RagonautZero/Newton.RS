#!/usr/bin/env python3
"""
Main entry point for LogicBridge Rule Engine
"""

import os
import sys
import uvicorn
from logicbridge.api import create_app

def main():
    """Main entry point"""
    # Check if running as CLI or server
    if len(sys.argv) > 1:
        # Run CLI
        from logicbridge.cli import main as cli_main
        cli_main()
    else:
        # Run web server
        app = create_app()
        
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", "5000"))
        
        print("🚀 Starting Newton.RS Rule Engine")
        print(f"📡 API server: http://{host}:{port}")
        print(f"🌐 Web interface: http://{host}:{port}")
        print(f"📊 Health check: http://{host}:{port}/health")
        print()
        print("Features available:")
        print("  • YAML/JSON rule definition parser")
        print("  • Deterministic rule evaluation engine") 
        print("  • REST API for rule management")
        print("  • Audit logging with SHA-based versioning")
        print("  • Web interface for testing")
        print("  • CLI tools for rule management")
        print()
        
        try:
            uvicorn.run(
                app, 
                host=host, 
                port=port,
                log_level="info"
            )
        except KeyboardInterrupt:
            print("\n👋 Shutting down LogicBridge...")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Failed to start server: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
