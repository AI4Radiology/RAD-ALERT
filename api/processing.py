import re
from .model import classifier
from .settings import tools_settings as settings
from .notifications import send_whatsapp
from .db import log_report


async def process_report(report: str, report_id: str) -> None:
    cleaned = report.lstrip("\ufeff").replace("\r\n", "\n").strip()

    match = re.search(r"(Hallazgos.*)$", cleaned,
                      flags=re.IGNORECASE | re.DOTALL)
    flat = re.sub(r"\s+", " ", (match.group(1) if match else "")).strip()

    pred = classifier(flat, truncation=True)[0]
    label, score = pred["label"], pred["score"]

    if label == "Crítico":
        opin_match = re.search(
            r"(?i)opinión\s*[:\-]?\s*(.*)",  
            cleaned,
            flags=re.IGNORECASE | re.DOTALL
        )
        opinion_text = ""
        if opin_match:
            opinion_text = re.sub(r"\s+", " ", opin_match.group(1)).strip()
        else:
            opinion_text = "(No se encontró sección 'opinión')"
        
        body = (
            f"🚨 *Alerta Crítico* 🚨\n"
            f"ID Informe: {report_id}\n"
            f"Hallazgos: {opinion_text}...\n"
            f"Confianza: {score:.2%}"
        )
        whatsapp_sent = False
        sid = None
        try:
            sid = send_whatsapp(settings.TWILIO_WHATSAPP_TO, body)
            whatsapp_sent = bool(sid)
        except Exception as e:
            whatsapp_sent = False
            print(f"► [{report_id}] Error enviando WhatsApp: {e}")
        

        log_report(report_id, score, whatsapp_sent)
        


