# Root test configuration.
# Synthetic fixture conventions:
#   - All fixtures are deterministic and never read private/gold data.
#   - Synthetic workbooks and documents live under tests/fixtures/ (versionable).
#   - Real gold (02-DOCS/data/SUBSET_GOLD.xlsx) must never appear in any test path.
import sys
from pathlib import Path

# Add the tests/ directory to sys.path so that test-only helpers (e.g.
# tests/fakes.py) are importable from any subdirectory without making tests/
# a package (which would change pytest's import mode for existing test files).
_TESTS_ROOT = Path(__file__).parent
if str(_TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TESTS_ROOT))
