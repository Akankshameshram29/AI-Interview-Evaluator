import pytest
from fastapi import HTTPException
from backend.routes.practice import validate_audio_file_size


def test_valid_file_size_passes():
    validate_audio_file_size(10)  # should not raise


def test_oversized_file_raises_400():
    with pytest.raises(HTTPException) as exc_info:
        validate_audio_file_size(60)
    assert exc_info.value.status_code == 400