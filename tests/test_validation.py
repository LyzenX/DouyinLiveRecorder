"""Validation tests to ensure the testing infrastructure works correctly."""

import sys
from pathlib import Path

import pytest


class TestInfrastructureValidation:
    """Test class to validate the testing infrastructure setup."""

    def test_pytest_installed(self):
        """Verify pytest is properly installed."""
        assert "pytest" in sys.modules

    def test_pytest_cov_installed(self):
        """Verify pytest-cov is properly installed."""
        import pytest_cov
        assert pytest_cov is not None

    def test_pytest_mock_installed(self):
        """Verify pytest-mock is properly installed."""
        import pytest_mock
        assert pytest_mock is not None

    def test_project_structure(self):
        """Verify the project structure is set up correctly."""
        project_root = Path(__file__).parent.parent
        
        # Check main directories exist
        assert project_root.exists()
        assert (project_root / "dylr").exists()
        assert (project_root / "tests").exists()
        assert (project_root / "tests" / "unit").exists()
        assert (project_root / "tests" / "integration").exists()

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists and is properly configured."""
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"
        
        assert pyproject_path.exists()
        
        # Check content includes required sections
        content = pyproject_path.read_text()
        assert "[tool.poetry]" in content
        assert "[tool.pytest.ini_options]" in content
        assert "[tool.coverage.run]" in content

    @pytest.mark.unit
    def test_unit_marker(self):
        """Test that the unit marker works correctly."""
        assert True

    @pytest.mark.integration
    def test_integration_marker(self):
        """Test that the integration marker works correctly."""
        assert True

    @pytest.mark.slow
    def test_slow_marker(self):
        """Test that the slow marker works correctly."""
        assert True

    def test_fixtures_available(self, temp_dir, mock_config, mock_room_info):
        """Test that common fixtures are available and working."""
        # Test temp_dir fixture
        assert temp_dir.exists()
        assert temp_dir.is_dir()
        
        # Test mock_config fixture
        config = mock_config.get_config()
        assert isinstance(config, dict)
        assert "path" in config
        
        # Test mock_room_info fixture
        assert mock_room_info.room_id == "12345"
        assert mock_room_info.room_title == "Test Room"

    def test_coverage_configuration(self):
        """Verify coverage is properly configured."""
        try:
            import coverage
            assert coverage is not None
        except ImportError:
            pytest.fail("Coverage module not installed")

    def test_dylr_module_importable(self):
        """Verify the dylr module can be imported."""
        try:
            import dylr
            assert dylr is not None
        except ImportError:
            pytest.fail("Cannot import dylr module")