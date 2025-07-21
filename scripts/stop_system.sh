#!/bin/bash
# Spatial Constellation System Stop Script

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

echo -e "${BLUE}=== Spatial Constellation System Stop ===${NC}"
echo "Project directory: $PROJECT_DIR"
echo

# Function to stop component by PID file
stop_component() {
    local name="$1"
    local pidfile="$PROJECT_DIR/data/logs/${name}.pid"
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${BLUE}Stopping $name (PID: $pid)...${NC}"
            kill "$pid"
            
            # Wait for process to stop
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            if ps -p "$pid" > /dev/null 2>&1; then
                echo -e "${YELLOW}Force stopping $name...${NC}"
                kill -9 "$pid"
            fi
            
            echo -e "${GREEN}$name stopped.${NC}"
        else
            echo -e "${YELLOW}$name not running (PID $pid not found).${NC}"
        fi
        rm "$pidfile"
    else
        echo -e "${YELLOW}$name PID file not found.${NC}"
    fi
}

# Function to stop component by name
stop_by_name() {
    local process_name="$1"
    local display_name="$2"
    
    local pids=$(pgrep -f "$process_name" || true)
    if [ -n "$pids" ]; then
        echo -e "${BLUE}Stopping $display_name processes...${NC}"
        echo "$pids" | xargs kill
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "$process_name" || true)
        if [ -n "$remaining_pids" ]; then
            echo -e "${YELLOW}Force stopping $display_name...${NC}"
            echo "$remaining_pids" | xargs kill -9
        fi
        echo -e "${GREEN}$display_name stopped.${NC}"
    else
        echo -e "${YELLOW}No $display_name processes found.${NC}"
    fi
}

# Stop components in reverse order of startup
echo -e "${BLUE}Stopping system components...${NC}"

# Stop Flask API
stop_component "flask_api"

# Stop any remaining Python processes related to the system
stop_by_name "conversational_cli.py" "Conversational CLI"
stop_by_name "spatial-constellation" "System processes"

# Clean up any remaining PID files
if [ -d "$PROJECT_DIR/data/logs" ]; then
    rm -f "$PROJECT_DIR/data/logs"/*.pid
    echo -e "${GREEN}Cleaned up PID files.${NC}"
fi

# Check for any remaining processes
echo
echo -e "${BLUE}Checking for remaining processes...${NC}"

remaining_processes=$(ps aux | grep -E "(conversational_cli|spatial-constellation|flask.*5000)" | grep -v grep || true)
if [ -n "$remaining_processes" ]; then
    echo -e "${YELLOW}Warning: Some processes may still be running:${NC}"
    echo "$remaining_processes"
    echo
    echo "You may need to manually stop these processes with:"
    echo "  kill <PID>"
else
    echo -e "${GREEN}No remaining system processes found.${NC}"
fi

# Show final status
echo
echo -e "${GREEN}=== System Stop Complete ===${NC}"
echo "All Spatial Constellation components have been stopped."
echo
echo "To start the system again:"
echo "  ./scripts/start_system.sh"