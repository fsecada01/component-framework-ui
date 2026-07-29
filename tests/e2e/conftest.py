import os
import subprocess
import sys
import threading
import time
from collections.abc import Generator
from pathlib import Path

import pytest
import uvicorn


def _run_fastapi_server(theme: str = "bulma", host: str = "127.0.0.1", port: int = 8771) -> None:
    from tests.integration.jinja_app.main import make_app

    config = uvicorn.Config(make_app(theme), host=host, port=port, log_level="error")
    server = uvicorn.Server(config)
    server.run()


def _start_cotton_server(port: int, theme: str) -> subprocess.Popen:
    """Start the Django cotton E2E server as a subprocess.

    A separate process so it gets its own Django configuration including
    django_cotton, without contaminating the pytest process's settings (which
    unit and integration tests rely on). The theme arrives via the environment
    because Django settings are read once at startup.
    """
    server_script = Path(__file__).parent / "_django_e2e_server.py"
    env = {**os.environ, "CF_UI_E2E_THEME": theme}
    return subprocess.Popen(
        [sys.executable, str(server_script), "127.0.0.1", str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env,
    )


@pytest.fixture(scope="session")
def jinja_server_url() -> Generator[str, None, None]:
    thread = threading.Thread(target=_run_fastapi_server, args=("bulma", "127.0.0.1", 8771))
    thread.daemon = True
    thread.start()
    time.sleep(2.0)
    yield "http://127.0.0.1:8771"


@pytest.fixture(scope="session")
def cotton_server_url() -> Generator[str, None, None]:
    proc = _start_cotton_server(8772, "bulma")
    time.sleep(2.0)
    yield "http://127.0.0.1:8772"
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def daisy_jinja_server_url() -> Generator[str, None, None]:
    thread = threading.Thread(target=_run_fastapi_server, args=("daisy", "127.0.0.1", 8773))
    thread.daemon = True
    thread.start()
    time.sleep(2.0)
    yield "http://127.0.0.1:8773"


@pytest.fixture(scope="session")
def daisy_cotton_server_url() -> Generator[str, None, None]:
    """The same consumer templates as the Bulma server, CF_UI_THEME="daisy".

    Nothing else differs — that is the claim this tier exists to check.
    """
    proc = _start_cotton_server(8774, "daisy")
    time.sleep(2.0)
    yield "http://127.0.0.1:8774"
    proc.terminate()
    proc.wait(timeout=5)


@pytest.fixture(scope="session")
def fomantic_jinja_server_url() -> Generator[str, None, None]:
    thread = threading.Thread(target=_run_fastapi_server, args=("fomantic", "127.0.0.1", 8779))
    thread.daemon = True
    thread.start()
    time.sleep(2.0)
    yield "http://127.0.0.1:8779"


@pytest.fixture(scope="session")
def fomantic_cotton_server_url() -> Generator[str, None, None]:
    """The same consumer templates again, ``CF_UI_THEME="fomantic"``."""
    proc = _start_cotton_server(8780, "fomantic")
    time.sleep(2.0)
    yield "http://127.0.0.1:8780"
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


@pytest.fixture(params=["js_on", "js_off"])
def daisy_jinja_page(request, browser, daisy_jinja_server_url):
    ctx = browser.new_context(java_script_enabled=(request.param == "js_on"))
    page = ctx.new_page()
    page.set_default_timeout(5000)
    yield page, request.param
    ctx.close()


@pytest.fixture(params=["js_on", "js_off"])
def daisy_cotton_page(request, browser, daisy_cotton_server_url):
    ctx = browser.new_context(java_script_enabled=(request.param == "js_on"))
    page = ctx.new_page()
    page.set_default_timeout(5000)
    yield page, request.param
    ctx.close()


@pytest.fixture(params=["js_on", "js_off"])
def fomantic_jinja_page(request, browser, fomantic_jinja_server_url):
    ctx = browser.new_context(java_script_enabled=(request.param == "js_on"))
    page = ctx.new_page()
    page.set_default_timeout(5000)
    yield page, request.param
    ctx.close()


@pytest.fixture(params=["js_on", "js_off"])
def fomantic_cotton_page(request, browser, fomantic_cotton_server_url):
    ctx = browser.new_context(java_script_enabled=(request.param == "js_on"))
    page = ctx.new_page()
    page.set_default_timeout(5000)
    yield page, request.param
    ctx.close()
