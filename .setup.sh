#!/bin/bash
# Codex startup script - validates repo and sets up environment

echo "🔍 Validating repo structure..."

# Check for required files
required_files=(
    "Master System Documentation.md"
    "AI_Execution_Protocol.md" 
    "codex_log.md"
    ".codex"
)

missing_files=()

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -eq 0 ]; then
    echo "✅ All required files present. Codex may proceed."
    echo "📋 Repository: Spatial Constellation System"
    echo "📖 Protocol: AI_Execution_Protocol.md active"
    echo "📝 Logging: codex_log.md ready"
    echo ""
    echo "Codex should now follow the step-by-step roadmap in:"
    echo "Master System Documentation.md"
    exit 0
else
    echo "❌ Missing required files:"
    for file in "${missing_files[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Codex execution blocked until files are present."
    exit 1
fi