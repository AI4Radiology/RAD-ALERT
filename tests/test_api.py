

import json
import uuid
import pytest
from httpx import AsyncClient

from api.main import app              
from api.notifications import send_whatsapp as real_send_whatsapp
from api.db            import log_report as real_log_report
from api.model import model   


@pytest.fixture
def sample_report():
    return (
        "TOMOGRAFÍA COMPUTADA DE TÓRAX\n"
        "Hallazgos: Consolidaciones …\n"
        "Opinión: Sospecha de hemorragia intraparenquimatosa."
    )




@pytest.fixture(autouse=True)
def patch_send_whatsapp(monkeypatch):
    def _fake_send(to, body):
        return "SM_FAKE_SID" if "Sospecha" in body else None
    # parche en ambos lugares
    monkeypatch.setattr("api.notifications.send_whatsapp", _fake_send)
    monkeypatch.setattr("api.processing.send_whatsapp", _fake_send)


@pytest.fixture(autouse=True)
def patch_log_report(monkeypatch):
    def factory():
        collected = []
        def _fake_log(report_id, score, sent):
            collected.append((report_id, score, sent))
        return collected, _fake_log

    collected, _fake = factory()
    monkeypatch.setattr("api.db.log_report", _fake)
    monkeypatch.setattr("api.processing.log_report", _fake)
    yield collected 

@pytest.mark.asyncio
async def test_happy_path(sample_report, patch_log_report):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {"report": sample_report, "reportId": "abc-123"}
        r = await ac.post("/hl7", json=payload)
    assert r.status_code == 200
    
    assert len(patch_log_report) == 1
    rid, score, sent = patch_log_report[0]
    assert rid == "abc-123"
    assert sent is True
    assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_no_critico(sample_report, patch_log_report):
    
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("api.model.classifier", lambda txt, truncation: [{"label": "No crítico", "score": 0.8}])
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={"report": sample_report})
    assert r.status_code == 200
    
    assert patch_log_report[0][2] is False
    monkeypatch.undo()


@pytest.mark.asyncio
async def test_json_malformado():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        bad = "{ report: ??? }"
        r = await ac.post("/hl7", content=bad, headers={"Content-Type": "application/json"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_invalid_content_type(sample_report):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/hl7", content="foo", headers={"Content-Type": "text/plain"})
    assert r.status_code == 415


@pytest.mark.asyncio
async def test_duplicate_id(sample_report, patch_log_report):
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {"report": sample_report, "reportId": "dup-1"}
        await ac.post("/hl7", json=payload)
        await ac.post("/hl7", json=payload)
    
    assert len(patch_log_report) == 2
    assert all(rid == "dup-1" for rid,_,_ in patch_log_report)
