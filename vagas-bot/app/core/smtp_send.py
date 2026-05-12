import smtplib
from email.message import EmailMessage
from pathlib import Path


def send_smtp_email(
    *,
    host: str,
    port: int,
    username: str,
    password: str,
    from_name: str | None,
    to_addr: str,
    subject: str,
    body_plain: str,
    attachment_path: str | None,
    attachment_filename: str = "curriculo.pdf",
    timeout_seconds: int = 60,
) -> None:
    """Envia e-mail em texto plano via SMTP (ex.: Gmail com STARTTLS na porta 587).

    Args:
        host: Host SMTP (ex.: smtp.gmail.com).
        port: Porta (587 para STARTTLS).
        username: Usuário SMTP (normalmente o próprio e-mail remetente).
        password: Senha ou senha de app.
        from_name: Nome exibido no remetente, opcional.
        to_addr: Destinatário.
        subject: Assunto.
        body_plain: Corpo em texto plano.
        attachment_path: Caminho absoluto de PDF para anexar, ou None.
        attachment_filename: Nome do arquivo no anexo.
        timeout_seconds: Timeout de conexão/envio.

    Raises:
        FileNotFoundError: Se attachment_path for informado e o arquivo não existir.
        smtplib.SMTPException: Em falhas de autenticação ou envio.
    """
    msg = EmailMessage()
    msg["From"] = f"{from_name} <{username}>" if from_name else username
    msg["To"] = to_addr
    msg["Subject"] = subject
    msg.set_content(body_plain)
    if attachment_path:
        path = Path(attachment_path)
        data = path.read_bytes()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="pdf",
            filename=attachment_filename,
        )
    with smtplib.SMTP(host, port, timeout=timeout_seconds) as smtp:
        smtp.starttls()
        smtp.login(username, password)
        smtp.send_message(msg)
