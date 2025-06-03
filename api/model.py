from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from . import settings
import os

try:
    tokenizer = AutoTokenizer.from_pretrained(os.getenv.HF_MODEL_NAME)
    model_hf  = AutoModelForSequenceClassification.from_pretrained(settings.HF_MODEL_NAME)
    nlp = pipeline("text-classification", model=model_hf, tokenizer=tokenizer)

    def predict_proba(txt: str) -> float:
        res = nlp(txt, truncation=True, max_length=512)[0]
        score = float(res['score'])
        return score if res['label'].upper().startswith('POS') else 1 - score
except Exception as e:
    _kw = {"neumonia","fractura","tumor","hemorragia"}
    predict_proba = lambda t: 0.9 if any(k in t.lower() for k in _kw) else 0.1
