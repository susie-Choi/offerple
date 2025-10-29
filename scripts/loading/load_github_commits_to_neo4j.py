"""
GitHub 커밋 데이터를 Neo4j에 업로드하는 스크립트
컨트리뷰터 영향도 분석을 위한 그래프 구조 생성
"""
import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from datetime import datetime
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubCommitLoader:
    def __init__(self, neo4j_uri=None, neo4j_user=None, neo4j_password=None):
        neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI")
        neo4j_user = neo4j_user or os.getenv("NEO4J_USERNAME", "neo4j")
        neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
    def close(self):
        self.driver.close()
        
    def load_commits_from_file(self, file_path):
        """JSONL 파일에서 커밋 데이터를 읽어서 Neo4j에 업로드"""
        logger.info(f"Loading commits from {file_path}")
        
        with self.driver.session() as session:
            commit_count = 0
            contributor_count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if line.strip():
                        try:
                            commit_data = json.loads(line.strip())
                            self._create_commit_graph(session, commit_data)
                            commit_count += 1
                            
                            if commit_count % 100 == 0:
                                logger.info(f"Processed {commit_count} commits...")
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON decode error at line {line_num}: {e}")
                        except Exception as e:
                            logger.error(f"Error processing line {line_num}: {e}")
                            
        logger.info(f"Loaded {commit_count} commits from {file_path}")
        return commit_count
        
    def _create_commit_graph(self, session, commit_data):
        """개별 커밋 데이터로 그래프 노드와 관계 생성"""
        
        # 커밋 노드 생성
        commit_query = """
        MERGE (c:Commit {sha: $sha})
        SET c.message = $message,
            c.timestamp = $timestamp,
            c.url = $url,
            c.html_url = $html_url,
            c.comment_count = $comment_count,
            c.verified = $verified
        """
        
        # 작성자 노드 생성
        author_query = """
        MERGE (a:Author {login: $author_login})
        SET a.id = $author_id,
            a.node_id = $author_node_id,
            a.avatar_url = $author_avatar_url,
            a.url = $author_url,
            a.html_url = $author_html_url,
            a.type = $author_type,
            a.site_admin = $author_site_admin
        """
        
        # 커밋터 노드 생성
        committer_query = """
        MERGE (cm:Committer {login: $committer_login})
        SET cm.id = $committer_id,
            cm.node_id = $committer_node_id,
            cm.avatar_url = $committer_avatar_url,
            cm.url = $committer_url,
            cm.html_url = $committer_html_url,
            cm.type = $committer_type,
            cm.site_admin = $committer_site_admin
        """
        
        # 저장소 노드 생성
        repo_query = """
        MERGE (r:Repository {full_name: $repo_full_name})
        SET r.name = $repo_name,
            r.owner = $repo_owner
        """
        
        # 관계 생성
        relationships_query = """
        MATCH (c:Commit {sha: $sha})
        MATCH (a:Author {login: $author_login})
        MATCH (cm:Committer {login: $committer_login})
        MATCH (r:Repository {full_name: $repo_full_name})
        
        MERGE (a)-[:AUTHORED]->(c)
        MERGE (cm)-[:COMMITTED]->(c)
        MERGE (c)-[:BELONGS_TO]->(r)
        """
        
        # CVE가 있는 경우 CVE와 연결
        cve_relationship_query = """
        MATCH (c:Commit {sha: $sha})
        MATCH (cve:CVE {id: $cve_id})
        MERGE (c)-[:FIXES]->(cve)
        """
        
        try:
            # 커밋 데이터 추출
            payload = commit_data.get('payload', {})
            commit_info = payload.get('commit', {})
            author_info = payload.get('author', {})
            committer_info = payload.get('committer', {})
            
            # 저장소 정보 추출
            repo_full_name = commit_data.get('repo', 'unknown/unknown')
            repo_parts = repo_full_name.split('/')
            repo_owner = repo_parts[0] if len(repo_parts) > 0 else 'unknown'
            repo_name = repo_parts[1] if len(repo_parts) > 1 else 'unknown'
            
            # 커밋 노드 생성
            session.run(commit_query, {
                'sha': payload.get('sha', ''),
                'message': commit_info.get('message', ''),
                'timestamp': commit_info.get('author', {}).get('date', ''),
                'url': payload.get('url', ''),
                'html_url': payload.get('html_url', ''),
                'comment_count': payload.get('comment_count', 0),
                'verified': payload.get('verification', {}).get('verified', False)
            })
            
            # 작성자 노드 생성
            if author_info:
                session.run(author_query, {
                    'author_login': author_info.get('login', ''),
                    'author_id': author_info.get('id', ''),
                    'author_node_id': author_info.get('node_id', ''),
                    'author_avatar_url': author_info.get('avatar_url', ''),
                    'author_url': author_info.get('url', ''),
                    'author_html_url': author_info.get('html_url', ''),
                    'author_type': author_info.get('type', ''),
                    'author_site_admin': author_info.get('site_admin', False)
                })
            
            # 커밋터 노드 생성
            if committer_info:
                session.run(committer_query, {
                    'committer_login': committer_info.get('login', ''),
                    'committer_id': committer_info.get('id', ''),
                    'committer_node_id': committer_info.get('node_id', ''),
                    'committer_avatar_url': committer_info.get('avatar_url', ''),
                    'committer_url': committer_info.get('url', ''),
                    'committer_html_url': committer_info.get('html_url', ''),
                    'committer_type': committer_info.get('type', ''),
                    'committer_site_admin': committer_info.get('site_admin', False)
                })
            
            # 저장소 노드 생성
            session.run(repo_query, {
                'repo_full_name': repo_full_name,
                'repo_name': repo_name,
                'repo_owner': repo_owner
            })
            
            # 관계 생성
            session.run(relationships_query, {
                'sha': payload.get('sha', ''),
                'author_login': author_info.get('login', '') if author_info else '',
                'committer_login': committer_info.get('login', '') if committer_info else '',
                'repo_full_name': repo_full_name
            })
            
            # CVE 관계 생성 (CVE별 커밋 파일인 경우)
            cve_id = commit_data.get('cve_id')
            if cve_id:
                session.run(cve_relationship_query, {
                    'sha': payload.get('sha', ''),
                    'cve_id': cve_id
                })
                
        except Exception as e:
            logger.error(f"Error creating commit graph: {e}")
            
    def load_all_commit_files(self, data_dir="data/raw/github"):
        """모든 커밋 파일을 순차적으로 로드"""
        data_path = Path(data_dir)
        total_commits = 0
        
        # CVE별 커밋 파일들
        cve_commits_dir = data_path / "commits_by_cve"
        if cve_commits_dir.exists():
            for file_path in cve_commits_dir.glob("*.jsonl"):
                if file_path.stat().st_size > 0:  # 빈 파일 제외
                    commits = self.load_commits_from_file(file_path)
                    total_commits += commits
                    
        # 주요 프로젝트 커밋 파일들
        top_repos_dir = data_path / "commits_smart" / "top_repos"
        if top_repos_dir.exists():
            for file_path in top_repos_dir.glob("*.jsonl"):
                if file_path.stat().st_size > 0:
                    commits = self.load_commits_from_file(file_path)
                    total_commits += commits
                    
        # Python 생태계 커밋 파일들
        python_ecosystem_dir = data_path / "commits_smart" / "python_ecosystem"
        if python_ecosystem_dir.exists():
            for file_path in python_ecosystem_dir.glob("*.jsonl"):
                if file_path.stat().st_size > 0:
                    commits = self.load_commits_from_file(file_path)
                    total_commits += commits
                    
        logger.info(f"Total commits loaded: {total_commits}")
        return total_commits
        
    def create_contributor_metrics(self):
        """기여자별 메트릭 계산 및 저장"""
        logger.info("Creating contributor metrics...")
        
        with self.driver.session() as session:
            # 기여자별 통계 계산
            metrics_query = """
            MATCH (a:Author)-[:AUTHORED]->(c:Commit)-[:BELONGS_TO]->(r:Repository)
            WITH a, 
                 count(c) as total_commits,
                 count(DISTINCT r) as projects_contributed,
                 collect(DISTINCT r.name)[0..5] as sample_projects,
                 min(c.timestamp) as first_commit,
                 max(c.timestamp) as last_commit
                 
            SET a.total_commits = total_commits,
                a.projects_contributed = projects_contributed,
                a.sample_projects = sample_projects,
                a.first_commit = first_commit,
                a.last_commit = last_commit,
                a.experience_months = duration.between(
                    datetime(first_commit), 
                    datetime(last_commit)
                ).months
                
            RETURN a.login, total_commits, projects_contributed, experience_months
            ORDER BY total_commits DESC
            LIMIT 20
            """
            
            result = session.run(metrics_query)
            logger.info("Top contributors by commit count:")
            for record in result:
                logger.info(f"  {record['a.login']}: {record['total_commits']} commits, "
                          f"{record['projects_contributed']} projects, "
                          f"{record['experience_months']} months experience")
                          
    def analyze_security_patterns(self):
        """보안 관련 커밋 패턴 분석"""
        logger.info("Analyzing security patterns...")
        
        with self.driver.session() as session:
            # 보안 관련 키워드가 포함된 커밋 찾기
            security_query = """
            MATCH (a:Author)-[:AUTHORED]->(c:Commit)
            WHERE c.message =~ '(?i).*(security|vulnerability|cve|fix|patch|exploit).*'
            
            WITH a, count(c) as security_commits, 
                 collect(c.message)[0..3] as sample_messages
                 
            SET a.security_commits = security_commits,
                a.security_sample_messages = sample_messages
                
            RETURN a.login, security_commits, sample_messages
            ORDER BY security_commits DESC
            LIMIT 10
            """
            
            result = session.run(security_query)
            logger.info("Top security contributors:")
            for record in result:
                logger.info(f"  {record['a.login']}: {record['security_commits']} security commits")

def main():
    """메인 실행 함수"""
    logger.info("Starting GitHub commit data upload to Neo4j...")
    
    # 환경 변수에서 Neo4j 연결 정보 가져오기
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    loader = GitHubCommitLoader(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        # 모든 커밋 파일 로드
        total_commits = loader.load_all_commit_files()
        
        # 기여자 메트릭 생성
        loader.create_contributor_metrics()
        
        # 보안 패턴 분석
        loader.analyze_security_patterns()
        
        logger.info(f"Successfully loaded {total_commits} commits to Neo4j!")
        
    except Exception as e:
        logger.error(f"Error during data loading: {e}")
    finally:
        loader.close()

if __name__ == "__main__":
    main()
