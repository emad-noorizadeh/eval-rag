# Copyright 2025 Emad Noorizadeh
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env python3
"""
Environment Setup Script
Author: Emad Noorizadeh

Sets up a virtual environment and installs all requirements for the RAG Frontend project.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description, cwd=None):
    """Run a command and handle errors gracefully."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            cwd=cwd,
            capture_output=True, 
            text=True
        )
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"   Error: {e.stderr.strip()}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported")
        print("   Please use Python 3.8 or higher")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def create_virtual_environment(venv_path):
    """Create a virtual environment."""
    print(f"📦 Creating virtual environment at {venv_path}")
    
    # Remove existing venv if it exists
    if os.path.exists(venv_path):
        print("   Removing existing virtual environment...")
        import shutil
        shutil.rmtree(venv_path)
    
    # Create new virtual environment
    if not run_command(f"python -m venv {venv_path}", "Creating virtual environment"):
        return False
    
    return True

def get_activation_script(venv_path):
    """Get the correct activation script path based on OS."""
    if platform.system() == "Windows":
        return os.path.join(venv_path, "Scripts", "activate")
    else:
        return os.path.join(venv_path, "bin", "activate")

def get_pip_path(venv_path):
    """Get the correct pip path based on OS."""
    if platform.system() == "Windows":
        return os.path.join(venv_path, "Scripts", "pip")
    else:
        return os.path.join(venv_path, "bin", "pip")

def install_requirements(venv_path, requirements_path):
    """Install requirements in the virtual environment."""
    pip_path = get_pip_path(venv_path)
    
    # Upgrade pip first
    if not run_command(f"{pip_path} install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install requirements
    if not run_command(f"{pip_path} install -r {requirements_path}", "Installing requirements"):
        return False
    
    return True

def install_spacy_model(venv_path, wheels_dir):
    """Install spaCy model from wheels directory."""
    pip_path = get_pip_path(venv_path)
    wheel_file = os.path.join(wheels_dir, "en_core_web_sm-3.8.0-py3-none-any.whl")
    
    if os.path.exists(wheel_file):
        if not run_command(f"{pip_path} install {wheel_file}", "Installing spaCy model"):
            return False
    else:
        print(f"⚠️  spaCy model wheel not found at {wheel_file}")
        print("   You may need to install it manually later")
    
    return True

def create_activation_scripts(venv_path, project_root):
    """Create convenient activation scripts."""
    activation_script = get_activation_script(venv_path)
    
    # Create activation script for Unix/Mac
    if platform.system() != "Windows":
        script_content = f"""#!/bin/bash
# RAG Frontend Environment Activation Script
# Author: Emad Noorizadeh

echo "🚀 Activating RAG Frontend environment..."
source {activation_script}
echo "✅ Environment activated!"
echo "📁 Project root: {project_root}"
echo "🐍 Python: $(which python)"
echo "📦 Pip: $(which pip)"
echo ""
echo "To start the backend:"
echo "  cd {project_root}/backend"
echo "  python main.py"
echo ""
echo "To start the frontend:"
echo "  cd {project_root}/frontend"
echo "  npm run dev"
"""
        script_path = os.path.join(project_root, "activate_env.sh")
        with open(script_path, "w") as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        print(f"✅ Created activation script: {script_path}")
    
    # Create activation script for Windows
    script_content = f"""@echo off
REM RAG Frontend Environment Activation Script
REM Author: Emad Noorizadeh

echo 🚀 Activating RAG Frontend environment...
call {activation_script}
echo ✅ Environment activated!
echo 📁 Project root: {project_root}
echo 🐍 Python: %VIRTUAL_ENV%\\Scripts\\python.exe
echo 📦 Pip: %VIRTUAL_ENV%\\Scripts\\pip.exe
echo.
echo To start the backend:
echo   cd {project_root}\\backend
echo   python main.py
echo.
echo To start the frontend:
echo   cd {project_root}\\frontend
echo   npm run dev
"""
    script_path = os.path.join(project_root, "activate_env.bat")
    with open(script_path, "w") as f:
        f.write(script_content)
    print(f"✅ Created activation script: {script_path}")

def main():
    """Main setup function."""
    print("=" * 60)
    print("🚀 RAG Frontend Environment Setup")
    print("=" * 60)
    
    # Get project paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)  # Go up from backend/setup to backend
    project_root = os.path.dirname(project_root)  # Go up from backend to project root
    backend_dir = os.path.join(project_root, "backend")
    venv_path = os.path.join(project_root, "venv")
    requirements_path = os.path.join(backend_dir, "requirements.txt")
    wheels_dir = os.path.join(backend_dir, "wheels")
    
    print(f"📁 Project root: {project_root}")
    print(f"📁 Backend directory: {backend_dir}")
    print(f"📁 Virtual environment: {venv_path}")
    print(f"📁 Requirements: {requirements_path}")
    print(f"📁 Wheels directory: {wheels_dir}")
    print()
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Check if requirements.txt exists
    if not os.path.exists(requirements_path):
        print(f"❌ Requirements file not found: {requirements_path}")
        return False
    
    # Create virtual environment
    if not create_virtual_environment(venv_path):
        return False
    
    # Install requirements
    if not install_requirements(venv_path, requirements_path):
        return False
    
    # Install spaCy model
    if not install_spacy_model(venv_path, wheels_dir):
        return False
    
    # Create activation scripts
    create_activation_scripts(venv_path, project_root)
    
    print("\n" + "=" * 60)
    print("🎉 Environment setup completed successfully!")
    print("=" * 60)
    print()
    print("📋 Next steps:")
    print("1. Activate the environment:")
    if platform.system() == "Windows":
        print("   activate_env.bat")
    else:
        print("   source activate_env.sh")
    print()
    print("2. Start the backend:")
    print("   cd backend")
    print("   python main.py")
    print()
    print("3. Start the frontend (in another terminal):")
    print("   cd frontend")
    print("   npm run dev")
    print()
    print("4. Download models (optional):")
    print("   cd backend/setup")
    print("   python minilm_loader.py")
    print()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
