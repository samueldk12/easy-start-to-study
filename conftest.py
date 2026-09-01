"""
Pytest root conftest.

Redirects StackStudio's registry/cache/state persistence and scaffolded project
output to a scratch directory before any `studio.*` module is imported, so the
test suite never reads or mutates the real projects/.registry.json,
projects/projects_cache.json, projects/.state_history.json, or the user's actual
projects/ folder. Must set the env var at module import time (not inside a
fixture) because those modules compute their file paths once at import time.
"""

import os
import tempfile

_TEST_PROJECTS_DIR = tempfile.mkdtemp(prefix="stackstudio-test-projects-")
os.environ.setdefault("STACKSTUDIO_PROJECTS_DIR", _TEST_PROJECTS_DIR)
