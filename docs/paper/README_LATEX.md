# NeurIPS 스타일 한글 보고서 작성 가이드

## 📁 파일 구조

```
nlp/
├── neurips_paper.tex          # 메인 LaTeX 파일
├── neurips_2024.sty           # NeurIPS 스타일 파일
├── nlp-midterm-report-final.md # 원본 마크다운
├── report_data.json            # 데이터
└── images/                     # 이미지 폴더
    ├── cve_cwe_network.jpg
    ├── database_schema.jpg
    ├── log4shell_graph.jpg
    ├── severity_distribution.jpg
    ├── supply_chain.jpg
    └── top_cwes.jpg
```

## 🚀 사용 방법

### 방법 1: Overleaf 사용 (권장)

1. **Overleaf 접속**: https://www.overleaf.com
2. **프로젝트 생성**: New Project → Upload Project
3. **파일 업로드**:
   - `neurips_paper.tex` (메인 파일)
   - `neurips_2024.sty` (스타일 파일)
   - `images/` 폴더 전체
4. **컴파일러 설정**:
   - 컴파일러: **XeLaTeX** (한글 지원)
   - 또는 **pdfLaTeX** (kotex 사용 시)
5. **한글 폰트**:
   - Overleaf에서 기본 한글 폰트를 지원합니다
   - 필요시 나눔고딕 등을 업로드하여 사용 가능

### 방법 2: 로컬에서 컴파일

#### 필수 패키지 설치 (macOS)

```bash
# MacTeX 설치
brew install --cask mactex

# XeLaTeX로 컴파일
xelatex neurips_paper.tex
xelatex neurips_paper.tex  # 두 번 실행 (참조 해결)
```

#### 필수 패키지 설치 (Windows)

1. MiKTeX 또는 TeX Live 설치
2. Command Prompt에서:

```powershell
cd nlp
xelatex neurips_paper.tex
xelatex neurips_paper.tex  # 두 번 실행
```

#### 필수 패키지 설치 (Linux)

```bash
# TeX Live 설치
sudo apt-get install texlive-xetex texlive-lang-cjk

# 컴파일
cd nlp
xelatex neurips_paper.tex
xelatex neurips_paper.tex  # 두 번 실행
```

## ✏️ 한글 지원 옵션

### 옵션 1: xeCJK 사용 (권장) - 현재 설정

```latex
\usepackage{fontspec}
\usepackage{xeCJK}
\setCJKmainfont{NanumGothic}[Path=fonts/, Extension=.ttf]
```

**필요한 작업**: `fonts/` 폴더에 나눔고딕 폰트 파일 업로드
- [나눔고딕 다운로드](https://hangeul.naver.com/)

### 옵션 2: kotex 사용 (Overleaf 기본)

```latex
\usepackage[utf8]{inputenc}
\usepackage{kotex}
```

`neurips_paper.tex` 파일 상단에서 주석을 해제하면 됩니다.

### 옵션 3: pdfLaTeX + ctex (중국어/한글 공용)

```latex
\usepackage{ctex}
```

## 📝 내용 편집

### 이미지 삽입

```latex
\begin{figure}[ht]
  \centering
  \includegraphics[width=0.8\textwidth]{images/cve_cwe_network.jpg}
  \caption{CVE-CWE 네트워크 그래프}
  \label{fig:cve-cwe}
\end{figure}
```

### 표 삽입 (이미 포함됨)

```latex
\begin{table}[ht]
  \centering
  \caption{표 제목}
  \label{tab:label}
  \begin{tabular}{ll}
    \toprule
    항목1 & 항목2 \\
    \midrule
    값1 & 값2 \\
    \bottomrule
  \end{tabular}
\end{table}
```

### 수식 삽입

```latex
\begin{equation}
E = mc^2
\end{equation}
```

### 리스트

```latex
\begin{itemize}
  \item 항목 1
  \item 항목 2
\end{itemize}

\begin{enumerate}
  \item 첫 번째
  \item 두 번째
\end{enumerate}
```

## 🎨 스타일링

### 색상 변경

```latex
\textcolor{red}{경고 텍스트}
\textcolor{blue}{정보 텍스트}
```

### 강조

```latex
\textbf{굵은 글씨}
\textit{기울임}
\texttt{코드 폰트}
```

## 📊 표와 그림 자동 생성 스크립트

```bash
# Python 데이터로부터 표 생성
cd nlp
python convert_final_report.py

# 또는 직접 편집
python generate_report_data.py
```

## ⚠️ 주의사항

1. **컴파일러**: 반드시 **XeLaTeX** 또는 **pdfLaTeX**을 사용하세요
2. **한글 폰트**: 폰트 경로가 올바른지 확인하세요
3. **이미지**: 모든 이미지를 `images/` 폴더에 배치하세요
4. **두 번 컴파일**: 참조(표, 그림 등)를 위해 두 번 컴파일해야 합니다
5. **인코딩**: 파일은 **UTF-8**로 저장되어야 합니다

## 📦 파일 업로드 체크리스트 (Overleaf)

- [ ] neurips_paper.tex
- [ ] neurips_2024.sty
- [ ] images/cve_cwe_network.jpg
- [ ] images/database_schema.jpg
- [ ] images/log4shell_graph.jpg
- [ ] images/severity_distribution.jpg
- [ ] images/supply_chain.jpg
- [ ] images/top_cwes.jpg
- [ ] fonts/ (한글 폰트, 옵션)

## 🔧 트러블슈팅

### 한글이 깨져요
- XeLaTeX을 사용하고 있는지 확인
- 한글 폰트 경로가 올바른지 확인
- `fonts/` 폴더에 폰트 파일이 있는지 확인

### 그림이 안 나와요
- 이미지 경로가 올바른지 확인 (`images/` 폴더 내)
- 파일 확장자가 대소문자 일치하는지 확인 (일부 시스템은 대소문자 구분)
- LaTeX 컴파일 에러 메시지 확인

### 표가 이상해요
- `\toprule`, `\midrule`, `\bottomrule` 사용 확인
- 셀 개수가 헤더와 일치하는지 확인
- `&`로 구분했는지 확인

## 💡 Tips

1. **증분 컴파일**: Overleaf는 자동으로 증분 컴파일을 수행합니다
2. **Live Preview**: Overleaf에서 실시간으로 미리보기 가능
3. **협업**: Overleaf는 Git 연동이 가능합니다
4. **버전 관리**: 파일 변경 이력이 자동으로 저장됩니다

## 📞 추가 도움

- NeurIPS 공식 스타일: https://neurips.cc/Conferences/2024/PaperInformation/StyleFiles
- Overleaf 문서: https://www.overleaf.com/learn
- LaTeX 한글 가이드: https://www.overleaf.com/learn/latex/Chinese

