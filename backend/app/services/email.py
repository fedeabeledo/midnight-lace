import asyncio
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_registro_html(codigo: str) -> str:
    return f"""
    <html>
    <body style="font-family: Georgia, serif; background:#f5f0eb; padding:20px;">
        <div style="max-width:600px; margin:auto; background:#fff; padding:30px; border:1px solid #d4c5b5;">
            <h1 style="color:#3a2e2e; text-align:center;">Midnight Lace</h1>
            <h2 style="color:#6b4f4f;">Confirma tu cuenta</h2>
            <p>Gracias por registrarte. Tu código de confirmación es:</p>
            <div style="font-size:32px; letter-spacing:8px; text-align:center;
                        background:#3a2e2e; color:#f5f0eb; padding:20px; margin:20px 0;
                        font-family: 'Courier New', monospace;">
                {codigo}
            </div>
            <p>Ingresá este código en la pantalla de confirmación para activar tu cuenta.</p>
            <p style="color:#888; font-size:12px;">El código expira en 15 minutos.</p>
        </div>
    </body>
    </html>
    """


def _build_recuperacion_html(codigo: str) -> str:
    return f"""
    <html>
    <body style="font-family: Georgia, serif; background:#f5f0eb; padding:20px;">
        <div style="max-width:600px; margin:auto; background:#fff; padding:30px; border:1px solid #d4c5b5;">
            <h1 style="color:#3a2e2e; text-align:center;">Midnight Lace</h1>
            <h2 style="color:#6b4f4f;">Recuperación de contraseña</h2>
            <p>Recibimos una solicitud para restablecer tu contraseña. Tu código es:</p>
            <div style="font-size:32px; letter-spacing:8px; text-align:center;
                        background:#3a2e2e; color:#f5f0eb; padding:20px; margin:20px 0;
                        font-family: 'Courier New', monospace;">
                {codigo}
            </div>
            <p>Si no solicitaste este cambio, ignorá este email.</p>
            <p style="color:#888; font-size:12px;">El código expira en 15 minutos.</p>
        </div>
    </body>
    </html>
    """


def _build_rechazo_html(motivo: str) -> str:
    return f"""
    <html>
    <body style="font-family: Georgia, serif; background:#f5f0eb; padding:20px;">
        <div style="max-width:600px; margin:auto; background:#fff; padding:30px; border:1px solid #d4c5b5;">
            <h1 style="color:#3a2e2e; text-align:center;">Midnight Lace</h1>
            <h2 style="color:#6b4f4f;">Solicitud rechazada</h2>
            <p>Lamentamos informarte que tu solicitud de registro fue rechazada.</p>
            <p><strong>Motivo:</strong> {motivo}</p>
            <p>Si creés que es un error, contactanos a soporte@midnightlace.com.</p>
        </div>
    </body>
    </html>
    """


SUBJECTS = {
    "registro": "Midnight Lace — Código de confirmación",
    "recuperacion": "Midnight Lace — Recuperación de contraseña",
    "rechazo": "Midnight Lace — Solicitud rechazada",
}


def _build_email(to: str, tipo: str, codigo: str | None = None, motivo: str | None = None) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_from}>"
    msg["To"] = to
    msg["Subject"] = SUBJECTS[tipo]

    if tipo == "registro":
        html = _build_registro_html(codigo)
    elif tipo == "recuperacion":
        html = _build_recuperacion_html(codigo)
    elif tipo == "rechazo":
        html = _build_rechazo_html(motivo or "No especificado")
    else:
        raise ValueError(f"Tipo de email no soportado: {tipo}")

    text_fallback = f"Midnight Lace\n\n{SUBJECTS[tipo]}\n\n"
    if codigo:
        text_fallback += f"Código: {codigo}\n\nExpira en 15 minutos."
    if motivo:
        text_fallback += f"Motivo: {motivo}"

    msg.attach(MIMEText(text_fallback, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


def _send_smtp_sync(msg: MIMEMultipart) -> tuple[bool, str]:
    try:
        if settings.smtp_use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls(context=context)
                if settings.smtp_user:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_user:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        return True, "OK"
    except Exception as e:
        return False, str(e)


async def send_email(to: str, tipo: str, codigo: str | None = None, motivo: str | None = None) -> bool:
    """
    Envía email según el tipo:
    - "registro": email con código de confirmación
    - "recuperacion": email con código de recuperación
    - "rechazo": email de rechazo (requiere motivo)

    Siempre imprime en consola (para dev/testing).
    Retorna True si se envió OK, False si falló.
    Si SMTP no está configurado, solo imprime en consola y retorna True.
    """
    if tipo == "registro" or tipo == "recuperacion":
        print(f"[EMAIL] {tipo.upper()} → {to}: código={codigo}")
    elif tipo == "rechazo":
        print(f"[EMAIL] {tipo.upper()} → {to}: motivo={motivo}")

    if not settings.smtp_host:
        print(f"[EMAIL] SMTP no configurado. Email no enviado (solo log).")
        return True

    try:
        msg = _build_email(to, tipo, codigo=codigo, motivo=motivo)
        ok, err = await asyncio.to_thread(_send_smtp_sync, msg)
        if ok:
            print(f"[EMAIL] {tipo.upper()} → {to}: enviado OK")
            logger.info(f"Email {tipo} enviado a {to}")
            return True
        else:
            print(f"[EMAIL] {tipo.upper()} → {to}: ERROR {err}")
            logger.error(f"Error enviando email {tipo} a {to}: {err}")
            return False
    except Exception as e:
        print(f"[EMAIL] {tipo.upper()} → {to}: EXCEPTION {e}")
        logger.exception(f"Excepción enviando email {tipo} a {to}")
        return False
