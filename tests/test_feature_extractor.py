"""Tests for feature extractor."""
import pytest
from datetime import datetime, timedelta

from src.zero_day_defense.prediction.feature_engineering import FeatureExtractor
from src.zero_day_defense.prediction.models import CommitSignal
from src.zero_day_defense.prediction.exceptions import InsufficientDataError


@pytest.fixture
def extractor():
    """Create a FeatureExtractor instance."""
    return FeatureExtractor()


@pytest.fixture
def sample_commits():
    """Create sample commit signals."""
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    
    return [
        CommitSignal(
            sha="abc123",
            message="Fix security vulnerability",
            author="Alice",
            timestamp=base_time,  # 10:00 - morning
            files_changed=["src/main.py", "tests/test_main.py"],
            lines_added=50,
            lines_deleted=20,
        ),
        CommitSignal(
            sha="def456",
            message="Update dependencies",
            author="Bob",
            timestamp=base_time + timedelta(hours=5),  # 15:00 - afternoon
            files_changed=["requirements.txt", "config.yaml"],
            lines_added=10,
            lines_deleted=5,
        ),
        CommitSignal(
            sha="ghi789",
            message="Add new feature",
            author="Alice",
            timestamp=base_time + timedelta(days=1, hours=10),  # Next day 20:00 - evening
            files_changed=["src/feature.py", "src/utils.js"],
            lines_added=100,
            lines_deleted=10,
        ),
        CommitSignal(
            sha="jkl012",
            message="Fix tests",
            author="Charlie",
            timestamp=base_time + timedelta(days=2, hours=-8),  # 2 days later 02:00 - night
            files_changed=["tests/test_feature.py"],
            lines_added=30,
            lines_deleted=15,
        ),
    ]


def test_extract_commit_features_empty_list(extractor):
    """Test that empty commit list raises error."""
    with pytest.raises(InsufficientDataError):
        extractor.extract_commit_features([])


def test_extract_commit_features_basic(extractor, sample_commits):
    """Test basic commit feature extraction."""
    features = extractor.extract_commit_features(sample_commits)
    
    # Check that all expected features are present
    expected_features = [
        "commit_frequency",
        "lines_added_avg",
        "lines_deleted_avg",
        "lines_added_total",
        "lines_deleted_total",
        "files_per_commit_avg",
        "author_diversity",
        "author_concentration",
        "commit_hour_morning",
        "commit_hour_afternoon",
        "commit_hour_evening",
        "commit_hour_night",
        "file_type_py",
        "file_type_js",
        "file_type_java",
        "file_type_config",
        "file_type_test",
        "file_type_doc",
    ]
    
    for feature in expected_features:
        assert feature in features, f"Missing feature: {feature}"


def test_commit_frequency(extractor, sample_commits):
    """Test commit frequency calculation."""
    features = extractor.extract_commit_features(sample_commits)
    
    # 4 commits over ~2 days
    assert features["commit_frequency"] > 0
    assert features["commit_frequency"] < 10  # Reasonable upper bound


def test_lines_changed_features(extractor, sample_commits):
    """Test lines added/deleted features."""
    features = extractor.extract_commit_features(sample_commits)
    
    # Total: 50+10+100+30 = 190 added, 20+5+10+15 = 50 deleted
    assert features["lines_added_total"] == 190.0
    assert features["lines_deleted_total"] == 50.0
    assert features["lines_added_avg"] == 190.0 / 4
    assert features["lines_deleted_avg"] == 50.0 / 4


def test_files_per_commit(extractor, sample_commits):
    """Test files per commit calculation."""
    features = extractor.extract_commit_features(sample_commits)
    
    # Total files: 2+2+2+1 = 7, commits: 4
    assert features["files_per_commit_avg"] == 7.0 / 4


def test_author_diversity(extractor, sample_commits):
    """Test author diversity calculation."""
    features = extractor.extract_commit_features(sample_commits)
    
    # 3 unique authors: Alice, Bob, Charlie
    assert features["author_diversity"] == 3.0


def test_author_concentration(extractor, sample_commits):
    """Test author concentration (Gini coefficient)."""
    features = extractor.extract_commit_features(sample_commits)
    
    # Alice: 2 commits, Bob: 1, Charlie: 1
    # Should have some concentration (not perfectly equal)
    assert 0.0 <= features["author_concentration"] <= 1.0


def test_commit_time_patterns(extractor, sample_commits):
    """Test commit time pattern features."""
    features = extractor.extract_commit_features(sample_commits)
    
    # Check that time patterns sum to 1.0
    time_sum = (
        features["commit_hour_morning"] +
        features["commit_hour_afternoon"] +
        features["commit_hour_evening"] +
        features["commit_hour_night"]
    )
    assert abs(time_sum - 1.0) < 0.01
    
    # Sample commits: 10:00 (morning), 15:00 (afternoon), 20:00 (evening), 02:00 (night)
    # Morning (6-12): 1 commit (10:00)
    # Afternoon (12-18): 1 commit (15:00)
    # Evening (18-24): 1 commit (20:00)
    # Night (0-6): 1 commit (02:00)
    assert features["commit_hour_morning"] == 0.25  # 1/4
    assert features["commit_hour_afternoon"] == 0.25  # 1/4
    assert features["commit_hour_evening"] == 0.25  # 1/4
    assert features["commit_hour_night"] == 0.25  # 1/4


def test_file_type_distribution(extractor, sample_commits):
    """Test file type distribution features."""
    features = extractor.extract_commit_features(sample_commits)
    
    # All file types should be between 0 and 1
    file_type_features = [
        "file_type_py",
        "file_type_js",
        "file_type_config",
        "file_type_test",
        "file_type_doc",
    ]
    
    for feature in file_type_features:
        assert 0.0 <= features[feature] <= 1.0
    
    # Check specific file types
    # Total files: main.py, test_main.py, requirements.txt, config.yaml, feature.py, utils.js, test_feature.py = 7
    # Python files: main.py, test_main.py, feature.py, test_feature.py = 4/7
    assert abs(features["file_type_py"] - 4/7) < 0.01
    
    # JS files: utils.js = 1/7
    assert abs(features["file_type_js"] - 1/7) < 0.01
    
    # Config files: config.yaml = 1/7 (requirements.txt is not in the config extensions list)
    assert abs(features["file_type_config"] - 1/7) < 0.01
    
    # Test files: test_main.py, test_feature.py = 2/7
    assert abs(features["file_type_test"] - 2/7) < 0.01


def test_single_commit(extractor):
    """Test feature extraction with single commit."""
    commit = CommitSignal(
        sha="abc123",
        message="Single commit",
        author="Alice",
        timestamp=datetime(2024, 1, 1, 10, 0, 0),
        files_changed=["main.py"],
        lines_added=10,
        lines_deleted=5,
    )
    
    features = extractor.extract_commit_features([commit])
    
    assert features["author_diversity"] == 1.0
    assert features["lines_added_avg"] == 10.0
    assert features["lines_deleted_avg"] == 5.0
    assert features["files_per_commit_avg"] == 1.0


def test_gini_coefficient_perfect_equality(extractor):
    """Test Gini coefficient with perfect equality."""
    # All authors have same number of commits
    gini = extractor._calculate_gini([5, 5, 5, 5])
    assert abs(gini) < 0.01  # Should be close to 0


def test_gini_coefficient_perfect_inequality(extractor):
    """Test Gini coefficient with perfect inequality."""
    # One author has all commits
    gini = extractor._calculate_gini([0, 0, 0, 10])
    assert gini > 0.5  # Should be high


def test_gini_coefficient_empty(extractor):
    """Test Gini coefficient with empty list."""
    gini = extractor._calculate_gini([])
    assert gini == 0.0


def test_no_files_changed(extractor):
    """Test feature extraction when no files are changed."""
    commits = [
        CommitSignal(
            sha="abc123",
            message="Empty commit",
            author="Alice",
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            files_changed=[],
            lines_added=0,
            lines_deleted=0,
        ),
    ]
    
    features = extractor.extract_commit_features(commits)
    
    # All file type features should be 0
    assert features["file_type_py"] == 0.0
    assert features["file_type_js"] == 0.0
    assert features["file_type_config"] == 0.0
    assert features["files_per_commit_avg"] == 0.0


def test_feature_values_are_numeric(extractor, sample_commits):
    """Test that all feature values are numeric."""
    features = extractor.extract_commit_features(sample_commits)
    
    for key, value in features.items():
        assert isinstance(value, (int, float)), f"Feature {key} is not numeric: {type(value)}"
