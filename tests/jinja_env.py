"""One Jinja ``Environment`` builder for the whole suite (#36).

The environment **deliberately declines to escape**. cf-ui's templates carry
their own ``{% autoescape true %}`` blocks, so any escaping a test observes
through this environment can only have come from the template itself — which
is exactly the guarantee #36 ships. A harness that autoescaped would mask a
template that lost its block.

History, because the wrong versions of this file looked right: each tier once
built its own environment with ``autoescape=select_autoescape([...])``. That
call keys off the file *extension*, and cf-ui's templates are ``.jinja`` — so
fixtures listing only ``["html"]`` resolved to ``False`` and quietly tested
nothing about escaping, while reading exactly like fixtures that did. An
interim version derived the setting from what ``install_cf_ui`` left on a
catalog, which was better but still made escaping a property of the harness
configuration. Now it is a property of the files under test, and this module
is one line of policy: the suite renders cf-ui templates the unfriendliest way
a consumer can.
"""

from __future__ import annotations

from os import PathLike

from jinja2 import Environment, FileSystemLoader, StrictUndefined


def make_env(directory: str | PathLike[str]) -> Environment:
    """A ``FileSystemLoader`` environment with autoescape off, on purpose."""
    return Environment(
        loader=FileSystemLoader(directory),
        autoescape=False,
        undefined=StrictUndefined,
    )
