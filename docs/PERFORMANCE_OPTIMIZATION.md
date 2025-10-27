# Performance Optimization Strategy

## Problem Analysis

### Current Speed: ~22 minutes/CVE
- Collecting 180-day commit history
- Active projects like Django: ~1000+ commits
- Detailed API call for each commit
- **Result**: 1000 API calls × 1 second wait = 16+ minutes

## Optimization Strategies

### 1. Batch API Calls (Most Effective)

**Problem**: Fetching commit details one by one
```python
for commit in commits:
    detail = get_commit_detail(commit.sha)  # N+1 problem
```

**Solution**: Use GraphQL API
```graphql
query {
  repository(owner: "django", name: "django") {
    object(expression: "main") {
      ... on Commit {
        history(first: 100, since: "2024-01-01") {
          nodes {
            oid
            message
            author {
              name
              email
              date
            }
            additions
            deletions
            changedFiles
          }
        }
      }
    }
  }
}
```

**Expected Improvement**: 1000 calls → 10 calls = **50x faster**

### 2. Parallel Processing

**Problem**: Sequential processing
```python
for cve in cves:
    result = validate_cve(cve)  # One at a time
```

**Solution**: Use multiprocessing
```python
from multiprocessing import Pool

with Pool(processes=4) as pool:
    results = pool.map(validate_cve, cves)
```

**Expected Improvement**: 4x faster with 4 cores

### 3. Caching

**Problem**: Repeated API calls for same data
```python
commits = fetch_commits(repo, since, until)  # Every time
```

**Solution**: Cache results
```python
import diskcache as dc

cache = dc.Cache('cache/')

@cache.memoize(expire=86400)  # 24 hours
def fetch_commits(repo, since, until):
    return api.get_commits(repo, since, until)
```

**Expected Improvement**: Near-instant for cached data

### 4. Incremental Collection

**Problem**: Collecting all data every time
```python
commits = fetch_all_commits(repo)  # Full history
```

**Solution**: Collect only new data
```python
last_collected = get_last_collection_time(repo)
new_commits = fetch_commits_since(repo, last_collected)
```

**Expected Improvement**: 10-100x faster for updates

### 5. Sampling Strategy

**Problem**: Analyzing all 1000+ commits
```python
for commit in all_commits:  # Too many
    analyze(commit)
```

**Solution**: Smart sampling
```python
# Sample commits intelligently
sampled = sample_commits(
    all_commits,
    strategy='stratified',  # By time period
    max_samples=100
)
```

**Expected Improvement**: 10x faster with minimal accuracy loss

## Implementation Priority

### Phase 1: Quick Wins (1-2 days)
1. ✅ Add caching for API calls
2. ✅ Implement commit sampling
3. ✅ Add progress bars

### Phase 2: Major Improvements (3-5 days)
1. ⏳ Switch to GraphQL API
2. ⏳ Add parallel processing
3. ⏳ Implement incremental collection

### Phase 3: Advanced Optimization (1-2 weeks)
1. ⏳ Database indexing
2. ⏳ Distributed processing
3. ⏳ Predictive prefetching

## Expected Results

| Optimization | Current | Target | Improvement |
|--------------|---------|--------|-------------|
| Batch API | 22 min | 2 min | 11x |
| Parallel (4 cores) | 22 min | 5.5 min | 4x |
| Caching | 22 min | <1 sec | 1000x+ |
| Sampling | 22 min | 2 min | 11x |
| **Combined** | **22 min** | **<30 sec** | **40x+** |

## Monitoring

Track performance metrics:
```python
import time
from functools import wraps

def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        print(f"{func.__name__}: {duration:.2f}s")
        return result
    return wrapper

@measure_time
def collect_commits(repo):
    # ... implementation
    pass
```

## Testing

Benchmark with different project sizes:
- Small: <100 commits (fastapi)
- Medium: 100-500 commits (flask)
- Large: 500-1000 commits (requests)
- Very Large: 1000+ commits (django)

## Next Steps

1. Implement GraphQL API client
2. Add caching layer
3. Benchmark improvements
4. Document new performance characteristics
