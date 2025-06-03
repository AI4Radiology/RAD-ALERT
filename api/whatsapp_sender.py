from . import settings
try:
    from twilio.rest import Client
    _client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN) if settings.TWILIO_SID else None
except ImportError:
    _client = None

def send_whatsapp(to:str, body:str):
    if not _client:
        print('[wa] Twilio OFF')
        return
    _client.messages.create(body=body[:1600], from_=settings.WHATSAPP_FROM, to=to)
