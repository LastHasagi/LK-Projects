import asyncio

from app.core.config import get_settings
from app.core.db import get_session_maker
from app.core.email_text import extract_emails
from app.core.smtp_send import send_smtp_email
from app.features.cv.service import get_active_cv

_MAX_EMAIL_BODY_CHARS = 50_000


async def dispatch_application_email(
    destinatario: str,
    assunto: str,
    corpo: str,
    *,
    anexar_cv: bool,
) -> str:
    """Valida e envia e-mail de candidatura via SMTP. Retorna mensagem de sucesso ou erro."""
    settings = get_settings()
    if not settings.smtp_user or not settings.smtp_password:
        return (
            "SMTP não configurado. Defina SMTP_USER e SMTP_PASSWORD no .env "
            "(Gmail: use senha de app em conta com 2FA)."
        )
    found = extract_emails(destinatario.strip())
    if len(found) != 1:
        return (
            "Informe exatamente um e-mail de destino "
            "(ou use extrair_emails_do_texto e peça qual usar)."
        )
    to_addr = found[0]
    if len(corpo) > _MAX_EMAIL_BODY_CHARS:
        return f"Corpo muito longo (máx. {_MAX_EMAIL_BODY_CHARS} caracteres)."
    attachment_path: str | None = None
    if anexar_cv:
        maker = get_session_maker()
        async with maker() as session:
            cv = await get_active_cv(session)
        if cv is None:
            return "Não há CV ativo. Envie um PDF e aguarde indexação antes de anexar."
        attachment_path = cv.path_pdf

    def _send() -> None:
        send_smtp_email(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            from_name=settings.smtp_from_name,
            to_addr=to_addr,
            subject=assunto.strip()[:998],
            body_plain=corpo,
            attachment_path=attachment_path if anexar_cv else None,
        )

    try:
        await asyncio.to_thread(_send)
    except FileNotFoundError:
        return "Arquivo do CV ativo não encontrado no disco. Reenvie o PDF."
    except Exception as e:
        return f"Falha ao enviar e-mail: {e!s}"

    return f"E-mail enviado com sucesso para {to_addr}."
