"""Test config: make `src/` importable without installing the package."""
import sys
from pathlib import Path

# Add the src/ directory to sys.path so tests can `import issuemosaic`
# whether the package is installed in editable mode or not.
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
