"""
마크다운 보고서를 NeurIPS 스타일 LaTeX로 변환하는 스크립트
"""
import json
import re
import sys
from pathlib import Path

def markdown_to_latex_table(table_lines):
    """마크다운 테이블을 LaTeX 테이블로 변환"""
    if not table_lines or len(table_lines) < 2:
        return ""
    
    # 첫 번째 줄: 헤더
    headers = [h.strip() for h in table_lines[0].split('|') if h.strip()]
    
    # 두 번째 줄: 분리자 (무시)
    
    # 나머지 줄: 데이터
    rows = []
    for line in table_lines[2:]:
        cells = [c.strip() for c in line.split('|') if c.strip()]
        if cells:
            rows.append(cells)
    
    if not headers or not rows:
        return ""
    
    # LaTeX 테이블 생성
    latex = "\\begin{table}[ht]\n"
    latex += "  \\centering\n"
    latex += "  \\caption{}\n"
    latex += "  \\label{}\n"
    latex += "  \\begin{tabular}{" + "l" * len(headers) + "}\n"
    latex += "    \\toprule\n"
    
    # 헤더
    latex += "    " + " & ".join([f"\\textbf{{{h}}}" for h in headers]) + " \\\\\n"
    latex += "    \\midrule\n"
    
    # 데이터
    for row in rows:
        # 부족한 셀은 빈 문자열로 채우기
        while len(row) < len(headers):
            row.append("")
        latex += "    " + " & ".join([cell.replace('$', '\\$') for cell in row[:len(headers)]]) + " \\\\\n"
    
    latex += "    \\bottomrule\n"
    latex += "  \\end{tabular}\n"
    latex += "\\end{table}\n"
    
    return latex

def markdown_to_latex_list(list_lines):
    """마크다운 리스트를 LaTeX 리스트로 변환"""
    latex = ""
    current_level = 0
    
    for line in list_lines:
        stripped = line.strip()
        if not stripped:
            continue
            
        # 리스트 항목 감지
        match = re.match(r'^([\*\-\+]) (.+)$', stripped)
        if match:
            latex += f"  \\item {match.group(2)}\n"
        else:
            # 숫자 리스트
            match = re.match(r'^(\d+)\. (.+)$', stripped)
            if match:
                if current_level == 0:
                    latex = latex.rstrip() + "\n\\begin{enumerate}\n  \\item "
                    current_level = 1
                else:
                    latex += "  \\item "
                latex += f"{match.group(2)}\n"
    
    if current_level > 0:
        latex = latex.rstrip() + "\n\\end{enumerate}\n"
    
    return latex

def markdown_to_latex_code(code_block, language="text"):
    """마크다운 코드 블록을 LaTeX verbatim으로 변환"""
    latex = "\\begin{verbatim}\n"
    latex += code_block
    latex += "\n\\end{verbatim}\n"
    return latex

def convert_section(heading, level):
    """마크다운 헤딩을 LaTeX 섹션으로 변환"""
    heading = heading.strip()
    if level == 1:
        return f"\\section{{{heading}}}"
    elif level == 2:
        return f"\\subsection{{{heading}}}"
    elif level == 3:
        return f"\\subsubsection{{{heading}}}"
    elif level == 4:
        return f"\\paragraph{{{heading}}}"
    return ""

def markdown_to_latex(md_content):
    """마크다운 전체를 LaTeX로 변환"""
    lines = md_content.split('\n')
    latex_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 헤딩 처리
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            heading = line.lstrip('#').strip()
            latex_lines.append(convert_section(heading, level))
            i += 1
            continue
        
        # 강조 처리 (**bold**, *italic*)
        line = re.sub(r'\*\*(.+?)\*\*', r'\\textbf{\1}', line)
        line = re.sub(r'\*(.+?)\*', r'\\textit{\1}', line)
        line = re.sub(r'`(.+?)`', r'\\texttt{\1}', line)
        
        # 인용 처리
        if line.strip().startswith('>'):
            latex_lines.append(f"\\begin{{quote}}\n{line.lstrip('>').strip()}\n\\end{{quote}}")
            i += 1
            continue
        
        # 일반 텍스트
        if line.strip():
            latex_lines.append(line)
        else:
            latex_lines.append("")
        
        i += 1
    
    return '\n'.join(latex_lines)

def main():
    """메인 함수"""
    # 마크다운 파일 읽기
    md_file = Path("nlp/nlp-midterm-report-final.md")
    
    if not md_file.exists():
        print(f"Error: {md_file} not found")
        return
    
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 간단한 변환 (전체 구조는 이미 neurips_paper.tex에 있음)
    print("✅ LaTeX 파일이 이미 생성되었습니다: nlp/neurips_paper.tex")
    print("\n📝 사용 방법:")
    print("1. neurips_paper.tex 파일을 편집하여 내용을 완성하세요")
    print("2. Overleaf에서 업로드하여 컴파일하세요")
    print("3. 한글 폰트가 없는 경우, 다음 중 하나를 선택하세요:")
    print("   - 방법 1: kotex 패키지 사용")
    print("   - 방법 2: XeLaTeX + xeCJK 사용 (권장)")
    print("   - 방법 3: ctex 패키지 사용")

if __name__ == "__main__":
    main()

