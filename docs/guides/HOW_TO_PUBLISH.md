# PyPI 배포 가이드

## 🎯 목표
GitHub Actions를 사용한 자동 배포

## 📝 단계별 가이드

### 1단계: API 토큰 생성 (1분)
1. https://pypi.org/manage/account/token/ 접속
2. "Add API token" 클릭
3. Token name: `rota-github-actions`
4. Scope: "Entire account" 선택
5. "Add token" 클릭
6. **토큰 복사** (한 번만 보임!)

### 2단계: GitHub에 토큰 저장 (1분)
1. https://github.com/susie-Choi/rota/settings/secrets/actions 접속
2. "New repository secret" 클릭
3. Name: `PYPI_API_TOKEN`
4. Secret: 복사한 토큰 붙여넣기
5. "Add secret" 클릭

### 3단계: GitHub Actions 실행 (1분)
1. https://github.com/susie-Choi/rota/actions 접속
2. 왼쪽에서 "Publish to PyPI" 선택
3. "Run workflow" 버튼 클릭
4. "Run workflow" 확인

### 4단계: 완료 확인 (2분)
- Actions 페이지에서 진행 상황 확인
- 성공하면 ✅ 표시
- 실패하면 ❌ 표시 (로그 확인)

## ✅ 배포 확인

```bash
pip install rota
python -c "import rota; print(rota.__version__)"
```

또는 https://pypi.org/project/rota/ 접속

## 🔄 다음 버전 배포

### 방법 1: GitHub Release (자동)
1. GitHub에서 "Releases" → "Create a new release"
2. Tag: `v0.1.1`
3. Title: `Release 0.1.1`
4. Description: 변경사항 작성
5. "Publish release" → 자동 배포!

### 방법 2: 수동 실행
1. `pyproject.toml`에서 버전 변경
2. 커밋 & 푸시
3. Actions → "Publish to PyPI" → "Run workflow"

## 🚨 문제 해결

### "Invalid credentials" 오류
- GitHub Secrets에 토큰이 제대로 저장되었는지 확인
- 토큰이 `pypi-`로 시작하는지 확인

### "Package already exists" 오류
- `pyproject.toml`에서 버전 번호 올리기
- 예: `0.1.0` → `0.1.1`

### "Build failed" 오류
- 로컬에서 `python -m build` 실행해보기
- 에러 메시지 확인

## 💡 팁

- **첫 배포**: 수동으로 "Run workflow" 실행
- **이후 배포**: GitHub Release 생성하면 자동
- **테스트**: TestPyPI로 먼저 테스트 가능

## 📦 현재 상태

- ✅ 패키지 빌드 완료
- ✅ GitHub Actions 설정 완료
- ⏳ PyPI 토큰 설정 필요
- ⏳ 첫 배포 대기 중

## 🎉 완료 후

```bash
# 전 세계 누구나 설치 가능!
pip install rota

# CLI 사용
rota --help
rota predict --repo django/django

# Python에서 사용
from rota import analyze_code_push
result = analyze_code_push("django/django", "abc123")
```
