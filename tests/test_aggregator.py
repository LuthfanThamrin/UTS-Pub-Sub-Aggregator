"""
Unit tests untuk Pub-Sub Log Aggregator.

Jalankan: pytest tests/ -v
"""

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# ─── Helper ──────────────────────────────────────────────────────────────────

def make_event(
    topic="test.topic",
    event_id="evt-001",
    timestamp="2025-01-01T00:00:00Z",
    source="pytest",
    payload=None,
):
    return {
        "topic": topic,
        "event_id": event_id,
        "timestamp": timestamp,
        "source": source,
        "payload": payload or {},
    }


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Client baru dengan DB sementara per test."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "dedup.db"))

    import importlib, src.main as m
    importlib.reload(m)

    from src.main import app
    with TestClient(app) as c:
        time.sleep(0.05)
        yield c


# ─── Test 1: Schema valid ─────────────────────────────────────────────────────

def test_schema_valid(client):
    """Event valid harus diterima dengan 202."""
    resp = client.post("/publish", json={"events": [make_event()]})
    assert resp.status_code == 202
    data = resp.json()
    assert data["received"] == 1
    assert data["accepted"] == 1
    assert data["duplicates"] == 0


# ─── Test 2: Schema — field wajib hilang ─────────────────────────────────────

def test_schema_missing_source(client):
    """Event tanpa 'source' harus ditolak 422."""
    bad = {
        "topic": "x", "event_id": "e1",
        "timestamp": "2025-01-01T00:00:00Z",
        "payload": {},
    }
    resp = client.post("/publish", json={"events": [bad]})
    assert resp.status_code == 422


# ─── Test 3: Schema — timestamp invalid ──────────────────────────────────────

def test_schema_bad_timestamp(client):
    """Timestamp bukan ISO 8601 harus ditolak 422."""
    resp = client.post("/publish", json={"events": [make_event(timestamp="01-01-2025")]})
    assert resp.status_code == 422


# ─── Test 4: Dedup — duplikat dalam satu batch di-drop ───────────────────────

def test_dedup_same_batch(client):
    """Kirim event yang sama dua kali → hanya 1 diterima."""
    evt = make_event(event_id="dup-001")
    resp = client.post("/publish", json={"events": [evt, evt]})
    assert resp.status_code == 202
    data = resp.json()
    assert data["received"] == 2
    assert data["accepted"] + data["duplicates"] == 2
    assert data["accepted"] >= 1


# ─── Test 5: GET /events hanya event unik ────────────────────────────────────

def test_events_unique_only(client):
    """3 event masuk (1 duplikat) → GET /events hanya tampilkan 2."""
    events = [
        make_event(event_id="u-001"),
        make_event(event_id="u-002"),
        make_event(event_id="u-001"),   # duplikat
    ]
    client.post("/publish", json={"events": events})
    time.sleep(0.3)

    resp = client.get("/events", params={"topic": "test.topic"})
    assert resp.status_code == 200
    ids = [e["event_id"] for e in resp.json()]
    assert sorted(ids) == ["u-001", "u-002"]


# ─── Test 6: Persistensi dedup store (simulasi restart) ──────────────────────

def test_dedup_persistence(tmp_path):
    """
    Tulis ke DedupStore, tutup, buka ulang →
    event yang sama masih terdeteksi duplikat.
    """
    from src.dedup_store import DedupStore

    db = tmp_path / "persist.db"

    store1 = DedupStore(db_path=db)
    saved = store1.save("logs", "p-001", "2025-01-01T00:00:00Z", "svc", {}, "2025-01-01T00:00:01Z")
    assert saved is True
    store1.close()

    store2 = DedupStore(db_path=db)
    assert store2.is_duplicate("logs", "p-001") is True
    saved2 = store2.save("logs", "p-001", "2025-01-01T00:00:00Z", "svc", {}, "2025-01-01T00:00:02Z")
    assert saved2 is False
    store2.close()


# ─── Test 7: GET /stats konsisten ────────────────────────────────────────────

def test_stats_consistency(client):
    """Stats harus mencerminkan event yang dikirim."""
    events = [
        make_event(event_id="s-001"),
        make_event(event_id="s-002"),
        make_event(event_id="s-001"),   # duplikat
        make_event(event_id="s-003"),
    ]
    client.post("/publish", json={"events": events})
    time.sleep(0.5)

    stats = client.get("/stats").json()
    assert stats["unique_processed"] >= 3
    assert stats["uptime_seconds"] >= 0
    assert "test.topic" in stats["topics"]


# ─── Test 8: Stress kecil — 1.000 event, 20% duplikat ───────────────────────

def test_stress_1000_events(client):
    """1.000 event (800 unik + 200 duplikat) harus selesai < 10 detik."""
    unique = [
        make_event(topic="stress", event_id=f"s-{i:04d}", source="tester")
        for i in range(800)
    ]
    dups = unique[:200]   # 20% duplikat
    all_events = unique + dups

    t0 = time.monotonic()
    resp = client.post("/publish", json={"events": all_events})
    elapsed = time.monotonic() - t0

    assert resp.status_code == 202
    assert elapsed < 10.0, f"Terlalu lambat: {elapsed:.2f}s"

    time.sleep(2.0)
    result = client.get("/events", params={"topic": "stress"}).json()
    assert len(result) == 800