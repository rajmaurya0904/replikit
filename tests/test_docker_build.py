import shutil
import subprocess
import pytest

@pytest.mark.skipif(shutil.which("docker") is None, reason="Docker not installed")
def test_docker_build():
    """Test that the Docker image builds successfully."""
    result = subprocess.run(
        ["docker", "build", "-t", "replikit-test", "."],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Docker build failed: {result.stderr}"
