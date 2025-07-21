#!/bin/bash
# Codex Supervision System Setup Script

echo "[🔧] Setting up Codex supervision framework..."

# Step 1: Enforce post-commit hook
echo "[1/3] Installing post-commit hook..."
cp ./post-commit .git/hooks/post-commit
chmod +x .git/hooks/post-commit
echo "✅ post-commit hook installed."

# Step 2: Place HALT marker README
echo "[2/3] Verifying HALT marker documentation..."
if [ ! -f HALT_marker_readme.md ]; then
  echo "⚠️  HALT_marker_readme.md missing. Download and place it in the repo root."
else
  echo "✅ HALT_marker_readme.md found."
fi

# Step 3: Confirm control files
echo "[3/3] Checking roadmap control files..."
for file in "Master System Documentation.md" "AI_EXECUTION_PROTOCOL.md" "codex_log.md"
do
  if [ -f "$file" ]; then
    echo "✅ $file found."
  else
    echo "🚨 $file missing! Codex will be uncontrolled without it."
  fi
done

echo "[✅] Codex supervision setup complete."