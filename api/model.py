from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import torch
from .settings import tools_settings as settings

tokenizer = AutoTokenizer.from_pretrained(settings.MODEL_DIR)
model     = AutoModelForSequenceClassification.from_pretrained(settings.MODEL_DIR)

id2label_map = {0: "No crítico", 1: "Crítico"}
model.config.id2label = id2label_map
model.config.label2id = {v: k for k, v in id2label_map.items()}

torch_device = 0 if torch.cuda.is_available() else -1
classifier = pipeline(
    "text-classification",
    model=model,
    tokenizer=tokenizer,
    device=torch_device
)
