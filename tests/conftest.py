"""Make the vendored vedirect_x library importable without Home Assistant.

Importing it as `custom_components.vedirect.vedirect_x` would execute the
integration's __init__.py, which needs homeassistant installed. These tests
only exercise the protocol library.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "custom_components" / "vedirect"))
