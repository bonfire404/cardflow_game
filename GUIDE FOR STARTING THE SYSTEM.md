# Manual to Start The App

cd python_prototype

python -m ui.main
# Update Exe command
python -m PyInstaller --noconfirm MamasGo.spec

# Update Exe command (clear cache)
rm -rf build dist && python -m PyInstaller MamasGo.spec
