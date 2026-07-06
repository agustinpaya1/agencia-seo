"""Startup wiring test for backend/app/main.py.

The lifespan must call ``ensure_indexes`` on the connected db before the app
starts serving. Mongo itself is faked: ``AsyncMongoClient`` and
``ensure_indexes`` are monkeypatched on the main module, and entering the
TestClient context runs the real lifespan.
"""

from fastapi.testclient import TestClient

import backend.app.main as main


class FakeMongoClient:
    def __init__(self, *args, **kwargs):
        self.dbs: dict[str, object] = {}

    def __getitem__(self, name: str):
        return self.dbs.setdefault(name, object())

    async def close(self):
        pass


def test_lifespan_ensures_indexes_before_serving(monkeypatch):
    ensured: list = []

    async def fake_ensure_indexes(db):
        ensured.append(db)

    monkeypatch.setattr(main, "AsyncMongoClient", FakeMongoClient)
    monkeypatch.setattr(main, "ensure_indexes", fake_ensure_indexes)

    with TestClient(main.app) as client:
        # Startup already ran: indexes were created before the first request.
        assert len(ensured) == 1
        assert ensured[0] is main.app.state.db
        assert client.get("/health").status_code == 200
