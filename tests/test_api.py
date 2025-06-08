import pytest
from httpx import AsyncClient, ASGITransport
from api.main import app

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
        return "SM_FAKE_SID"  # Siempre simula éxito en los tests
    monkeypatch.setattr("api.notifications.send_whatsapp", _fake_send)
    monkeypatch.setattr("api.processing.send_whatsapp", _fake_send)


@pytest.fixture(autouse=True)
def patch_log_report(monkeypatch):
    collected = []
    def _fake_log(report_id, score, sent,critico):
        collected.append((report_id, score, sent,critico))
    monkeypatch.setattr("api.db.log_report", _fake_log)
    monkeypatch.setattr("api.processing.log_report", _fake_log)
    return collected

@pytest.fixture(autouse=True)
def patch_classifier(monkeypatch):
    
    monkeypatch.setattr("api.processing.classifier", lambda txt, truncation: [{"label": "Crítico", "score": 0.9}])

transport = ASGITransport(app=app)

@pytest.mark.asyncio
async def test_happy_path(sample_report, patch_log_report):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={"report": sample_report, "reportId": "abc-123"})
    assert r.status_code == 200
    assert len(patch_log_report) == 1
    rid, score, sent, critico  = patch_log_report[0]
    assert rid == "abc-123"
    assert sent is True
    assert critico is True

@pytest.mark.asyncio
async def test_no_critico(sample_report, patch_log_report, monkeypatch):
    
    monkeypatch.setattr("api.processing.classifier", lambda txt, truncation: [{"label": "No crítico", "score": 0.8}])
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={"report": sample_report})
    assert r.status_code == 200
    assert len(patch_log_report) == 0

@pytest.mark.asyncio
async def test_json_malformado():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", content="{ report: ??? }", headers={"Content-Type": "application/json"})
    assert r.status_code == 400

@pytest.mark.asyncio
async def test_invalid_content_type(sample_report):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", content="foo", headers={"Content-Type": "text/plain"})
    assert r.status_code == 400

@pytest.mark.asyncio
async def test_duplicate_id(sample_report, patch_log_report):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        await ac.post("/hl7", json={"report": sample_report, "reportId": "dup-1"})
        await ac.post("/hl7", json={"report": sample_report, "reportId": "dup-1"})
    assert len(patch_log_report) == 2
    assert all(rid == "dup-1" for rid,_,_,_ in patch_log_report)

import uuid


@pytest.mark.asyncio
async def test_empty_report_field():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={"report": ""})
    assert r.status_code == 200
    data = r.json()
    assert data["ack"] == "bien recibido"
    assert "report_id" in data

@pytest.mark.asyncio
async def test_missing_report_field():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={})
    assert r.status_code == 200
    data = r.json()
    assert data["ack"] == "bien recibido"
    assert "report_id" in data and isinstance(data["report_id"], str)


@pytest.mark.asyncio
async def test_opinion_only_section(patch_log_report, monkeypatch):
    monkeypatch.setattr("api.processing.classifier", lambda txt, truncation: [{"label": "Crítico", "score": 0.95}])
    text = "Opinión: Sospecha de hemorragia"
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={"report": text, "reportId": "only-opinion"})
    assert r.status_code == 200
    assert len(patch_log_report) == 1
    rid, score, sent, critico  = patch_log_report[0]
    assert rid == "only-opinion"


@pytest.mark.asyncio
async def test_exception_in_send_whatsapp(patch_log_report, monkeypatch):
    monkeypatch.setattr("api.processing.classifier", lambda txt, truncation: [{"label": "Crítico", "score": 0.99}])
    
    monkeypatch.setattr("api.notifications.send_whatsapp", lambda to, body: (_ for _ in ()).throw(Exception("Twilio fail!")))
    monkeypatch.setattr("api.processing.send_whatsapp", lambda to, body: (_ for _ in ()).throw(Exception("Twilio fail!")))
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={"report": "Hallazgos: ...\nOpinión: Prueba", "reportId": "fail-twilio"})
    assert r.status_code == 200
    assert len(patch_log_report) == 1
    rid, score, sent, critico  = patch_log_report[0]
    assert rid == "fail-twilio"
    assert sent is False
    assert critico is True


@pytest.mark.asyncio
async def test_report_id_autogenerated():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={"report": "Hallazgos: ..."})
    assert r.status_code == 200
    data = r.json()
    assert "report_id" in data
    
    try:
        uuid.UUID(data["report_id"])
    except Exception:
        assert False, "report_id no es un UUID válido"


@pytest.mark.asyncio
async def test_report_numeric():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={"report": 12345})
    assert r.status_code == 200

@pytest.mark.asyncio
async def test_report_null():
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={"report": None})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_very_long_report(patch_log_report, monkeypatch):
    monkeypatch.setattr("api.processing.classifier", lambda txt, truncation: [{"label": "Crítico", "score": 0.77}])
    text = "Hallazgos: " + ("mucho texto, " * 10000) + "\nOpinión: Ok"
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={"report": text, "reportId": "large-report"})
    assert r.status_code == 200
    assert len(patch_log_report) == 1
    rid, score, sent, critico  = patch_log_report[0]
    assert rid == "large-report"


@pytest.mark.asyncio
async def test_hallazgos_no_opinion(patch_log_report, monkeypatch):
    monkeypatch.setattr("api.processing.classifier", lambda txt, truncation: [{"label": "Crítico", "score": 0.88}])
    text = "Hallazgos: Consolidaciones en el lóbulo superior derecho."
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/hl7", json={"report": text, "reportId": "no-opinion"})
    assert r.status_code == 200
    assert len(patch_log_report) == 1
    rid, score, sent, critico  = patch_log_report[0]
    assert rid == "no-opinion"
