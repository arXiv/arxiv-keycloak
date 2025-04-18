"""Tests using mypy."""
import os
import shutil
import subprocess

def test_run_mypy_module() -> None:
    """Run mypy on all module sources."""
    mypy = shutil.which("mypy")
    if mypy is None:
        raise EnvironmentError("mypy not found in PATH")
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    result: int = subprocess.call([mypy, "-p", "arxiv_oauth2"],  env=os.environ, cwd=root_dir)
    assert result == 0, 'Expect 0 type errors when running mypy on browse'
