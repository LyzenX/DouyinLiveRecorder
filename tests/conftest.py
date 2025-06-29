"""Shared pytest fixtures and configuration."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = Mock()
    config.get_config = Mock(return_value={
        "path": "/tmp/test_videos",
        "create_time_file": False,
        "live_status": 1,
        "use_chrome": False,
        "recording_time_list": [],
        "upload_bilibili": False,
        "bilibili_cookie": None,
        "delete_after_upload": False,
        "before_download_sec": 0,
        "process_m3u8": False,
        "remove_temp_file": True,
        "num_processes": 3,
        "ffmpeg_path": "ffmpeg",
        "max_download_size": 3,
        "max_download_time": 7200,
        "ts_timeout": 5,
        "log_level": "INFO",
    })
    return config


@pytest.fixture
def mock_room_info():
    """Create a mock room info object."""
    room_info = Mock()
    room_info.room_id = "12345"
    room_info.room_title = "Test Room"
    room_info.nickname = "Test User"
    room_info.status = 1
    room_info.web_room_id = "67890"
    return room_info


@pytest.fixture
def mock_api_response():
    """Create a mock API response."""
    return {
        "status_code": 0,
        "data": {
            "room": {
                "id": "12345",
                "title": "Test Room",
                "status": 1,
                "user": {
                    "nickname": "Test User",
                    "id": "67890"
                }
            }
        }
    }


@pytest.fixture
def mock_websocket():
    """Create a mock websocket connection."""
    ws = Mock()
    ws.recv = Mock(return_value=b"test_data")
    ws.send = Mock()
    ws.close = Mock()
    return ws


@pytest.fixture
def test_data_dir(temp_dir):
    """Create a test data directory with sample files."""
    data_dir = temp_dir / "test_data"
    data_dir.mkdir(exist_ok=True)
    
    # Create sample test files
    (data_dir / "test_video.flv").write_text("fake video content")
    (data_dir / "test_config.json").write_text('{"test": true}')
    
    return data_dir


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_ffmpeg():
    """Create a mock FFmpeg process."""
    process = Mock()
    process.poll = Mock(return_value=None)
    process.wait = Mock(return_value=0)
    process.communicate = Mock(return_value=(b"", b""))
    process.returncode = 0
    return process