from pathlib import Path

from cf_ui._version import __version__

_HERE = Path(__file__).parent

JINJA_TEMPLATES_DIR = _HERE / "templates" / "jinja"
COTTON_TEMPLATES_DIR = _HERE / "templates" / "cotton"

__all__ = ["JINJA_TEMPLATES_DIR", "COTTON_TEMPLATES_DIR", "__version__"]
