from __future__ import annotations

from unittest.mock import Mock, patch
from participium.services.email_service import ConsoleEmailGateway
from participium.services.email_service import SmtpEmailGateway
from participium.services.email_service import build_email_gateway, SmtpEmailGateway
from participium.services.storage_service import StorageService
from participium.services.email_service import BaseEmailGateway
from types import SimpleNamespace

#covers those tests that weren't covered by other .py 

class TestConsoleEmailGateway:

    def test_send_writes_file_to_outbox(self, tmp_path):

        gw = ConsoleEmailGateway(outbox_dir=tmp_path, sender="no-reply@example.com")
        gw.send(recipient="user@example.com", subject="Hello", body="World")

        files = list(tmp_path.iterdir())
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8")
        assert "user@example.com" in content
        assert "Hello" in content
        assert "World" in content

    def test_send_creates_outbox_dir_if_missing(self, tmp_path):
        outbox = tmp_path / "outbox" / "nested"
        gw = ConsoleEmailGateway(outbox_dir=outbox, sender="no-reply@example.com")
        gw.send(recipient="user@example.com", subject="s", body="b")

        assert outbox.exists()
        assert len(list(outbox.iterdir())) == 1


class TestSmtpEmailGateway:

    def test_send_calls_smtp_correctly(self):

        gw = SmtpEmailGateway(
            host="smtp.example.com",
            port=587,
            username="user",
            password="pass",
            sender="no-reply@example.com",
            use_tls=True,
        )

        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp = Mock()
            mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_smtp_class.return_value.__exit__ = Mock(return_value=False)

            gw.send(recipient="dest@example.com", subject="Test", body="Body")

            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once_with("user", "pass")
            mock_smtp.send_message.assert_called_once()


class TestBuildAndBaseGateways:

    def test_build_email_gateway_returns_smtp_when_configured(self, tmp_path):

        settings = SimpleNamespace(
            mail_backend="smtp",
            smtp_host="smtp.example.com",
            smtp_port=25,
            smtp_username=None,
            smtp_password=None,
            mail_from="me@example.com",
            smtp_use_tls=False,
            mail_outbox_dir=tmp_path,
        )

        gw = build_email_gateway(settings)
        assert isinstance(gw, SmtpEmailGateway)

    def test_build_email_gateway_returns_console_by_default(self, tmp_path):

        settings = SimpleNamespace(
            mail_backend="console",
            smtp_host="",
            smtp_port=0,
            smtp_username=None,
            smtp_password=None,
            mail_from="me@example.com",
            smtp_use_tls=False,
            mail_outbox_dir=tmp_path,
        )

        gw = build_email_gateway(settings)
        assert isinstance(gw, ConsoleEmailGateway)

    def test_base_storage_and_email_defaults(self):

        svc = StorageService()
        assert svc.save(None) == "simulated-file"

        gw = BaseEmailGateway()
        assert gw.send("a@b.com", "s", "b") is None



