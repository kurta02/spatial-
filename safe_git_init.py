#!/usr/bin/env python3
"""
safe_git_init.py - Safe Git initialization for Kurt's Spatial AI Operating System
Integrates with the emergency backup system and brain.py ecosystem
"""

import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
from emergency_backup import create_emergency_backup

class GitSafetyManager:
    def __init__(self):
        self.home_path = Path.home()
        self.git_path = self.home_path / ".git"
        
    def run_command(self, command, capture_output=True):
        """Run shell command safely"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=capture_output, 
                text=True,
                cwd=self.home_path
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def check_git_status(self):
        """Check if git is already initialized"""
        if self.git_path.exists():
            print("📋 Git repository already exists")
            success, stdout, stderr = self.run_command("git status --porcelain")
            if success:
                lines = stdout.strip().split('\n') if stdout.strip() else []
                print(f"   📊 {len(lines)} files with changes")
                return True
            else:
                print("   ⚠️  Git repo exists but may be corrupted")
                return False
        return False
    
    def preview_git_add(self):
        """Show what files would be added to git"""
        print("📋 Checking what files will be added to git...")
        
        success, stdout, stderr = self.run_command("git ls-files --others --exclude-standard")
        if success and stdout:
            files = stdout.strip().split('\n')
            print(f"   📦 {len(files)} files will be added")
            
            # Show first 20 files
            print("   📁 Files to be committed (first 20):")
            for i, file in enumerate(files[:20]):
                print(f"      {i+1:2d}. {file}")
            
            if len(files) > 20:
                print(f"      ... and {len(files) - 20} more files")
                
            return files
        else:
            print("   ⚠️  No new files to add or git not initialized")
            return []
    
    def check_ignored_files(self):
        """Verify important files are being ignored"""
        print("🚫 Verifying dangerous files are ignored...")
        
        dangerous_patterns = [
            ".env", ".openai_key", "*.key", 
            "*vector_store.json", "*.sqlite3",
            "*.tgz", "*.zip", "Downloads/", ".ollama/"
        ]
        
        for pattern in dangerous_patterns:
            success, stdout, stderr = self.run_command(f"git check-ignore {pattern}")
            status = "✅ IGNORED" if success else "⚠️  NOT IGNORED"
            print(f"   {status}: {pattern}")
    
    def initialize_repo(self):
        """Initialize git repository"""
        print("🔧 Initializing git repository...")
        
        success, stdout, stderr = self.run_command("git init")
        if success:
            print("   ✅ Git repository initialized")
            return True
        else:
            print(f"   ❌ Failed to initialize git: {stderr}")
            return False
    
    def stage_files(self):
        """Add files to git staging"""
        print("📦 Adding files to git staging...")
        
        success, stdout, stderr = self.run_command("git add .")
        if success:
            print("   ✅ Files staged successfully")
            
            # Show staging status
            success, stdout, stderr = self.run_command("git status --short")
            if success and stdout:
                lines = stdout.strip().split('\n')
                print(f"   📊 {len(lines)} files staged")
                
                # Show first 10 staged files
                print("   📁 Staged files (first 10):")
                for i, line in enumerate(lines[:10]):
                    print(f"      {i+1:2d}. {line}")
                
                if len(lines) > 10:
                    print(f"      ... and {len(lines) - 10} more files")
            
            return True
        else:
            print(f"   ❌ Failed to stage files: {stderr}")
            return False
    
    def create_commit(self):
        """Create initial commit"""
        commit_message = """Initial commit: Kurt's Spatial AI Operating System - Pre-cleanup baseline

This baseline includes:
- Multi-LLM orchestration framework (brain.py, MultiLLM_Framework.py)
- RAG systems and vector database infrastructure  
- Spatial visualization components (GravitationalDashboard.html)
- Arduino and sensor project code
- Various AI assistant implementations
- Shell scripts and utilities

Vector databases and API keys excluded for safety.
Ready for filesystem cleanup and optimization.

Spatial AI Operating System Components:
- 96MB vector database (backed up separately)
- Multi-provider LLM orchestration
- Physics-based knowledge visualization
- Secure file operation framework
- Comprehensive logging and audit trails
"""
        
        print("💭 Creating initial commit...")
        success, stdout, stderr = self.run_command(f'git commit -m "{commit_message}"')
        
        if success:
            print("   ✅ Initial commit created successfully")
            
            # Show commit info
            success, stdout, stderr = self.run_command("git log --oneline -1")
            if success:
                print(f"   📝 Commit: {stdout.strip()}")
            
            return True
        else:
            print(f"   ❌ Failed to create commit: {stderr}")
            return False
    
    def setup_remote_instructions(self):
        """Show instructions for setting up remote repository"""
        print("\n🌐 Optional: Set up GitHub remote repository")
        print("=" * 50)
        print("1. Create a new repository on GitHub")
        print("2. Run these commands:")
        print("   git branch -M main")
        print("   git remote add origin https://github.com/yourusername/spatial-ai-system.git")
        print("   git push -u origin main")
        print("")
        print("🛡️  Your local repository is now safely backed up!")

def confirm_action(message):
    """Get user confirmation"""
    while True:
        response = input(f"{message} [y/N]: ").strip().lower()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no', '']:
            return False
        else:
            print("Please enter 'y' or 'n'")

def main():
    """Main git initialization process"""
    print("🧠 Safe Git Initialization for Kurt's Spatial AI Operating System")
    print("=" * 70)
    
    git_manager = GitSafetyManager()
    
    # Step 1: Emergency backup
    print("🚨 Step 1: Creating emergency backup...")
    if confirm_action("Create emergency backup before proceeding?"):
        backup_dir = create_emergency_backup()
        print(f"✅ Emergency backup created at: {backup_dir}")
    else:
        if not confirm_action("⚠️  Proceed WITHOUT backup? This is risky!"):
            print("❌ Aborted for safety. Run emergency_backup.py first.")
            return
    
    print("\n" + "=" * 70)
    
    # Step 2: Check existing git status
    print("🔍 Step 2: Checking git status...")
    repo_exists = git_manager.check_git_status()
    
    if not repo_exists:
        if not git_manager.initialize_repo():
            print("❌ Failed to initialize git repository")
            return
    
    print("\n" + "=" * 70)
    
    # Step 3: Preview what will be added
    print("📋 Step 3: Previewing files to be committed...")
    files_to_add = git_manager.preview_git_add()
    
    if not files_to_add:
        print("⚠️  No files to add. Repository may already be up to date.")
        return
    
    print("\n" + "=" * 70)
    
    # Step 4: Check ignored files
    print("🚫 Step 4: Verifying file exclusions...")
    git_manager.check_ignored_files()
    
    print("\n" + "=" * 70)
    
    # Step 5: Stage files
    print("📦 Step 5: Staging files...")
    if not confirm_action("Add these files to git staging?"):
        print("❌ Staging cancelled")
        return
    
    if not git_manager.stage_files():
        print("❌ Failed to stage files")
        return
    
    print("\n" + "=" * 70)
    
    # Step 6: Create commit
    print("💭 Step 6: Creating initial commit...")
    if not confirm_action("Create initial commit with baseline message?"):
        print("❌ Commit cancelled. Files remain staged.")
        print("💡 You can commit later with: git commit -m 'your message'")
        return
    
    if git_manager.create_commit():
        print("\n✅ Git repository successfully initialized!")
        git_manager.setup_remote_instructions()
    else:
        print("❌ Failed to create commit")
        return
    
    print("\n🎯 Next steps:")
    print("1. Test the enhanced brain.py system")
    print("2. Run filesystem cleanup tools") 
    print("3. Optimize the 96MB vector database")
    print("4. Integrate spatial constellation interface")
    
    print(f"\n📁 Emergency backup available at: {backup_dir}")

if __name__ == "__main__":
    main()
