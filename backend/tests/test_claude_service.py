import pytest
import json
from unittest.mock import MagicMock, patch


@pytest.fixture(autouse=True)
def mock_anthropic(monkeypatch):
    """Prevent real Anthropic client from being instantiated during tests."""
    mock_client = MagicMock()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    with patch("anthropic.Anthropic", return_value=mock_client):
        yield mock_client


def make_mock_response(payload: dict):
    """Helper: build a mock Claude API response from a dict."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps(payload))]
    return mock_response


def make_mock_text_response(text: str):
    """Helper: build a mock Claude API response from plain text."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=text)]
    return mock_response


@pytest.mark.asyncio
async def test_senior_cybersecurity_remote(mock_anthropic):
    mock_anthropic.messages.create.return_value = make_mock_response({
        "is_job_search": True,
        "what": "senior cybersecurity engineer",
        "where": "remote"
    })

    from app.claude_service import ClaudeService
    service = ClaudeService()
    result = await service.parse_job_search_query("find senior cybersecurity jobs in remote")

    assert result["is_job_search"] is True
    assert "cybersecurity" in result["what"].lower()
    assert result["where"].lower() == "remote"


@pytest.mark.asyncio
async def test_react_developer_toronto(mock_anthropic):
    mock_anthropic.messages.create.return_value = make_mock_response({
        "is_job_search": True,
        "what": "React developer",
        "where": "Toronto"
    })

    from app.claude_service import ClaudeService
    service = ClaudeService()
    result = await service.parse_job_search_query("show me React developer roles in Toronto")

    assert result["is_job_search"] is True
    assert "react" in result["what"].lower()
    assert "toronto" in result["where"].lower()


@pytest.mark.asyncio
async def test_non_job_search_message(mock_anthropic):
    mock_anthropic.messages.create.return_value = make_mock_response({
        "is_job_search": False,
        "what": "",
        "where": ""
    })

    from app.claude_service import ClaudeService
    service = ClaudeService()
    result = await service.parse_job_search_query("hello how are you")

    assert result["is_job_search"] is False


@pytest.mark.asyncio
async def test_job_search_no_location(mock_anthropic):
    mock_anthropic.messages.create.return_value = make_mock_response({
        "is_job_search": True,
        "what": "data scientist",
        "where": ""
    })

    from app.claude_service import ClaudeService
    service = ClaudeService()
    result = await service.parse_job_search_query("data science jobs")

    assert result["is_job_search"] is True
    assert "data" in result["what"].lower()
    assert result["where"] == ""


@pytest.mark.asyncio
async def test_response_with_markdown_fences(mock_anthropic):
    """Claude sometimes wraps JSON in markdown code fences - make sure we handle it."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(
        text='```json\n{"is_job_search": true, "what": "Python developer", "where": "Vancouver"}\n```'
    )]
    mock_anthropic.messages.create.return_value = mock_response

    from app.claude_service import ClaudeService
    service = ClaudeService()
    result = await service.parse_job_search_query("Python developer jobs in Vancouver")

    assert result["is_job_search"] is True
    assert "python" in result["what"].lower()
    assert "vancouver" in result["where"].lower()


# --- format_job_results tests ---

SAMPLE_JOBS = [
    {"title": "Senior Cybersecurity Engineer", "company": "Acme Corp", "location": "Remote", "salary_min": 90000, "salary_max": 130000},
    {"title": "Cybersecurity Analyst", "company": "SecureIT", "location": "Remote", "salary_min": 70000, "salary_max": 100000},
    {"title": "Information Security Manager", "company": "BigBank", "location": "Remote", "salary_min": 110000, "salary_max": 150000},
]


@pytest.mark.asyncio
async def test_format_job_results_returns_string(mock_anthropic):
    """format_job_results should return a non-empty string."""
    mock_anthropic.messages.create.return_value = make_mock_text_response(
        "Great news! I found 45 cybersecurity roles available remotely across Canada. "
        "Salaries range from $70,000 to $150,000, with opportunities at both startups and established firms. "
        "Good luck with your search!"
    )

    from app.claude_service import ClaudeService
    service = ClaudeService()
    result = await service.format_job_results(
        what="senior cybersecurity",
        where="remote",
        jobs=SAMPLE_JOBS,
        total_count=45
    )

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_format_job_results_no_location(mock_anthropic):
    """format_job_results should work when no location is provided."""
    mock_anthropic.messages.create.return_value = make_mock_text_response(
        "I found 20 data scientist positions across Canada. "
        "Roles span various industries with competitive salaries. Good luck!"
    )

    from app.claude_service import ClaudeService
    service = ClaudeService()
    result = await service.format_job_results(
        what="data scientist",
        where="",
        jobs=SAMPLE_JOBS,
        total_count=20
    )

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_format_job_results_empty_jobs(mock_anthropic):
    """format_job_results should handle an empty jobs list gracefully."""
    mock_anthropic.messages.create.return_value = make_mock_text_response(
        "I found 0 results for that search. Try broadening your keywords!"
    )

    from app.claude_service import ClaudeService
    service = ClaudeService()
    result = await service.format_job_results(
        what="quantum physicist",
        where="Yellowknife",
        jobs=[],
        total_count=0
    )

    assert isinstance(result, str)
    assert len(result) > 0
