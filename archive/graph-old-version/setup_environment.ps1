# Windows에서 uv 설치 및 환경 설정 스크립트

Write-Host "uv 설치 및 Text-to-Cypher 환경 설정 시작" -ForegroundColor Green

# uv 설치 (PowerShell 방법)
Write-Host "uv 설치 중..." -ForegroundColor Yellow
try {
    # uv 설치
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    Write-Host "uv 설치 완료" -ForegroundColor Green
} catch {
    Write-Host "uv 설치 실패: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "수동 설치 방법:" -ForegroundColor Yellow
    Write-Host "   1. https://github.com/astral-sh/uv/releases 에서 Windows 바이너리 다운로드" -ForegroundColor Yellow
    Write-Host "   2. PATH에 추가" -ForegroundColor Yellow
    exit 1
}

# uv 버전 확인
Write-Host "uv 버전 확인..." -ForegroundColor Yellow
uv --version

# Python 가상환경 생성
Write-Host "Python 가상환경 생성 중..." -ForegroundColor Yellow
uv venv text2cypher-env

# 가상환경 활성화 (Windows)
Write-Host "가상환경 활성화..." -ForegroundColor Yellow
& "text2cypher-env\Scripts\Activate.ps1"

# 필수 패키지 설치
Write-Host "필수 패키지 설치 중..." -ForegroundColor Yellow
uv pip install datasets transformers requests pandas tqdm pathlib

Write-Host "환경 설정 완료!" -ForegroundColor Green
Write-Host "다음 명령어로 가상환경을 활성화하세요:" -ForegroundColor Yellow
Write-Host "   text2cypher-env\Scripts\Activate.ps1" -ForegroundColor Cyan