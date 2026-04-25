"""
Standalone Django WSGI server for E2E tests.

Run as a subprocess so it gets its own Python process and Django configuration,
isolated from the pytest process's Django settings.
"""
import os
import sys
from pathlib import Path

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8772

# Ensure project root and src/ are on the path so imports work.
_here = Path(__file__).parent
_project_root = _here.parent.parent
_src = _project_root / "src"
for _p in [str(_project_root), str(_src)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Configure Django with cotton-enabled settings
os.environ["DJANGO_SETTINGS_MODULE"] = "tests.e2e._e2e_django_settings"

import django

django.setup()

from django.core.handlers.wsgi import WSGIHandler
from wsgiref.simple_server import make_server

httpd = make_server(HOST, PORT, WSGIHandler())
httpd.serve_forever()
