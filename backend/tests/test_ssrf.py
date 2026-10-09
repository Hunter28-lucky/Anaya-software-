import pytest
from app.core.ssrf import validate_and_resolve_url, is_ip_allowed, SSRFValidationError


def test_is_ip_allowed():
    assert is_ip_allowed("127.0.0.1") is False
    assert is_ip_allowed("10.0.0.1") is False
    assert is_ip_allowed("172.16.0.1") is False
    assert is_ip_allowed("192.168.1.1") is False
    assert is_ip_allowed("169.254.169.254") is False
    assert is_ip_allowed("::1") is False
    assert is_ip_allowed("8.8.8.8") is True
    assert is_ip_allowed("1.1.1.1") is True


def test_validate_and_resolve_url_forbidden_schemes():
    with pytest.raises(SSRFValidationError, match="Forbidden URL scheme"):
        validate_and_resolve_url("ftp://example.com/test")

    with pytest.raises(SSRFValidationError, match="Forbidden URL scheme"):
        validate_and_resolve_url("file:///etc/passwd")


def test_validate_and_resolve_url_forbidden_hostnames():
    with pytest.raises(SSRFValidationError, match="Forbidden hostname"):
        validate_and_resolve_url("http://metadata.google.internal")

    with pytest.raises(SSRFValidationError, match="Forbidden hostname"):
        validate_and_resolve_url("http://localhost:8000")


def test_validate_and_resolve_url_forbidden_ports():
    with pytest.raises(SSRFValidationError, match="Port 22 is not allowed"):
        validate_and_resolve_url("http://example.com:22")

    with pytest.raises(SSRFValidationError, match="Port 3306 is not allowed"):
        validate_and_resolve_url("http://example.com:3306")


def test_validate_and_resolve_url_public_domain():
    url, ip = validate_and_resolve_url("https://example.com")
    assert url.startswith("https://example.com")
    assert ip is not None
