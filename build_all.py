import PyInstaller.__main__
import sys
import time

sep = ':'  # macOS always uses ':'

shared_assets = [
    '--add-data', f'src/ui{sep}src/ui',
    '--add-data', f'assets{sep}assets',
    '--windowed',
    '--clean',
    '--icon', 'icon.icns',
    # macOS: AppKit, objc, Quartz needed for tray, hotkeys, screen recording
    '--collect-all', 'objc',
    '--collect-all', 'AppKit',
    '--collect-all', 'Quartz',
]

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
    # macOS entitlements for screen recording + accessibility
    '--osx-entitlements-file', 'entitlements.plist',
    *shared_assets
])

end = time.perf_counter()
with open('build_log.txt', 'a') as log_file:
    log_file.write(f"\nBuild for cloud-connected app took {end - start:.2f} seconds")

# Remind to code-sign after build
print("\n✅ Build complete.")
print("👉 Run this to sign the app (required for permissions to persist):")
print("   codesign --force --deep --sign - dist/RealityLens_Cloud")