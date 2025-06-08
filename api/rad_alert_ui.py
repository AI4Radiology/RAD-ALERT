import subprocess
import streamlit as st
from supabase import create_client, Client
import os
import sys


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


API_CMD = [
    sys.executable, "-m", "uvicorn",
    "api.main:app",
    "--host", "0.0.0.0",
    "--port", "8000",
    "--log-level", "info"
]

if "api_process_started" not in st.session_state:
    
    st.session_state["api_proc"] = subprocess.Popen(API_CMD)
    st.session_state["api_process_started"] = True


from api.settings import tools_settings as settings


SUPABASE_URL = settings.SUPABASE_URL
SUPABASE_KEY = settings.SUPABASE_KEY
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


st.set_page_config(page_title="RAD-ALERT Monitor", page_icon="🚨", layout="wide")
st.title("RAD-ALERT: Monitor y Configuración WhatsApp")


if "wa_to" not in st.session_state:
    st.session_state["wa_to"] = settings.TWILIO_WHATSAPP_TO

wa_to = st.text_input("Destino WhatsApp (+573XXXXXXXXX)", st.session_state["wa_to"])
if st.button("Guardar número de destino"):
    st.session_state["wa_to"] = wa_to
    st.success(f"Número destino actualizado: {wa_to}")

st.divider()
st.subheader("Reportes procesados recientemente")


try:
    response = supabase.from_("report_log").select("*").order("report_id", desc=True).limit(50).execute()
    data = response.data
    if data:
        import pandas as pd
        df = pd.DataFrame(data)
        cols = ["report_id", "score", "critico", "whatsapp_sent"]
        extra = [c for c in df.columns if c not in cols]
        st.dataframe(df[cols + extra], use_container_width=True)
    else:
        st.info("No hay reportes guardados aún.")
except Exception as e:
    st.error(f"Error consultando reportes: {e}")

st.caption("RAD-ALERT - Monitor Streamlit")
