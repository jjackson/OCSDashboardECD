#!/usr/bin/env python3
"""
Setup script for OCS Dashboard
Creates virtual environment and installs dependencies
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        # Use list form to avoid shell escaping issues with spaces
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False

def main():
    """Setup virtual environment and dependencies"""
    print("🚀 OCS Dashboard Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return 1
    
    print(f"✅ Python {sys.version}")
    
    # Determine venv activation script
    is_windows = platform.system() == "Windows"
    venv_dir = Path("venv")
    
    if is_windows:
        activate_script = venv_dir / "Scripts" / "activate.bat"
        pip_cmd = str(venv_dir / "Scripts" / "pip")
        python_cmd = str(venv_dir / "Scripts" / "python")
    else:
        activate_script = venv_dir / "bin" / "activate"
        pip_cmd = str(venv_dir / "bin" / "pip")
        python_cmd = str(venv_dir / "bin" / "python")
    
    # Create virtual environment
    if not venv_dir.exists():
        # Use list form to handle spaces in paths
        venv_cmd = [sys.executable, "-m", "venv", "venv"]
        if not run_command(venv_cmd, "Creating virtual environment"):
            return 1
    else:
        print("✅ Virtual environment already exists")
    
    # Upgrade pip
    pip_upgrade_cmd = [pip_cmd, "install", "--upgrade", "pip"]
    if not run_command(pip_upgrade_cmd, "Upgrading pip"):
        return 1
    
    # Install dependencies
    deps_cmd = [pip_cmd, "install", "-r", "requirements.txt"]
    if not run_command(deps_cmd, "Installing dependencies"):
        return 1
    
    # Create .env template if it doesn't exist
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 Creating .env file from template...")
            env_file.write_text(env_example.read_text())
            print("✅ .env file created - please edit it with your API key")
        else:
            print("📝 Creating .env template...")
            env_content = """# OpenChatStudio API Configuration
OCS_API_KEY=your_api_key_here
OCS_API_BASE_URL=https://chatbots.dimagi.com/api
"""
            env_file.write_text(env_content)
            print("✅ .env template created - please edit it with your API key")
    else:
        print("✅ .env file already exists")
    
    # Create data directories
    for dir_name in ["data", "data/sessions", "output"]:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Data directories created")
    
    print("\n🎉 Setup complete!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your OpenChatStudio API key")
    print("2. Activate virtual environment:")
    if is_windows:
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("3. Download data:")
    print("   python run_dashboard.py download")
    print("4. Generate dashboard:")
    print("   python run_dashboard.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
