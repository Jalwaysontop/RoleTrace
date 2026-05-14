import time

# ---------------------------
# IN-MEMORY SESSION STORE
# Keyed by session_id (uuid)
# Max 100 sessions, 1hr TTL
# ---------------------------

_store: dict = {}
_TTL_SECONDS = 3600
_MAX_SESSIONS = 100


def save_session(session_id: str, resume_data: dict):
    if len(_store) >= _MAX_SESSIONS:
        _evict_oldest()

    _store[session_id] = {
        "data": resume_data,
        "created_at": time.time()
    }


def get_session(session_id: str) -> dict | None:
    entry = _store.get(session_id)
    if not entry:
        return None

    if time.time() - entry["created_at"] > _TTL_SECONDS:
        del _store[session_id]
        return None

    return entry["data"]


def _evict_oldest():
    if not _store:
        return
    oldest_key = min(_store, key=lambda k: _store[k]["created_at"])
    del _store[oldest_key]
