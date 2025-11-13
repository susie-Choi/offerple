#!/bin/bash

# WSL Ubuntu 환경에서 Zero-Day Defense 프로젝트 설정 스크립트

echo "=== WSL Ubuntu 환경 설정 시작 ==="

# 시스템 업데이트
echo "시스템 패키지 업데이트 중..."
sudo apt update && sudo apt upgrade -y

# Python 및 필수 도구 설치
echo "Python 및 개발 도구 설치 중..."
sudo apt install -y python3 python3-pip python3-venv git curl wget

# uv 설치 (Python 패키지 매니저)
echo "uv 설치 중..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 프로젝트 디렉토리로 이동 (Windows 파일시스템 마운트 지점)
# WSL에서 Windows 파일에 접근: /mnt/c/Users/[사용자명]/프로젝트경로
echo "현재 디렉토리: $(pwd)"

# Python 가상환경 생성
echo "Python 가상환경 생성 중..."
python3 -m venv zero-day-defense-env
source zero-day-defense-env/bin/activate

# 또는 uv 사용
# uv venv zero-day-defense-env
# source zero-day-defense-env/bin/activate

# requirements.txt 설치
if [ -f "requirements.txt" ]; then
    echo "Python 패키지 설치 중..."
    pip install -r requirements.txt
    # 또는: uv pip install -r requirements.txt
else
    echo "requirements.txt 파일을 찾을 수 없습니다."
fi

# Docker 설치 (Neo4j 등을 위해)
echo "Docker 설치 중..."
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Docker Compose 설치
echo "Docker Compose 설치 중..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

echo "=== 설정 완료 ==="
echo "다음 명령어로 가상환경을 활성화하세요:"
echo "source zero-day-defense-env/bin/activate"
echo ""
echo "Docker를 사용하려면 다음 명령어를 실행하세요:"
echo "newgrp docker"
echo ""
echo "또는 시스템을 재시작하세요."