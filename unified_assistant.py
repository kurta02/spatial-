#!/usr/bin/env python3
"""
Kurt's Unified AI Assistant - Voice-to-Voice with Project Context
FIXED VERSION - Corrected LLaMA query and TTS
"""

import os
import subprocess
import tempfile
import time
import re
import webrtcvad
import collections
import sounddevice as sd
import soundfile as sf
import numpy as np
from datetime import datetime
from pathlib import Path

class UnifiedAssistant:
    def __init__(self):
        # Paths from your existing setup - VERIFIED WORKING
        self.whisper_path = "/home/kurt/whisper.cpp/build/bin/whisper-cli"
        self.whisper_model = "/home/kurt/whisper.cpp/models/ggml-base.en.bin"
        self.llama_path = "/home/kurt/llama.cpp/build/bin/llama-cli"
        self.llama_model = "/home/kurt/llama.cpp/models/mistral-7b-instruct.Q4_K_M.gguf"
        
        # Project management
        self.project_file = Path.home() / ".last_assistant_project"
        self.projects_dir = Path.home() / "Documents/KurtVault/projects"
        self.vault_path = Path.home() / "Documents/KurtVault"
        
        # Audio settings
        self.sample_rate = 16000
        self.frame_duration = 30
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        self.num_padding_frames = 35
        
        # Context management
        self.current_project = self.load_current_project()
        
        print(f"🤖 Kurt's Unified Assistant Ready!")
        print(f"📁 Current project: {self.current_project}")

    def load_current_project(self):
        """Load the last used project or prompt for selection"""
        if self.project_file.exists():
            project = self.project_file.read_text().strip()
            print(f"📁 Continuing with project: {project}")
            return project
        else:
            return self.select_project()

    def select_project(self):
        """Interactive project selection"""
        if not self.projects_dir.exists():
            print(f"⚠️ Projects directory not found: {self.projects_dir}")
            print("Creating default project...")
            self.projects_dir.mkdir(parents=True, exist_ok=True)
            default_project = "esp32_main"
            (self.projects_dir / default_project).mkdir(exist_ok=True)
            self.project_file.write_text(default_project)
            return default_project
            
        projects = [p.name for p in self.projects_dir.iterdir() if p.is_dir()]
        if not projects:
            print("No projects found. Creating default project...")
            default_project = "esp32_main"
            (self.projects_dir / default_project).mkdir(exist_ok=True)
            self.project_file.write_text(default_project)
            return default_project
            
        print("\n📁 Available projects:")
        for i, project in enumerate(projects, 1):
            print(f"  {i}. {project}")
        
        while True:
            try:
                choice = int(input("Select project number: ")) - 1
                if 0 <= choice < len(projects):
                    project = projects[choice]
                    self.project_file.write_text(project)
                    return project
            except (ValueError, IndexError):
                print("Invalid selection. Try again.")

    def record_audio_vad(self):
        """Voice Activity Detection recording with manual stop"""
        print("🎤 Listening...")
        print("   - Speak naturally, pause to auto-stop")
        print("   - Or press Ctrl+C once to stop manually (great for noisy cars!)")
        
        vad = webrtcvad.Vad(1)
        ring_buffer = collections.deque(maxlen=self.num_padding_frames)
        triggered = False
        voiced_frames = []
        
        stream = sd.InputStream(
            samplerate=self.sample_rate, 
            channels=1, 
            dtype='int16', 
            blocksize=self.frame_size
        )
        stream.start()

        try:
            while True:
                audio, _ = stream.read(self.frame_size)
                is_speech = vad.is_speech(audio.tobytes(), self.sample_rate)
                if not triggered:
                    ring_buffer.append((audio.copy(), is_speech))
                    num_voiced = len([f for f, speech in ring_buffer if speech])
                    if num_voiced > 0.7 * ring_buffer.maxlen:
                        triggered = True
                        print("🔴 Recording started...")
                        for f, _ in ring_buffer:
                            voiced_frames.append(f)
                        ring_buffer.clear()
                else:
                    voiced_frames.append(audio.copy())
                    ring_buffer.append((audio.copy(), is_speech))
                    num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                    if num_unvoiced > 0.7 * ring_buffer.maxlen:
                        print("⏸️ Auto-stop (silence detected)")
                        break
        except KeyboardInterrupt:
            print("⏹️ Manual stop (Ctrl+C)")
        finally:
            stream.stop()

        if not voiced_frames:
            print("⚠️ No audio recorded")
            return None
            
        audio_array = np.concatenate(voiced_frames, axis=0)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        sf.write(tmp_path, audio_array, self.sample_rate)
        print("✅ Recording complete")
        return tmp_path

    def transcribe_audio(self, audio_path):
        """Transcribe using Whisper - FIXED to be less picky"""
        print("🔄 Transcribing audio...")
        try:
            result = subprocess.run([
                self.whisper_path,
                "-m", self.whisper_model,
                "-f", audio_path,
                "--no-timestamps"
            ], capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            print("❌ Whisper timed out. Skipping.")
            return ""

        output_text = result.stdout.strip()
        if output_text:
            cleaned = re.sub(r'\[\d+:\d+\.\d+ --> \d+:\d+\.\d+\]', '', output_text)
            cleaned = re.sub(r'\[\d+\.\d+s --> \d+\.\d+s\]', '', cleaned)
            cleaned = cleaned.strip()
            
            if len(cleaned) >= 2:
                print(f"🎯 Transcribed: '{cleaned}'")
                return cleaned
        
        print("⚠️ No clear speech detected")
        return ""

    def get_project_context(self):
        """Get context about current project"""
        project_path = self.projects_dir / self.current_project
        context = f"You are helping with project: {self.current_project}\n"
        
        if project_path.exists():
            recent_files = []
            for file in project_path.glob("*.md"):
                if file.stat().st_mtime > time.time() - (7 * 24 * 3600):
                    recent_files.append(file.name)
            if recent_files:
                context += f"Recent files: {', '.join(recent_files[:3])}\n"
        
        return context

    def query_ai_with_context(self, prompt):
        """Enhanced AI query with project awareness - FIXED"""
        print(f"🧠 Processing: {prompt}")
        
        project_context = self.get_project_context()
        
        system_prompt = f"""You are a helpful AI assistant working on Kurt's {self.current_project} project. 
{project_context}
Please provide helpful, concise responses about ESP32 development, sensors, coding, or project management.

User question: {prompt}

Please respond helpfully and concisely:"""

        return self.query_llama(system_prompt)

    def query_llama(self, prompt):
        """Query local LLaMA - FIXED to get proper responses"""
        print("🔄 Querying LLaMA...")
        
        try:
            result = subprocess.run([
                self.llama_path,
                "-m", self.llama_model,
                "-p", prompt,
                "-n", "200",
                "--temp", "0.7",
                "--no-display-prompt",
                "-no-cnv"
            ], capture_output=True, text=True, timeout=45)
            
            if result.returncode != 0:
                print(f"⚠️ LLaMA error: {result.stderr}")
                return "I had trouble processing that. Could you try rephrasing?"
            
            response = result.stdout.strip()
            
            lines = response.split('\n')
            clean_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('[INST]') and not line.startswith('User:'):
                    clean_lines.append(line)
            
            response = ' '.join(clean_lines).strip()
            
            if len(response) < 10:
                return "I'm not sure about that. Could you be more specific?"
            
            return response
            
        except subprocess.TimeoutExpired:
            print("❌ LLaMA timed out.")
            return "Sorry, I took too long to think about that. Can you try again?"
        except Exception as e:
            print(f"❌ LLaMA error: {e}")
            return "I had a technical issue. Could you repeat that?"

    def save_to_project(self, question, response):
        """Save conversation to project files"""
        project_path = self.projects_dir / self.current_project
        project_path.mkdir(parents=True, exist_ok=True)
        
        log_file = project_path / "assistantlog.md"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"""
## {timestamp}
**Question:** {question}
**Response:** {response}

"""
        with open(log_file, "a") as f:
            f.write(log_entry)
        print(f"💾 Saved to {log_file}")

    def speak_response(self, text):
        """Text-to-speech using system TTS"""
        if not text.strip():
            return
        
        print("🔊 Speaking response...")
        
        try:
            subprocess.run([
                "espeak", 
                "-s", "160",
                "-p", "50",
                text
            ], check=True, capture_output=True)
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        try:
            subprocess.run(["spd-say", text], check=True, capture_output=True)
            return
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        print(f"🔇 TTS not available, text only:")
        print(f"📝 {text}")

    def run_voice_loop(self):
        """Main voice interaction loop"""
        print("\n🤖 Voice Assistant Ready!")
        print("💡 Perfect for cars and noisy environments!")
        print("🎤 Say 'change project', 'quit', or ask about your ESP32 work")
        
        try:
            while True:
                print("\n--- Ready to listen ---")
                
                audio_path = self.record_audio_vad()
                if audio_path is None:
                    continue
                    
                prompt = self.transcribe_audio(audio_path)
                if not prompt:
                    print("⚠️ Try speaking more clearly or closer to mic")
                    os.unlink(audio_path)
                    continue
                
                print(f"📝 You said: '{prompt}'")
                
                if "change project" in prompt.lower():
                    self.current_project = self.select_project()
                    response = f"Switched to project {self.current_project}"
                    print(f"🤖 {response}")
                    self.speak_response(response)
                    os.unlink(audio_path)
                    continue
                
                if any(word in prompt.lower() for word in ["quit", "exit", "goodbye", "stop"]):
                    response = "Goodbye! Happy coding!"
                    print(f"🤖 {response}")
                    self.speak_response(response)
                    os.unlink(audio_path)
                    break
                
                response = self.query_ai_with_context(prompt)
                print(f"🤖 Response: {response}")
                
                self.save_to_project(prompt, response)
                self.speak_response(response)
                
                os.unlink(audio_path)
                
        except KeyboardInterrupt:
            print("\n👋 Assistant stopped.")

def main():
    print("🚀 Starting Kurt's Voice AI Assistant...")
    assistant = UnifiedAssistant()
    assistant.run_voice_loop()

if __name__ == "__main__":
    main()
