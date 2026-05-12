from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.tables import Base
from app.main import app


@pytest.fixture
def mock_llm():
    """Mock LLM to avoid real API calls in tests."""
    with patch("app.services.llm.generate_text", new_callable=AsyncMock) as mock:
        mock.return_value = "Mock generated appeal letter with [1] citation."
        yield mock


@pytest.fixture
def mock_rag_init():
    """Skip RAG initialization in tests."""
    with patch("app.services.rag.initialize_rag", new_callable=AsyncMock):
        yield


@pytest.fixture
async def client(mock_rag_init):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
