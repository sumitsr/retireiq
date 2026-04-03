import json
import logging
import queue
import time
from threading import Lock

logger = logging.getLogger(__name__)


class SSEService:
    """
    The Stream Dispatcher (The Broadcaster).

    Manages real-time event distribution for RetireIQ sessions via
    Server-Sent Events (SSE).  Thread-safe via a shared Lock.
    """

    QUEUE_MAX_SIZE = 100
    HEARTBEAT_INTERVAL_S = 20  # seconds before a keep-alive ping is sent

    def __init__(self):
        # session_id → list[queue.Queue]
        self.listeners: dict = {}
        self.lock = Lock()
        logger.debug("[SSEService] Initialised.")

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def subscribe(self, session_id):
        """
        Creates a listener queue for a session and yields SSE-formatted events.

        The generator blocks until an event arrives or the heartbeat interval
        expires.  On client disconnect (GeneratorExit), the queue is removed.
        """
        q = queue.Queue(maxsize=self.QUEUE_MAX_SIZE)
        self._register_listener(session_id, q)

        logger.info("[SSEService] Client subscribed | session=%s total_listeners=%d",
                    session_id, len(self.listeners.get(session_id, [])))

        try:
            yield self._format_sse("connected", {"status": "streaming", "session_id": session_id})
            yield from self._event_loop(session_id, q)
        except GeneratorExit:
            self._deregister_listener(session_id, q)
            logger.info("[SSEService] Client disconnected | session=%s", session_id)

    def publish(self, session_id, event, data):
        """
        Broadcasts an event to all subscribers of the given session.
        Events that exceed queue capacity are silently dropped.
        """
        with self.lock:
            listeners = self.listeners.get(session_id, [])

        if not listeners:
            logger.debug("[SSEService] Publish called with no active listeners | session=%s event=%s",
                         session_id, event)
            return

        dropped = 0
        for q in listeners:
            try:
                q.put_nowait({"event": event, "data": data})
            except queue.Full:
                dropped += 1
                logger.warning("[SSEService] Queue full — event dropped | session=%s event=%s",
                               session_id, event)

        if dropped == 0:
            logger.debug("[SSEService] Event published | session=%s event=%s listeners=%d",
                         session_id, event, len(listeners))

    # -----------------------------------------------------------------------
    # Private — Listener lifecycle
    # -----------------------------------------------------------------------

    def _register_listener(self, session_id, q):
        """Adds a new queue to the listener registry for a session."""
        with self.lock:
            if session_id not in self.listeners:
                self.listeners[session_id] = []
            self.listeners[session_id].append(q)

    def _deregister_listener(self, session_id, q):
        """Removes a queue and cleans up empty session entries."""
        with self.lock:
            if session_id in self.listeners:
                try:
                    self.listeners[session_id].remove(q)
                except ValueError:
                    pass  # Already removed
                if not self.listeners[session_id]:
                    del self.listeners[session_id]
                    logger.debug("[SSEService] Session cleaned up | session=%s", session_id)

    # -----------------------------------------------------------------------
    # Private — Event loop
    # -----------------------------------------------------------------------

    def _event_loop(self, session_id, q):
        """
        Yields formatted SSE events from the queue.
        Sends a heartbeat ping every HEARTBEAT_INTERVAL_S seconds to
        prevent proxy/load-balancer idle-connection timeouts.
        """
        while True:
            try:
                event_data = q.get(timeout=self.HEARTBEAT_INTERVAL_S)
                logger.debug("[SSEService] Yielding event | session=%s event=%s",
                             session_id, event_data.get("event"))
                yield self._format_sse(event_data["event"], event_data["data"])
            except queue.Empty:
                logger.debug("[SSEService] Heartbeat ping | session=%s", session_id)
                yield self._format_sse("ping", {"time": time.time()})

    # -----------------------------------------------------------------------
    # Private — Formatting
    # -----------------------------------------------------------------------

    def _format_sse(self, event, data):
        """Returns a correctly formatted SSE wire-format string."""
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# Single global instance — shared across all request threads
sse_service = SSEService()
