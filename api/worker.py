import threading, time
from .db import get_conn, TABLE_CONFIG, TABLE_REPORTS, sql
from .emailer import send_email
from .whatsapp_sender import send_whatsapp
from . import settings

def _loop(interval:int=10):
    last_id = 0
    while True:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql.SQL("SELECT * FROM {} WHERE id>%s AND verdict='critical'")
                        .format(TABLE_REPORTS), (last_id,))
            rows = cur.fetchall()
            if rows:
                cur.execute(sql.SQL("SELECT key,value FROM {}")
                            .format(TABLE_CONFIG))
                cfg = {r['key']: r['value'] for r in cur.fetchall()}
                email_to = cfg.get('email', settings.DEFAULT_EMAIL)
                wa_to    = cfg.get('whatsapp', settings.WHATSAPP_TO)
            for r in rows:
                body = f"ALERTA CRÍTICA\n\n{r['text'][:500]}...\nprob={r['prob']:.2f}"
                send_email(email_to, 'RAD‑ALERT', body)
                send_whatsapp(wa_to, body)
                last_id = r['id']
        time.sleep(interval)

def start_worker():
    threading.Thread(target=_loop, daemon=True).start()
