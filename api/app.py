#!/usr/bin/env python3
"""
Flask API Wrapper - REST API that wraps the unified orchestrator
Provides HTTP endpoints for all orchestrator functionality
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Add paths for imports
sys.path.insert(0, '/home/kurt/spatial-ai')
sys.path.insert(0, '/home/kurt/migration-workspace')

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

# Import orchestrator and memory systems
from unified_orchestrator import UnifiedOrchestrator
from persistent_memory_postgres import PersistentMemoryPostgres

# Load environment configuration
from dotenv import load_dotenv
load_dotenv("/home/kurt/spatial-ai/.env")

# Configure logging
logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
logger = logging.getLogger(__name__)

class FlaskAPIWrapper:
    """Flask API wrapper for the unified orchestrator"""
    
    def __init__(self, port: int = 5000, use_postgres: bool = True):
        print(f"🔧 Initializing Flask API Wrapper...")
        
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for frontend integration
        self.port = port
        self.use_postgres = use_postgres
        
        print(f"   Creating unified orchestrator...")
        # Initialize orchestrator and memory system
        self.orchestrator = UnifiedOrchestrator()
        print(f"   ✅ Orchestrator created")
        
        # Choose memory backend
        if use_postgres:
            print(f"   Attempting PostgreSQL connection...")
            try:
                self.memory = PersistentMemoryPostgres()
                logger.info("Using PostgreSQL memory backend")
                print(f"   ✅ PostgreSQL memory backend connected")
            except Exception as e:
                logger.warning(f"PostgreSQL unavailable, falling back to SQLite: {e}")
                print(f"   ⚠️  PostgreSQL failed, using SQLite: {e}")
                self.memory = self.orchestrator.memory
        else:
            self.memory = self.orchestrator.memory
            logger.info("Using SQLite memory backend")
            print(f"   ✅ Using SQLite memory backend")
        
        print(f"   Setting up API routes...")
        # Setup routes
        self._setup_routes()
        print(f"   ✅ Routes configured")
        
        logger.info(f"Flask API Wrapper initialized on port {port}")
        print(f"✅ Flask API Wrapper ready on port {port}")
    
    def _setup_routes(self):
        """Setup all API routes"""
        
        # Health check
        @self.app.route('/', methods=['GET'])
        def health_check():
            """API health check"""
            return jsonify({
                "status": "healthy",
                "service": "spatial-ai-api",
                "timestamp": datetime.now().isoformat(),
                "memory_backend": self.memory.__class__.__name__,
                "version": "1.0.0"
            })
        
        # System status
        @self.app.route('/api/system/status', methods=['GET'])
        def get_system_status():
            """Get comprehensive system status"""
            try:
                status = self.orchestrator.get_system_status()
                
                # Store API call in memory
                self.memory.store_memory("api_wrapper", "status_request", 
                                       "System status requested via API",
                                       metadata={"endpoint": "/api/system/status"})
                
                return jsonify({
                    "success": True,
                    "data": status,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting system status: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # Component management
        @self.app.route('/api/components/start', methods=['POST'])
        def start_components():
            """Start components (all or specific)"""
            try:
                data = request.get_json() or {}
                component = data.get('component')  # Optional specific component
                
                if component:
                    result = self.orchestrator.start_component(component)
                    action = f"Started component: {component}"
                else:
                    result = self.orchestrator.start_all_components()
                    action = "Started all components"
                
                # Log the action
                self.memory.store_memory("api_wrapper", "component_start", action,
                                       metadata={"component": component, "result": result})
                
                return jsonify({
                    "success": True,
                    "action": action,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error starting components: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/components/stop', methods=['POST'])
        def stop_components():
            """Stop components (all or specific)"""
            try:
                data = request.get_json() or {}
                component = data.get('component')  # Optional specific component
                
                if component:
                    result = self.orchestrator.stop_component(component)
                    action = f"Stopped component: {component}"
                else:
                    result = self.orchestrator.stop_all_components()
                    action = "Stopped all components"
                
                # Log the action
                self.memory.store_memory("api_wrapper", "component_stop", action,
                                       metadata={"component": component, "result": result})
                
                return jsonify({
                    "success": True,
                    "action": action,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error stopping components: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # Component execution
        @self.app.route('/api/components/execute', methods=['POST'])
        def execute_command():
            """Execute command on specific component"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "success": False,
                        "error": "JSON body required",
                        "timestamp": datetime.now().isoformat()
                    }), 400
                
                component = data.get('component')
                command = data.get('command')
                
                if not component or not command:
                    return jsonify({
                        "success": False,
                        "error": "Both 'component' and 'command' are required",
                        "timestamp": datetime.now().isoformat()
                    }), 400
                
                # Execute command
                result = self.orchestrator.execute_command(component, command, **data.get('kwargs', {}))
                
                return jsonify({
                    "success": True,
                    "component": component,
                    "command": command,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error executing command: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # Memory operations
        @self.app.route('/api/memory/store', methods=['POST'])
        def store_memory():
            """Store memory entry"""
            try:
                data = request.get_json()
                if not data:
                    return jsonify({
                        "success": False,
                        "error": "JSON body required",
                        "timestamp": datetime.now().isoformat()
                    }), 400
                
                component = data.get('component')
                entry_type = data.get('entry_type')
                content = data.get('content')
                
                if not all([component, entry_type, content]):
                    return jsonify({
                        "success": False,
                        "error": "component, entry_type, and content are required",
                        "timestamp": datetime.now().isoformat()
                    }), 400
                
                # Store memory entry
                entry_id = self.memory.store_memory(
                    component=component,
                    entry_type=entry_type,
                    content=content,
                    context=data.get('context', ''),
                    metadata=data.get('metadata', {}),
                    importance=data.get('importance', 5)
                )
                
                return jsonify({
                    "success": True,
                    "entry_id": entry_id,
                    "component": component,
                    "entry_type": entry_type,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error storing memory: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/memory/retrieve', methods=['GET'])
        def retrieve_memory():
            """Retrieve memory entries"""
            try:
                # Get query parameters
                component = request.args.get('component')
                entry_type = request.args.get('entry_type')
                context = request.args.get('context', '')
                limit = int(request.args.get('limit', 100))
                
                # Retrieve entries
                entries = self.memory.retrieve_memory(
                    component=component,
                    entry_type=entry_type,
                    context=context,
                    limit=limit
                )
                
                # Convert datetime objects to strings for JSON serialization
                for entry in entries:
                    if 'created_at' in entry and entry['created_at']:
                        entry['created_at'] = entry['created_at'].isoformat() if hasattr(entry['created_at'], 'isoformat') else str(entry['created_at'])
                    if 'updated_at' in entry and entry['updated_at']:
                        entry['updated_at'] = entry['updated_at'].isoformat() if hasattr(entry['updated_at'], 'isoformat') else str(entry['updated_at'])
                
                return jsonify({
                    "success": True,
                    "entries": entries,
                    "count": len(entries),
                    "filters": {
                        "component": component,
                        "entry_type": entry_type,
                        "context": context,
                        "limit": limit
                    },
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error retrieving memory: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/memory/stats', methods=['GET'])
        def get_memory_stats():
            """Get memory system statistics"""
            try:
                stats = self.memory.get_memory_stats()
                
                return jsonify({
                    "success": True,
                    "stats": stats,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting memory stats: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # Memory consolidation
        @self.app.route('/api/memory/consolidate', methods=['POST'])
        def consolidate_memory():
            """Consolidate memory entries"""
            try:
                data = request.get_json() or {}
                older_than_hours = data.get('older_than_hours')
                
                result = self.memory.consolidate_memory(older_than_hours)
                
                return jsonify({
                    "success": True,
                    "result": result,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error consolidating memory: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # Session management
        @self.app.route('/api/session/current', methods=['GET'])
        def get_current_session():
            """Get current session information"""
            try:
                session_id = self.memory.get_current_session_id()
                
                return jsonify({
                    "success": True,
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error getting current session: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        @self.app.route('/api/session/new', methods=['POST'])
        def start_new_session():
            """Start a new session"""
            try:
                data = request.get_json() or {}
                component = data.get('component')
                
                session_id = self.memory.start_new_session(component)
                
                return jsonify({
                    "success": True,
                    "session_id": session_id,
                    "component": component,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"Error starting new session: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }), 500
        
        # Error handlers
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({
                "success": False,
                "error": "Endpoint not found",
                "timestamp": datetime.now().isoformat()
            }), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({
                "success": False,
                "error": "Internal server error",
                "timestamp": datetime.now().isoformat()
            }), 500
    
    def run(self, debug: bool = False, host: str = '0.0.0.0'):
        """Run the Flask API server"""
        logger.info(f"Starting Flask API server on {host}:{self.port}")
        
        # Store startup in memory
        self.memory.store_memory("api_wrapper", "server_start", 
                                f"Flask API server started on {host}:{self.port}",
                                metadata={"host": host, "port": self.port, "debug": debug})
        
        self.app.run(host=host, port=self.port, debug=debug)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flask API Wrapper for Spatial AI System')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--sqlite', action='store_true', help='Use SQLite instead of PostgreSQL')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Flask API Wrapper on {args.host}:{args.port}")
    print(f"   Debug mode: {args.debug}")
    print(f"   Memory backend: {'SQLite' if args.sqlite else 'PostgreSQL'}")
    
    try:
        # Create and run API wrapper
        api = FlaskAPIWrapper(port=args.port, use_postgres=not args.sqlite)
        print("✅ Flask API Wrapper created successfully")
        
        api.run(debug=args.debug, host=args.host)
    except KeyboardInterrupt:
        logger.info("API server stopped by user")
        print("🛑 API server stopped by user")
    except Exception as e:
        logger.error(f"API server error: {e}")
        print(f"❌ API server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()