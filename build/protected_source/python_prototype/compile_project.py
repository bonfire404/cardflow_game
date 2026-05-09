import os
import sys
from setuptools import setup
from Cython.Build import cythonize

# We will compile the core UI and Path files to protect the main logic
files = [
    "ui/paths.py",
    # We keep main.py as a wrapper or compile it too? 
    # Usually main entry is better as a small wrapper if we compile everything else.
]

try:
    setup(
        name='Cardflow Protected',
        ext_modules=cythonize(files, language_level="3"),
        script_args=['build_ext', '--inplace']
    )
    print("Compilation successful!")
except Exception as e:
    print(f"Compilation failed: {e}")
    sys.exit(1)
