import importlib.util
import shutil
import ssl
from pathlib import Path

import pytest

import app.db as db
from app.db import _connect_args

_spec = importlib.util.spec_from_file_location(
    "init_db_script", Path(__file__).resolve().parent.parent / "scripts" / "init_db.py"
)
init_db = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(init_db)


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv("DB_SSL_CA", raising=False)
    monkeypatch.delenv("DB_SSL_CA_PATH", raising=False)
    monkeypatch.setattr(db, "_warned_unverified", False)


def _make_ca(tmp_path):
    candidates = [ssl.get_default_verify_paths().cafile]
    try:
        import certifi

        candidates.insert(0, certifi.where())
    except ImportError:
        pass
    for src in candidates:
        if src and Path(src).is_file():
            dest = tmp_path / "ca.pem"
            shutil.copy(src, dest)
            return dest
    pytest.skip("no CA bundle available")


def test_plain_url_has_no_ssl():
    args = _connect_args("mysql://u:p@h:3307/tickets")
    assert args["database"] == "tickets"
    assert args["port"] == 3307
    assert "ssl" not in args


def test_query_stripped_from_database_name():
    args = _connect_args("mysql://u:p@h/defaultdb?ssl-mode=REQUIRED")
    assert args["database"] == "defaultdb"


def test_required_without_ca_is_unverified_and_warns_once(caplog):
    with caplog.at_level("WARNING"):
        ctx = _connect_args("mysql://u:p@h/d?ssl-mode=required")["ssl"]
        _connect_args("mysql://u:p@h/d?ssl-mode=required")
    assert ctx.verify_mode == ssl.CERT_NONE
    assert ctx.check_hostname is False
    assert len(caplog.records) == 1


def test_unknown_mode_is_plain():
    assert "ssl" not in _connect_args("mysql://u:p@h/d?ssl-mode=DISABLED")


def test_ca_path_verifies_cert_only(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_SSL_CA_PATH", str(_make_ca(tmp_path)))
    ctx = _connect_args("mysql://u:p@h/d?ssl-mode=VERIFY_CA")["ssl"]
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is False


def test_verify_identity_checks_hostname(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_SSL_CA_PATH", str(_make_ca(tmp_path)))
    ctx = _connect_args("mysql://u:p@h/d?ssl-mode=VERIFY_IDENTITY")["ssl"]
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def test_ca_pem_text_written_to_temp_file_once(monkeypatch, tmp_path):
    bundle = _make_ca(tmp_path).read_text()
    end = "-----END CERTIFICATE-----"
    pem = bundle[: bundle.index(end) + len(end)]
    pem = pem[pem.index("-----BEGIN CERTIFICATE-----") :]
    monkeypatch.setenv("DB_SSL_CA", pem)
    path1 = db._ca_file()
    assert path1 == db._ca_file()
    assert Path(path1).read_text().strip() == pem.strip()
    ctx = _connect_args("mysql://u:p@h/d?ssl-mode=REQUIRED")["ssl"]
    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_init_db_plain_url():
    params = init_db.parse_database_url("mysql://u:p@h:3306/tickets")
    assert params["database"] == "tickets"
    assert "ssl" not in params


def test_init_db_aiven_url_strips_query():
    url = "mysql://avnadmin:pw@h.aivencloud.com:12345/tickets?ssl-mode=REQUIRED"
    params = init_db.parse_database_url(url)
    assert params["database"] == "tickets"
    assert params["port"] == 12345
    assert params["ssl"].verify_mode == ssl.CERT_NONE


def test_init_db_ca_path_verify_identity(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_SSL_CA_PATH", str(_make_ca(tmp_path)))
    params = init_db.parse_database_url("mysql://u:p@h/tickets?ssl-mode=VERIFY_IDENTITY")
    assert params["ssl"].verify_mode == ssl.CERT_REQUIRED
    assert params["ssl"].check_hostname is True
