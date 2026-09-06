import pytest

from app.fetcher import FetchError, normalize_url, validate_public_url


def test_normalize_url_adds_https_and_removes_fragment():
    assert normalize_url("example.org/a?q=1#fragment") == "https://example.org/a?q=1"


def test_normalize_url_rejects_credentials():
    with pytest.raises(FetchError, match="credentials"):
        normalize_url("https://user:pass@example.org/")


def test_normalize_url_rejects_non_http_scheme():
    with pytest.raises(FetchError):
        normalize_url("file:///etc/passwd")


@pytest.mark.asyncio
async def test_private_literal_ip_is_blocked():
    with pytest.raises(FetchError, match="private, local, reserved"):
        await validate_public_url("http://127.0.0.1:8000/", allow_private=False)


@pytest.mark.asyncio
async def test_private_literal_ip_can_be_allowed_explicitly():
    result = await validate_public_url("http://127.0.0.1:8000/", allow_private=True)
    assert result == "http://127.0.0.1:8000/"
