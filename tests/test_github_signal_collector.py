"""Tests for GitHub signal collector."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.zero_day_defense.prediction.signal_collectors import GitHubSignalCollector
from src.zero_day_defense.prediction.models import CommitSignal
from src.zero_day_defense.prediction.exceptions import (
    TimeRangeError,
    RepositoryNotFoundError,
    GitHubRateLimitError,
)


@pytest.fixture
def collector():
    """Create a GitHubSignalCollector instance."""
    return GitHubSignalCollector(github_token="test_token")


@pytest.fixture
def mock_commit_response():
    """Mock GitHub API commit response."""
    return [
        {
            "sha": "abc123",
            "commit": {
                "message": "Fix security vulnerability",
                "author": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "date": "2024-01-15T10:00:00Z",
                },
            },
            "html_url": "https://github.com/owner/repo/commit/abc123",
        },
        {
            "sha": "def456",
            "commit": {
                "message": "Update dependencies",
                "author": {
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "date": "2024-01-16T14:30:00Z",
                },
            },
            "html_url": "https://github.com/owner/repo/commit/def456",
        },
    ]


@pytest.fixture
def mock_commit_detail():
    """Mock GitHub API commit detail response."""
    return {
        "files": [
            {"filename": "src/main.py"},
            {"filename": "tests/test_main.py"},
        ],
        "stats": {
            "additions": 50,
            "deletions": 20,
        },
    }


def test_collector_initialization():
    """Test GitHubSignalCollector initialization."""
    collector = GitHubSignalCollector(github_token="test_token")
    assert collector.source_name == "github_signals"
    assert collector.github_token == "test_token"
    assert "Authorization" in collector.session.headers


def test_collect_commit_history_invalid_time_range(collector):
    """Test that invalid time range raises error."""
    since = datetime(2024, 1, 20)
    until = datetime(2024, 1, 10)
    
    with pytest.raises(TimeRangeError):
        collector.collect_commit_history("owner/repo", since, until)


@patch("src.zero_day_defense.prediction.signal_collectors.github_signals.time.sleep")
def test_collect_commit_history_success(mock_sleep, collector, mock_commit_response, mock_commit_detail):
    """Test successful commit history collection."""
    since = datetime(2024, 1, 1)
    until = datetime(2024, 1, 31)
    
    # Mock the API responses
    with patch.object(collector, "_request") as mock_request:
        # First call returns commits list
        mock_response = Mock()
        mock_response.json.return_value = mock_commit_response
        mock_response.status_code = 200
        
        # Subsequent calls return commit details
        mock_detail_response = Mock()
        mock_detail_response.json.return_value = mock_commit_detail
        mock_detail_response.status_code = 200
        
        # Setup side effects: commits list, then details for each commit, then empty list
        mock_request.side_effect = [
            mock_response,  # First page of commits
            mock_detail_response,  # Detail for first commit
            mock_detail_response,  # Detail for second commit
            Mock(json=lambda: []),  # Empty list for next page
        ]
        
        commits = collector.collect_commit_history("owner/repo", since, until)
    
    assert len(commits) == 2
    assert isinstance(commits[0], CommitSignal)
    assert commits[0].sha == "abc123"
    assert commits[0].message == "Fix security vulnerability"
    assert commits[0].author == "John Doe"
    assert commits[0].lines_added == 50
    assert commits[0].lines_deleted == 20
    assert len(commits[0].files_changed) == 2


@patch("src.zero_day_defense.prediction.signal_collectors.github_signals.time.sleep")
def test_collect_commit_history_repository_not_found(mock_sleep, collector):
    """Test handling of repository not found error."""
    since = datetime(2024, 1, 1)
    until = datetime(2024, 1, 31)
    
    with patch.object(collector, "_request") as mock_request:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.ok = False
        mock_response.text = "Not Found"
        mock_request.side_effect = Exception("404")
        
        with pytest.raises(Exception):
            collector.collect_commit_history("owner/nonexistent", since, until)


def test_handle_rate_limit_exceeded(collector):
    """Test rate limit handling."""
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.headers = {
        "X-RateLimit-Remaining": "0",
        "X-RateLimit-Reset": str(int(datetime.now().timestamp()) + 3600),
    }
    
    with pytest.raises(GitHubRateLimitError):
        collector._handle_rate_limit(mock_response)


def test_handle_repository_not_found(collector):
    """Test repository not found handling."""
    mock_response = Mock()
    mock_response.status_code = 404
    
    with pytest.raises(RepositoryNotFoundError):
        collector._handle_rate_limit(mock_response)


@patch("src.zero_day_defense.prediction.signal_collectors.github_signals.time.sleep")
def test_get_commit_detail_success(mock_sleep, collector, mock_commit_detail):
    """Test getting commit details."""
    with patch.object(collector, "_request") as mock_request:
        mock_response = Mock()
        mock_response.json.return_value = mock_commit_detail
        mock_request.return_value = mock_response
        
        detail = collector._get_commit_detail("owner/repo", "abc123")
    
    assert len(detail["files_changed"]) == 2
    assert detail["lines_added"] == 50
    assert detail["lines_deleted"] == 20


@patch("src.zero_day_defense.prediction.signal_collectors.github_signals.time.sleep")
def test_get_commit_detail_failure(mock_sleep, collector):
    """Test handling of commit detail fetch failure."""
    with patch.object(collector, "_request") as mock_request:
        mock_request.side_effect = Exception("API Error")
        
        detail = collector._get_commit_detail("owner/repo", "abc123")
    
    # Should return empty data on failure
    assert detail["files_changed"] == []
    assert detail["lines_added"] == 0
    assert detail["lines_deleted"] == 0


@patch("src.zero_day_defense.prediction.signal_collectors.github_signals.time.sleep")
def test_collect_commit_history_pagination(mock_sleep, collector, mock_commit_response):
    """Test pagination handling."""
    since = datetime(2024, 1, 1)
    until = datetime(2024, 1, 31)
    
    with patch.object(collector, "_request") as mock_request:
        # First page returns full 100 items (simulated by returning 2 items)
        mock_response1 = Mock()
        mock_response1.json.return_value = mock_commit_response
        mock_response1.status_code = 200
        
        # Mock commit details
        mock_detail = Mock()
        mock_detail.json.return_value = {"files": [], "stats": {"additions": 0, "deletions": 0}}
        
        # Second page returns empty
        mock_response2 = Mock()
        mock_response2.json.return_value = []
        
        mock_request.side_effect = [
            mock_response1,  # First page
            mock_detail,  # Detail for commit 1
            mock_detail,  # Detail for commit 2
            mock_response2,  # Second page (empty)
        ]
        
        commits = collector.collect_commit_history("owner/repo", since, until)
    
    assert len(commits) == 2
