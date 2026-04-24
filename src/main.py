import asyncio
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from src.consumer import Consumer
from src.dedup_store import DedupStore
from src.models import PublishRequest, PublishResponse, StatsResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")

DB_PATH = Path(os.getenv("DB_PATH", "data/dedup.db"))
QUEUE_MAX = int(os.getenv("QUEUE_MAX", "100000"))

store: DedupStore = None
consumer: Consumer = None
queue: asyncio.Queue = None
start_time: float = 0.0
total_duplicates_rejected: int = 0  # tracking duplikat dari publish endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    global store, consumer, queue, start_time
    start_time = time.monotonic()
    store = DedupStore(db_path=DB_PATH)
    queue = asyncio.Queue(maxsize=QUEUE_MAX)
    consumer = Consumer(queue=queue, store=store)
    consumer.start()
    logger.info("Aggregator siap.")
    yield
    await consumer.stop()
    store.close()
    logger.info("Aggregator shutdown.")


app = FastAPI(
    title="Pub-Sub Log Aggregator",
    description="Idempotent consumer + SQLite deduplication",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/publish", response_model=PublishResponse, status_code=202)
async def publish(body: PublishRequest):
    global total_duplicates_rejected
    accepted = 0
    duplicates = 0
    seen_in_request: set[tuple[str, str]] = set()  # cegah intra-request dupes

    for event in body.events:
        key = (event.topic, event.event_id)

        # Cek duplikat dalam request yang sama
        if key in seen_in_request:
            duplicates += 1
            logger.warning(
                "[INTRA-REQUEST DUP] topic=%s event_id=%s", event.topic, event.event_id
            )
            continue

        # Cek duplikat di DB
        if store.is_duplicate(event.topic, event.event_id):
            duplicates += 1
            logger.warning(
                "[PRE-CHECK DUP] topic=%s event_id=%s", event.topic, event.event_id
            )
            continue

        try:
            queue.put_nowait(event.model_dump())
            seen_in_request.add(key)
            accepted += 1
        except asyncio.QueueFull:
            raise HTTPException(status_code=429, detail="Queue penuh, coba lagi nanti.")

    total_duplicates_rejected += duplicates  # akumulasi total

    return PublishResponse(
        received=len(body.events),
        accepted=accepted,
        duplicates=duplicates,
    )


@app.get("/events")
async def get_events(topic: str = Query(..., description="Nama topic")):
    return store.get_by_topic(topic)


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    return StatsResponse(
        received=consumer.received,
        unique_processed=store.count_unique(),
        duplicate_dropped=total_duplicates_rejected,  # pakai counter publish
        topics=store.all_topics(),
        uptime_seconds=round(time.monotonic() - start_time, 2),
    )


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "ts": datetime.now(timezone.utc).isoformat()})