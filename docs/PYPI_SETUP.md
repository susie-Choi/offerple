# PyPI 배포 설정 가이드

## 1. PyPI 계정 확인

### 계정이 있는 경우
- PyPI: https://pypi.org/
- TestPyPI: https://test.pypi.org/

### API 토큰 생성
1. PyPI 로그인
2. Account Settings → API tokens
3. "Add API token" 클릭
4. Scope: "Entire account" 또는 특정 프로젝트
5. 토큰 복사 (한 번만 표시됨!)

## 2. 인증 설정 방법

### 방법 1: 환경 변수 (추천)
```bash
# Windows PowerShell
$env:TWINE_USERNAME = "__token__"
$env:TWINE_PASSWORD = "pypi-YOUR_TOKEN_HERE"

# Windows CMD
set TWINE_USERNAME=__token__
set TWINE_PASSWORD=pypi-YOUR_TOKEN_HERE

# Linux/Mac
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YOUR_TOKEN_HERE
```

### 방법 2: .pypirc 파일
```bash
# Windows
notepad %USERPROFILE%\.pypirc

# Linux/Mac
nano ~/.pypirc
```

파일 내용:
```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_API_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR_TEST_API_TOKEN_HERE
```

### 방법 3: keyring 사용 (가장 안전)
```bash
# 토큰 저장
python -m keyring set https://upload.pypi.org/legacy/ __token__
# 프롬프트에서 토큰 입력

# TestPyPI
python -m keyring set https://test.pypi.org/legacy/ __token__
```

## 3. 연동 테스트

### 현재 설정 확인
```bash
# twine 설정 확인
python -m twine check dist/*

# 업로드 테스트 (실제 업로드 안 함)
python -m twine upload --repository testpypi dist/* --verbose
```

### 패키지 이름 확인
```bash
# 'rota' 이름이 사용 가능한지 확인
pip search rota
# 또는 https://pypi.org/project/rota/ 접속
```

## 4. 배포 프로세스

### Step 1: 패키지 빌드
```bash
# 이전 빌드 정리
python scripts/publish_to_pypi.py --skip-check --skip-upload

# 또는 수동으로
python -m build
```

### Step 2: 패키지 검증
```bash
python -m twine check dist/*
```

### Step 3: TestPyPI에 먼저 업로드 (권장)
```bash
python -m twine upload --repository testpypi dist/*
```

### Step 4: TestPyPI에서 설치 테스트
```bash
pip install -i https://test.pypi.org/simple/ rota
```

### Step 5: 실제 PyPI에 업로드
```bash
python -m twine upload dist/*
```

## 5. 자동화 스크립트 사용

### TestPyPI 업로드
```bash
python scripts/publish_to_pypi.py --test
```

### 실제 PyPI 업로드
```bash
python scripts/publish_to_pypi.py
```

## 6. 문제 해결

### "Package already exists" 오류
- 버전 번호를 올려야 함
- `pyproject.toml`에서 `version = "0.1.1"` 등으로 변경

### "Invalid credentials" 오류
- API 토큰 확인
- `__token__`을 username으로 사용했는지 확인
- 토큰이 `pypi-`로 시작하는지 확인

### "Package name not available" 오류
- 다른 이름 사용 필요
- 현재: `rota`
- 대안: `rota-security`, `rota-ai`, `py-rota` 등

## 7. 버전 관리

### Semantic Versioning
- `0.1.0`: 초기 릴리즈
- `0.1.1`: 버그 수정
- `0.2.0`: 새 기능 추가
- `1.0.0`: 안정 버전

### 버전 업데이트
```bash
# pyproject.toml 수정
version = "0.1.1"

# 태그 생성
git tag v0.1.1
git push origin v0.1.1
```

## 8. 배포 후 확인

### PyPI 페이지 확인
- https://pypi.org/project/rota/

### 설치 테스트
```bash
pip install rota
python -c "import rota; print(rota.__version__)"
```

### CLI 테스트
```bash
rota --help
rota predict --repo django/django
```

## 9. 보안 주의사항

⚠️ **절대 Git에 커밋하지 말 것:**
- `.pypirc` 파일
- API 토큰
- 비밀번호

✅ **`.gitignore`에 추가:**
```
.pypirc
*.pypirc
```

## 10. 다음 단계

배포 후:
1. GitHub Release 생성
2. README 업데이트 (설치 방법)
3. 문서 사이트 업데이트
4. 소셜 미디어 공지
5. 커뮤니티 공유
