
import os
from dotenv import load_dotenv

load_dotenv()


PG_USER     = os.getenv("PG_USER")
PG_PASSWORD = os.getenv("PG_PASSWORD")
PG_HOST     = os.getenv("PG_HOST")
PG_PORT     = os.getenv("PG_PORT")
PG_DBNAME   = os.getenv("PG_DBNAME")
DB_SCHEMA         = os.getenv("DB_SCHEMA", "public")

MODEL_PATH        = os.getenv("MODEL_PATH", "model/")
HF_MODEL_NAME     = os.getenv("HF_MODEL", "papluca/xlm-roberta-base-language-detection")
THRESHOLD         = float(os.getenv("THRESHOLD", 0.5))


DEFAULT_EMAIL     = os.getenv("DEFAULT_EMAIL", "alertas@hospital.org")
SMTP_SERVER       = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT         = int(os.getenv("SMTP_PORT", 587))
SMTP_USER         = os.getenv("SMTP_USER", "user@example.com")
SMTP_PASS         = os.getenv("SMTP_PASS", "password")


TWILIO_SID        = os.getenv("TWILIO_SID", "")
TWILIO_TOKEN      = os.getenv("TWILIO_TOKEN", "")
WHATSAPP_FROM     = os.getenv("WHATSAPP_FROM", "whatsapp:+14155238886")
WHATSAPP_TO       = os.getenv("WHATSAPP_TO", "whatsapp:+573001234567")

STREAMLIT_PORT    = int(os.getenv("STREAMLIT_PORT", 8501))
PORT    = int(os.getenv("APP_PORT", 8000))



settings = {
    "data": {
        "root_dir": "/content/drive/MyDrive/PDG/data",
        "train_file": "train_df.xlsx",
        "val_file":   "val_df.xlsx",
        "test_file":  "test_df.xlsx",
        "text_col":   "texto",
        "label_col":  "etiqueta",
    },
    "model": {
        "name":       "PlanTL-GOB-ES/roberta-base-biomedical-clinical-es",
        "max_length": 256
    },
    "training": {
        "batch_size":       8,
        "eval_batch_size":  16,
        "num_epochs":       6,
        "learning_rate":    2e-5,
        "weight_decay":     0.01,
        "gamma":            2.0,
        "early_patience":   3,
        "seed":             42,
        "output_dir":       "/content/critico_clf"
    }
}
