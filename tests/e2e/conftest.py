import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Generator

import pytest
import uvicorn


def _run_fastapi_server(host: str = "127.0.0.1", port: int = 8771) -> None:
    from tests.integration.jinja_app.main import app

    config = uvicorn.Config(app, host=host, port=port, log_level="error")
    server = uvicorn.Server(config)
    server.run()


@pytest.fixture(scope="session")
def jinja_server_url() -> Generator[str, None, None]:
    thread = threading.Thread(target=_run_fastapi_server, daemon=True)
    thread.start()
    time.sleep(2.0)
    yield "http://127.0.0.1:8771"


@pytest.fixture(scope="session")
def cotton_server_url() -> Generator[str, None, None]:
    """
    Start the Django cotton E2E server as a subprocess so it has its own
    Python process with isolated Django settings that include django_cotton.
    This prevents contaminating the main pytest process's Django configuration
    (which unit and integration tests rely on).
    """
    server_script = Path(__file__).parent / "_django_e2e_server.py"
    proc = subprocess.Popen(
        [sys.executable, str(server_script), "127.0.0.1", "8772"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(2.0)
    yield "http://127.0.0.1:8772"
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(params=["js_on", "js_off"])
def jinja_page(request, browser, jinja_server_url):
    ctx = browser.new_context(java_script_enabled=(request.param == "js_on"))
    page = ctx.new_page()
    page.set_default_timeout(5000)
    yield page, request.param
    ctx.close()


@pytest.fixture(params=["js_on", "js_off"])
def cotton_page(request, browser, cotton_server_url):
    ctx = browser.new_context(java_script_enabled=(request.param == "js_on"))
    page = ctx.new_page()
    page.set_default_timeout(5000)
    yield page, request.param
    ctx.close()
