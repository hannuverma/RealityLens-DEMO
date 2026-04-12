import PyInstaller.__main__

# Shared assets (UI and Icons)
shared_assets = [
    '--add-data', 'src/ui;src/ui',
    '--add-data', 'assets;assets',
    '--icon', 'icon.ico',
    '--windowed',
    '--clean',
    '--collect-all', 'PyQt6',
]

# 1. Build the CLIENT-SIDE (Standalone) App
# This one NEEDS the .env file for direct API access
PyInstaller.__main__.run([
    'Double_model_ai/main.py', 
    '--name', 'RealityLens_Standalone',
    '--onefile',
    '--add-data', '.env;.',  # Bundling the keys here
    '--collect-all', 'google.genai',
    '--collect-all', 'tavily',
    '--collect-all', 'groq',
    *shared_assets
])

# 2. Build the SERVER-CONNECTED (Cloud) App
# This one DOES NOT get the .env file
PyInstaller.__main__.run([
    'server-connected-app/main.py',
    '--name', 'RealityLens_Cloud',
    '--onefile',
    # No .env added here - keeps your keys safe!
    *shared_assets
])