# GitHub Release 생성 가이드

## 자동 생성 (GitHub CLI 사용)

```bash
# GitHub CLI 설치 확인
gh --version

# Release 생성
gh release create v0.1.1 \
  --title "ROTA v0.1.1 - Initial PyPI Release 🎉" \
  --notes-file .github/RELEASE_NOTES_v0.1.1.md \
  dist/rota-0.1.1-py3-none-any.whl \
  dist/rota-0.1.1.tar.gz
```

## 수동 생성 (웹 브라우저)

### 1단계: Releases 페이지 이동
https://github.com/susie-Choi/rota/releases/new

### 2단계: 정보 입력

**Tag version**: `v0.1.1`
- "Choose a tag" 클릭
- `v0.1.1` 입력
- "Create new tag: v0.1.1 on publish" 선택

**Release title**: `ROTA v0.1.1 - Initial PyPI Release 🎉`

**Description**: `.github/RELEASE_NOTES_v0.1.1.md` 파일 내용 복사 붙여넣기

### 3단계: 파일 첨부 (선택사항)
- `dist/rota-0.1.1-py3-none-any.whl` 드래그 앤 드롭
- `dist/rota-0.1.1.tar.gz` 드래그 앤 드롭

### 4단계: 발행
- "Set as the latest release" 체크
- "Publish release" 클릭

## 완료 후 확인

1. **Release 페이지**: https://github.com/susie-Choi/rota/releases
2. **자동 배포**: GitHub Actions가 자동으로 PyPI에 재배포 (이미 배포되어 있으면 스킵)
3. **알림**: Watch하는 사용자들에게 자동 알림

## 다음 버전 배포 시

1. `pyproject.toml`에서 버전 업데이트
2. `CHANGELOG.md` 업데이트
3. 커밋 & 푸시
4. GitHub Release 생성 → 자동 배포!

---

**현재 상태**: v0.1.1 배포 준비 완료 ✅
