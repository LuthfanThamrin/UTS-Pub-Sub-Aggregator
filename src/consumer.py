import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class Consumer:
    """
    Background asyncio consumer yang memproses event dari queue secara idempotent.
    Satu event dengan (topic, event_id) yang sama hanya diproses sekali.
    """

    def __init__(self, queue: asyncio.Queue, store):
        self.queue = queue
        self.store = store
        self._task = None

        # Counter sesi ini (direset tiap restart)
        self.received = 0
        self.unique_processed = 0
        self.duplicate_dropped = 0

    def start(self):
        self._task = asyncio.create_task(self._loop(), name="consumer")
        logger.info("Consumer mulai.")

    async def stop(self):
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self):
        while True:
            try:
                event = await self.queue.get()
                await self._process(event)
                self.queue.task_done()
            except asyncio.CancelledError:
                break

    async def _process(self, event: dict):
        self.received += 1
        processed_at = datetime.now(timezone.utc).isoformat()

        saved = self.store.save(
            topic=event["topic"],
            event_id=event["event_id"],
            timestamp=event["timestamp"],
            source=event["source"],
            payload=event.get("payload", {}),
            processed_at=processed_at,
        )

        if saved:
            self.unique_processed += 1
            logger.info("[OK] topic=%s event_id=%s", event["topic"], event["event_id"])
        else:
            self.duplicate_dropped += 1