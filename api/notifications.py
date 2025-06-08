from twilio.rest import Client
from .settings import tools_settings as settings

_twilio_client = Client(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)

def send_whatsapp(to_number: str, body: str) -> str:
    
    msg = _twilio_client.messages.create(
        from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
        to=f"whatsapp:{to_number}",
        body=body
    )
    return msg.sid
