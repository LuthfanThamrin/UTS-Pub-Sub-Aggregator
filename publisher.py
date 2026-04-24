"""
publisher.py — Simulator publisher untuk Docker Compose.
Mengirim EVENT_COUNT event dengan DUPLICATE_RATIO sebagai duplikat.
"""

import json
import logging
import os
import random
import time
import uuid
from datetime import datetime, timezone
from urllib.request import Request, urlopen

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("publisher")

AGGREGATOR_URL = os.getenv("AGGREGATOR_URL", "http://localhost:8080")
EVENT_COUNT     = int(os.getenv("EVENT_COUNT", "5000"))
DUPLICATE_RATIO = float(os.getenv("DUPLICATE_RATIO", "0.20"))
BATCH_SIZE      = int(os.getenv("BATCH_SIZE", "100"))

TOPICS = ["logs.appA", "logs.appB", "metrics.cpu", "metrics.mem"]


def wait_ready(timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urlopen(f"{AGGREGATOR_URL}/health", timeout=3)
            logger.info("Aggregator ready.")
            return
        except Exception:
            logger.info("Menunggu aggregator...")
            time.sleep(2)
    raise RuntimeError("Aggregator tidak merespons.")


def post(events):
    body = json.dumps({"events": events}).encode()
    req = Request(f"{AGGREGATOR_URL}/publish", data=body,
                  headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def main():
    wait_ready()

    n_unique = int(EVENT_COUNT * (1 - DUPLICATE_RATIO))
    n_dup    = EVENT_COUNT - n_unique
    now      = datetime.now(timezone.utc).isoformat()

    unique_events = [
        {"topic": random.choice(TOPICS), "event_id": str(uuid.uuid4()),
         "timestamp": now, "source": "publisher", "payload": {"i": i}}
        for i in range(n_unique)
    ]
    all_events = unique_events + random.choices(unique_events, k=n_dup)
    random.shuffle(all_events)

    received = accepted = dups = 0
    t0 = time.monotonic()
    for i in range(0, len(all_events), BATCH_SIZE):
        try:
            r = post(all_events[i:i + BATCH_SIZE])
            received += r["received"]; accepted += r["accepted"]; dups += r["duplicates"]
        except Exception as e:
            logger.error("Batch gagal: %s", e)

    logger.info("Selesai: received=%d accepted=%d dups=%d (%.2fs)",
                received, accepted, dups, time.monotonic() - t0)

    try:
        with urlopen(f"{AGGREGATOR_URL}/stats", timeout=5) as r:
            logger.info("Stats: %s", json.dumps(json.loads(r.read()), indent=2))
    except Exception:
        pass


if __name__ == "__main__":
    main()