# verify_setup.py — Run this to confirm everything is ready

import sys

libraries = [
    "pandas", "numpy", "yfinance", "matplotlib",
    "seaborn", "sklearn", "nltk", "openpyxl",
    "sqlalchemy", "pyodbc"
]

print(f"Python Version: {sys.version}\n")
print("Library Check:")
print("-" * 35)

all_good = True
for lib in libraries:
    try:
        __import__(lib)
        print(f"  ✅ {lib}")
    except ImportError:
        print(f"  ❌ {lib}  ← MISSING")
        all_good = False

print("-" * 35)
if all_good:
    print("\n🎉 All libraries installed! Ready for Stage 2.")
else:
    print("\n⚠️  Install missing libraries using: pip install <library-name>")