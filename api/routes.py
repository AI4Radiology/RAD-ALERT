import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
from contextlib import asynccontextmanager

from . import settings, model
from .db import get_conn, TABLE_REPORTS, TABLE_CONFIG, sql
from .worker import start_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    start_worker()
    yield
    


app = FastAPI(title='RAD-ALERT API', lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)


class ReportIn(BaseModel):
    report: str

class VerdictOut(BaseModel):
    verdict: Literal['critical','normal']
    probability: float

class ContactCfg(BaseModel):
    email: str | None = None
    whatsapp: str | None = None

@app.post('/predict', response_model=VerdictOut)
def predict(inp: ReportIn):
    print(f"Received report: {inp.report}")














@app.get('/config', response_model=ContactCfg)
def get_cfg():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(sql.SQL("SELECT key, value FROM {}")
                    .format(TABLE_CONFIG))
        cfg = {r['key']: r['value'] for r in cur.fetchall()}
    return ContactCfg(email=cfg.get('email'), whatsapp=cfg.get('whatsapp'))

@app.put('/config', response_model=ContactCfg)
def put_cfg(cfg: ContactCfg):
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            if cfg.email is not None:
                cur.execute(
                    sql.SQL("UPDATE {} SET value = %s WHERE key = 'email'")
                        .format(TABLE_CONFIG), (cfg.email,)
                )
            if cfg.whatsapp is not None:
                cur.execute(
                    sql.SQL("UPDATE {} SET value = %s WHERE key = 'whatsapp'")
                        .format(TABLE_CONFIG), (cfg.whatsapp,)
                )
            conn.commit()
        return cfg
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
