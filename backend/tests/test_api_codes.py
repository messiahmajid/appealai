import pytest


@pytest.mark.asyncio
async def test_search_cpt_returns_results(client):
    resp = await client.get("/api/codes/cpt", params={"q": "knee"})
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert len(data["results"]) > 0
    assert all("code" in r and "description" in r and "category" in r for r in data["results"])


@pytest.mark.asyncio
async def test_search_cpt_empty_query(client):
    resp = await client.get("/api/codes/cpt", params={"q": ""})
    assert resp.status_code == 200
    assert resp.json()["results"] == []


@pytest.mark.asyncio
async def test_search_cpt_short_query(client):
    resp = await client.get("/api/codes/cpt", params={"q": "k"})
    assert resp.status_code == 200
    assert resp.json()["results"] == []


@pytest.mark.asyncio
async def test_search_icd10_returns_results(client):
    resp = await client.get("/api/codes/icd10", params={"q": "osteoarthritis"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0


@pytest.mark.asyncio
async def test_search_icd10_by_code(client):
    resp = await client.get("/api/codes/icd10", params={"q": "M17"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0
    assert any("M17" in r["code"] for r in data["results"])


@pytest.mark.asyncio
async def test_search_cpt_by_code(client):
    resp = await client.get("/api/codes/cpt", params={"q": "27447"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) > 0
    assert data["results"][0]["code"] == "27447"


@pytest.mark.asyncio
async def test_search_cpt_no_match(client):
    resp = await client.get("/api/codes/cpt", params={"q": "zzzzxyz"})
    assert resp.status_code == 200
    assert resp.json()["results"] == []
