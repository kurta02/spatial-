#!/bin/bash
# Spatial Constellation System Startup Script

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}=== Spatial Constellation System Startup ===${NC}"
echo "Project directory: $PROJECT_DIR"
echo

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv "$PROJECT_DIR/venv"
    echo -e "${GREEN}Virtual environment created.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$PROJECT_DIR/venv/bin/activate"

# Upgrade pip and install requirements
echo -e "${BLUE}Installing/updating dependencies...${NC}"
pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"

# Check for .env file
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found!${NC}"
    echo "Copying .env.example to .env..."
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo -e "${RED}Please edit .env file with your API keys and database credentials.${NC}"
    echo "Then run this script again."
    exit 1
fi

# Load environment variables
export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)

# Check PostgreSQL connection
echo -e "${BLUE}Checking PostgreSQL connection...${NC}"
if ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" >/dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to PostgreSQL server.${NC}"
    echo "Please ensure PostgreSQL is running and credentials are correct."
    echo "Check: sudo systemctl status postgresql"
    exit 1
fi

echo -e "${GREEN}PostgreSQL connection successful.${NC}"

# Setup database if needed
echo -e "${BLUE}Setting up database...${NC}"
cd "$PROJECT_DIR"
python scripts/setup_database.py

# Check if all required API keys are present
missing_keys=()
if [ -z "$OPENAI_API_KEY" ]; then
    missing_keys+=("OPENAI_API_KEY")
fi
if [ -z "$ANTHROPIC_API_KEY" ]; then
    missing_keys+=("ANTHROPIC_API_KEY")
fi

if [ ${#missing_keys[@]} -gt 0 ]; then
    echo -e "${YELLOW}Warning: Missing API keys: ${missing_keys[*]}${NC}"
    echo "Some LLM models may not be available."
fi

# Start the system components
echo -e "${BLUE}Starting system components...${NC}"

# Create necessary directories
mkdir -p "$PROJECT_DIR/data/logs"
mkdir -p "$PROJECT_DIR/data/workspace"
mkdir -p "$PROJECT_DIR/data/conversations"

# Function to start component in background
start_component() {
    local name="$1"
    local script="$2"
    local logfile="$PROJECT_DIR/data/logs/${name}.log"
    
    echo -e "${BLUE}Starting $name...${NC}"
    nohup python "$script" > "$logfile" 2>&1 &
    local pid=$!
    echo "$pid" > "$PROJECT_DIR/data/logs/${name}.pid"
    echo -e "${GREEN}$name started (PID: $pid)${NC}"
}

# Check what the user wants to start
case "${1:-all}" in
    "cli"|"chat")
        echo -e "${GREEN}Starting conversational CLI...${NC}"
        python "$PROJECT_DIR/core/conversational_cli.py"
        ;;
    "api")
        echo -e "${GREEN}Starting Flask API...${NC}"
        cd "$PROJECT_DIR"
        python "$PROJECT_DIR/api/app.py"
        ;;
    "all")
        # Start Flask API in background
        start_component "flask_api" "$PROJECT_DIR/api/app.py"
        
        # Wait a moment for API to start
        sleep 2
        
        # Show status
        echo
        echo -e "${GREEN}=== System Status ===${NC}"
        echo "Flask API: Running (see data/logs/flask_api.log)"
        echo "Database: Connected"
        echo "Configuration: Loaded"
        echo
        echo -e "${BLUE}Available commands:${NC}"
        echo "  python core/conversational_cli.py  # Start CLI"
        echo "  curl http://localhost:5000/health   # Check API health"
        echo "  ./scripts/stop_system.sh           # Stop all components"
        echo
        echo -e "${GREEN}System startup complete!${NC}"
        ;;
    "status")
        echo -e "${BLUE}Checking system status...${NC}"
        
        # Check if API is running
        if [ -f "$PROJECT_DIR/data/logs/flask_api.pid" ]; then
            api_pid=$(cat "$PROJECT_DIR/data/logs/flask_api.pid")
            if ps -p "$api_pid" > /dev/null 2>&1; then
                echo -e "${GREEN}Flask API: Running (PID: $api_pid)${NC}"
            else
                echo -e "${RED}Flask API: Stopped${NC}"
            fi
        else
            echo -e "${RED}Flask API: Not started${NC}"
        fi
        
        # Check database
        if pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" >/dev/null 2>&1; then
            echo -e "${GREEN}Database: Connected${NC}"
        else
            echo -e "${RED}Database: Not accessible${NC}"
        fi
        ;;
    "stop")
        echo -e "${BLUE}Stopping system components...${NC}"
        for pidfile in "$PROJECT_DIR/data/logs"/*.pid; do
            if [ -f "$pidfile" ]; then
                pid=$(cat "$pidfile")
                component=$(basename "$pidfile" .pid)
                if ps -p "$pid" > /dev/null 2>&1; then
                    echo -e "${BLUE}Stopping $component (PID: $pid)...${NC}"
                    kill "$pid"
                    echo -e "${GREEN}$component stopped.${NC}"
                else
                    echo -e "${YELLOW}$component already stopped.${NC}"
                fi
                rm "$pidfile"
            fi
        done
        echo -e "${GREEN}All components stopped.${NC}"
        ;;
    *)
        echo "Usage: $0 [all|cli|api|status|stop]"
        echo "  all    - Start all components (default)"
        echo "  cli    - Start conversational CLI only"
        echo "  api    - Start Flask API only"
        echo "  status - Check system status"
        echo "  stop   - Stop all components"
        exit 1
        ;;
esac