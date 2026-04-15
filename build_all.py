import PyInstaller.__main__
import sys

# Detect separator based on OS (';' for Windows, ':' for Linux)
sep = ';' if sys.platform.startswith('win') else ':'

# Shared assets (UI and Icons)
shared_assets = [
    '--add-data', f'src/ui{sep}src/ui',
    '--add-data', f'assets{sep}assets',
    '--icon', 'icon.ico',
    '--windowed',
    '--clean',
    '--collect-all', 'PyQt6',
]

# 1. Build the CLIENT-SIDE (Standalone) App
PyInstaller.__main__.run([
    'Double_model_ai/main.py', 
    '--name', 'RealityLens_Standalone',
    '--onefile',
    '--add-data', f'.env{sep}.',  # Corrected separator
    '--collect-all', 'google.genai',
    '--collect-all', 'tavily',
    '--collect-all', 'groq',
    *shared_assets
])

# 2. Build the SERVER-CONNECTED (Cloud) App
PyInstaller.__main__.run([
    'server-connected-app/main.py',
    '--name', 'RealityLens_Cloud',
    '--onefile',
    *shared_assets
])