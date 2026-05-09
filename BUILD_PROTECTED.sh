#!/bin/bash

echo "-------------------------------------------------------"
echo "  CARDFLOW - PROTECTED PRODUCTION BUILD (PyArmor)"
echo "-------------------------------------------------------"

# 1. Clean previous builds
echo "[1/4] Cleaning old build files..."
rm -rf dist build

# 2. Obfuscate the source code
echo "[2/4] Obfuscating core logic..."
# We obfuscate core files only to stay within trial limits
pyarmor gen -O build/obfuscated python_prototype/game/engine.py python_prototype/game/ai_bot.py python_prototype/ui/database.py python_prototype/ui/progression_manager.py

# 3. Assemble Protected Source
echo "[3/4] Assembling protected source..."
mkdir -p build/protected_source/python_prototype
cp -r python_prototype/* build/protected_source/python_prototype/

# Swap in obfuscated files
cp build/obfuscated/engine.py build/protected_source/python_prototype/game/engine.py
cp build/obfuscated/ai_bot.py build/protected_source/python_prototype/game/ai_bot.py
cp build/obfuscated/database.py build/protected_source/python_prototype/ui/database.py
cp build/obfuscated/progression_manager.py build/protected_source/python_prototype/ui/progression_manager.py

# Place runtime at the base for global access
cp -r build/obfuscated/pyarmor_runtime_000000 build/protected_source/

# 4. Bundle into executable
echo "[4/4] Bundling into executable..."
pyinstaller --clean --noconfirm Cardflow_protected.spec

echo "-------------------------------------------------------"
echo "Build complete! Protected binary is in: dist/Cardflow.exe"
echo "-------------------------------------------------------"
