"""
컨트리뷰터 영향도 분석 스크립트
Neo4j 그래프 데이터를 활용한 심층 분석
"""
import json
import os
from pathlib import Path
from neo4j import GraphDatabase
from datetime import datetime, timedelta
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from collections import defaultdict, Counter

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContributorInfluenceAnalyzer:
    def __init__(self, neo4j_uri="neo4j+s://26e236b3.databases.neo4j.io", neo4j_user="neo4j", neo4j_password="yc-TW0XnNO3rV9u0mSR59BVHxlyeJjTC8ngO3QhbkVw"):
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
    def close(self):
        self.driver.close()
        
    def analyze_contributor_experience_patterns(self):
        """기여자 경험 패턴 분석"""
        logger.info("Analyzing contributor experience patterns...")
        
        with self.driver.session() as session:
            # 경험별 커밋 패턴 분석
            experience_query = """
            MATCH (a:Author)-[:AUTHORED]->(c:Commit)-[:BELONGS_TO]->(r:Repository)
            WHERE a.experience_months IS NOT NULL
            
            WITH a, 
                 a.experience_months as experience,
                 a.total_commits as total_commits,
                 a.projects_contributed as projects,
                 a.security_commits as security_commits
                 
            WHERE total_commits >= 5  // 최소 5개 커밋 이상
            
            RETURN experience, 
                   avg(total_commits) as avg_commits,
                   avg(projects) as avg_projects,
                   avg(security_commits) as avg_security_commits,
                   count(a) as contributor_count
            ORDER BY experience
            """
            
            result = session.run(experience_query)
            
            experience_data = []
            for record in result:
                experience_data.append({
                    'experience_months': record['experience'],
                    'avg_commits': record['avg_commits'],
                    'avg_projects': record['avg_projects'],
                    'avg_security_commits': record['avg_security_commits'] or 0,
                    'contributor_count': record['contributor_count']
                })
                
            return experience_data
            
    def analyze_security_vulnerability_patterns(self):
        """보안 취약점 도입 패턴 분석"""
        logger.info("Analyzing security vulnerability introduction patterns...")
        
        with self.driver.session() as session:
            # CVE와 관련된 커밋 분석
            cve_pattern_query = """
            MATCH (a:Author)-[:AUTHORED]->(c:Commit)-[:FIXES]->(cve:CVE)
            WITH a, cve, c
            
            MATCH (a)-[:AUTHORED]->(other_c:Commit)-[:BELONGS_TO]->(r:Repository)
            WHERE other_c.timestamp < c.timestamp
            
            WITH a, cve, c, count(other_c) as commits_before_fix
            
            RETURN a.login as author,
                   cve.id as cve_id,
                   cve.severity as severity,
                   commits_before_fix,
                   c.message as fix_message
            ORDER BY commits_before_fix DESC
            LIMIT 50
            """
            
            result = session.run(cve_pattern_query)
            
            vulnerability_patterns = []
            for record in result:
                vulnerability_patterns.append({
                    'author': record['author'],
                    'cve_id': record['cve_id'],
                    'severity': record['severity'],
                    'commits_before_fix': record['commits_before_fix'],
                    'fix_message': record['fix_message']
                })
                
            return vulnerability_patterns
            
    def analyze_project_influence_network(self):
        """프로젝트 영향도 네트워크 분석"""
        logger.info("Analyzing project influence network...")
        
        with self.driver.session() as session:
            # 프로젝트 간 기여자 공유 분석
            project_network_query = """
            MATCH (a:Author)-[:AUTHORED]->(c:Commit)-[:BELONGS_TO]->(r:Repository)
            WITH a, collect(DISTINCT r.name) as projects
            
            WHERE size(projects) >= 2  // 2개 이상 프로젝트에 기여
            
            WITH projects
            UNWIND projects as project1
            UNWIND projects as project2
            WHERE project1 <> project2
            
            WITH project1, project2, count(*) as shared_contributors
            WHERE shared_contributors >= 2
            
            RETURN project1, project2, shared_contributors
            ORDER BY shared_contributors DESC
            LIMIT 100
            """
            
            result = session.run(project_network_query)
            
            network_data = []
            for record in result:
                network_data.append({
                    'project1': record['project1'],
                    'project2': record['project2'],
                    'shared_contributors': record['shared_contributors']
                })
                
            return network_data
            
    def analyze_commit_timing_patterns(self):
        """커밋 타이밍 패턴 분석"""
        logger.info("Analyzing commit timing patterns...")
        
        with self.driver.session() as session:
            # 시간대별 커밋 패턴
            timing_query = """
            MATCH (a:Author)-[:AUTHORED]->(c:Commit)
            WHERE c.timestamp IS NOT NULL
            
            WITH a, 
                 datetime(c.timestamp).hour as hour,
                 count(c) as commits_at_hour
                 
            RETURN hour, 
                   avg(commits_at_hour) as avg_commits,
                   count(DISTINCT a) as active_contributors
            ORDER BY hour
            """
            
            result = session.run(timing_query)
            
            timing_data = []
            for record in result:
                timing_data.append({
                    'hour': record['hour'],
                    'avg_commits': record['avg_commits'],
                    'active_contributors': record['active_contributors']
                })
                
            return timing_data
            
    def identify_high_influence_contributors(self):
        """고영향도 기여자 식별"""
        logger.info("Identifying high influence contributors...")
        
        with self.driver.session() as session:
            # 영향도 점수 계산
            influence_query = """
            MATCH (a:Author)-[:AUTHORED]->(c:Commit)-[:BELONGS_TO]->(r:Repository)
            WITH a, 
                 count(c) as total_commits,
                 count(DISTINCT r) as projects_contributed,
                 a.security_commits as security_commits,
                 a.experience_months as experience_months
                 
            WHERE total_commits >= 10  // 최소 10개 커밋
            
            WITH a, total_commits, projects_contributed, 
                 coalesce(security_commits, 0) as security_commits,
                 coalesce(experience_months, 0) as experience_months
                 
            // 영향도 점수 계산 (가중치 적용)
            WITH a, total_commits, projects_contributed, security_commits, experience_months,
                 (total_commits * 1.0 + 
                  projects_contributed * 2.0 + 
                  security_commits * 3.0 + 
                  experience_months * 0.1) as influence_score
                 
            RETURN a.login as author,
                   total_commits,
                   projects_contributed,
                   security_commits,
                   experience_months,
                   influence_score
            ORDER BY influence_score DESC
            LIMIT 50
            """
            
            result = session.run(influence_query)
            
            high_influence_contributors = []
            for record in result:
                high_influence_contributors.append({
                    'author': record['author'],
                    'total_commits': record['total_commits'],
                    'projects_contributed': record['projects_contributed'],
                    'security_commits': record['security_commits'],
                    'experience_months': record['experience_months'],
                    'influence_score': record['influence_score']
                })
                
            return high_influence_contributors
            
    def generate_analysis_report(self, output_dir="analysis_results"):
        """분석 결과 종합 리포트 생성"""
        logger.info("Generating comprehensive analysis report...")
        
        # 분석 실행
        experience_data = self.analyze_contributor_experience_patterns()
        vulnerability_patterns = self.analyze_security_vulnerability_patterns()
        network_data = self.analyze_project_influence_network()
        timing_data = self.analyze_commit_timing_patterns()
        high_influence = self.identify_high_influence_contributors()
        
        # 결과 저장
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # JSON 형태로 저장
        results = {
            'experience_patterns': experience_data,
            'vulnerability_patterns': vulnerability_patterns,
            'project_network': network_data,
            'timing_patterns': timing_data,
            'high_influence_contributors': high_influence,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        with open(output_path / "contributor_influence_analysis.json", 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        # 요약 통계 생성
        summary_stats = {
            'total_contributors_analyzed': len(high_influence),
            'avg_experience_months': sum(d['experience_months'] for d in high_influence) / len(high_influence) if high_influence else 0,
            'total_security_commits': sum(d['security_commits'] for d in high_influence),
            'projects_with_shared_contributors': len(set(d['project1'] for d in network_data) | set(d['project2'] for d in network_data)),
            'vulnerability_fixes_analyzed': len(vulnerability_patterns)
        }
        
        with open(output_path / "analysis_summary.json", 'w', encoding='utf-8') as f:
            json.dump(summary_stats, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Analysis report saved to {output_path}")
        logger.info(f"Summary: {summary_stats}")
        
        return results, summary_stats
        
    def create_visualizations(self, results, output_dir="analysis_results"):
        """분석 결과 시각화"""
        logger.info("Creating visualizations...")
        
        output_path = Path(output_dir)
        
        # 1. 경험별 커밋 패턴
        if results['experience_patterns']:
            df_exp = pd.DataFrame(results['experience_patterns'])
            
            plt.figure(figsize=(12, 8))
            plt.subplot(2, 2, 1)
            plt.scatter(df_exp['experience_months'], df_exp['avg_commits'], alpha=0.6)
            plt.xlabel('Experience (months)')
            plt.ylabel('Average Commits')
            plt.title('Experience vs Average Commits')
            
            plt.subplot(2, 2, 2)
            plt.scatter(df_exp['experience_months'], df_exp['avg_security_commits'], alpha=0.6)
            plt.xlabel('Experience (months)')
            plt.ylabel('Average Security Commits')
            plt.title('Experience vs Security Commits')
            
            plt.subplot(2, 2, 3)
            plt.bar(df_exp['experience_months'], df_exp['contributor_count'])
            plt.xlabel('Experience (months)')
            plt.ylabel('Contributor Count')
            plt.title('Experience Distribution')
            
            plt.subplot(2, 2, 4)
            plt.scatter(df_exp['avg_commits'], df_exp['avg_security_commits'], alpha=0.6)
            plt.xlabel('Average Commits')
            plt.ylabel('Average Security Commits')
            plt.title('Commits vs Security Commits')
            
            plt.tight_layout()
            plt.savefig(output_path / "experience_patterns.png", dpi=300, bbox_inches='tight')
            plt.close()
            
        # 2. 고영향도 기여자 상위 20명
        if results['high_influence_contributors']:
            df_influence = pd.DataFrame(results['high_influence_contributors'][:20])
            
            plt.figure(figsize=(15, 10))
            plt.subplot(2, 2, 1)
            plt.barh(df_influence['author'], df_influence['influence_score'])
            plt.xlabel('Influence Score')
            plt.title('Top 20 Contributors by Influence Score')
            
            plt.subplot(2, 2, 2)
            plt.scatter(df_influence['total_commits'], df_influence['projects_contributed'], 
                       s=df_influence['security_commits']*10, alpha=0.6)
            plt.xlabel('Total Commits')
            plt.ylabel('Projects Contributed')
            plt.title('Commits vs Projects (bubble size = security commits)')
            
            plt.subplot(2, 2, 3)
            plt.hist(df_influence['experience_months'], bins=10, alpha=0.7)
            plt.xlabel('Experience (months)')
            plt.ylabel('Count')
            plt.title('Experience Distribution (Top Contributors)')
            
            plt.subplot(2, 2, 4)
            plt.scatter(df_influence['experience_months'], df_influence['influence_score'], alpha=0.6)
            plt.xlabel('Experience (months)')
            plt.ylabel('Influence Score')
            plt.title('Experience vs Influence Score')
            
            plt.tight_layout()
            plt.savefig(output_path / "high_influence_contributors.png", dpi=300, bbox_inches='tight')
            plt.close()
            
        # 3. 시간대별 커밋 패턴
        if results['timing_patterns']:
            df_timing = pd.DataFrame(results['timing_patterns'])
            
            plt.figure(figsize=(12, 6))
            plt.plot(df_timing['hour'], df_timing['avg_commits'], marker='o')
            plt.xlabel('Hour of Day')
            plt.ylabel('Average Commits')
            plt.title('Commit Activity by Hour of Day')
            plt.grid(True, alpha=0.3)
            plt.savefig(output_path / "commit_timing_patterns.png", dpi=300, bbox_inches='tight')
            plt.close()
            
        logger.info(f"Visualizations saved to {output_path}")

def main():
    """메인 실행 함수"""
    logger.info("Starting contributor influence analysis...")
    
    # 환경 변수에서 Neo4j 연결 정보 가져오기
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j+s://26e236b3.databases.neo4j.io")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "yc-TW0XnNO3rV9u0mSR59BVHxlyeJjTC8ngO3QhbkVw")
    
    analyzer = ContributorInfluenceAnalyzer(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        # 분석 실행 및 리포트 생성
        results, summary = analyzer.generate_analysis_report()
        
        # 시각화 생성
        analyzer.create_visualizations(results)
        
        logger.info("Contributor influence analysis completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
