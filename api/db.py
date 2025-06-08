from supabase import create_client, Client
from .settings import tools_settings as settings

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

def log_report(report_id: str, score: float, whatsapp_sent: bool) -> None:
    supabase \
      .table("report_log") \
      .upsert(
          {
            "report_id": report_id,
            "score": score,
            "whatsapp_sent": whatsapp_sent
          }
      ) \
      .execute()
