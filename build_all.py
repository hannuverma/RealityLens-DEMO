import PyInstaller.__main__
import sys
import time

sep = ';' if sys.platform.startswith('win') else ':'

shared_assets = [
    '--add-data', f'src/ui{sep}src/ui',
    '--add-data', f'assets{sep}assets',
    '--windowed',
    '--clean',
]

# .ico is Windows-only; use .icns on macOS, .png on Linux
if sys.platform.startswith('win'):
    shared_assets += ['--icon', 'icon.ico']
elif sys.platform == 'darwin':
    shared_assets += ['--icon', 'icon.icns']
# Linux: skip --icon, it's not supported in the same way

start = time.perf_counter()

# 1. Build the CLIENT-SIDE (Standalone) App
# PyInstaller.__main__.run([
#     'Double_model_ai/main.py',
#     '--name', 'RealityLens_Standalone',
#     '--onefile',
#     '--add-data', f'.env{sep}.',
#     '--collect-all', 'google.genai',
#     '--collect-all', 'tavily',
#     '--collect-all', 'groq',
#     *shared_assets
# ])

end = time.perf_counter()
with open('build_log.txt', 'w') as log_file:
    log_file.write(f"Build for standalone app took {end - start:.2f} seconds")

start = time.perf_counter()

# 2. Build the SERVER-CONNECTED (Cloud) App
PyInstaller.__main__.run([
    'server-connected-app/main.py',
    '--name', 'RealityLens_Cloud',
    '--onefile',
    *shared_assets
])

end = time.perf_counter()
with open('build_log.txt', 'a') as log_file:
    log_file.write(f"\nBuild for cloud-connected app took {end - start:.2f} seconds")