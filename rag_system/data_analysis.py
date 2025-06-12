"""
RAG 시스템을 위한 데이터 분석 모듈
크롤링된 FAQ 데이터를 분석하고 전처리합니다.
"""

import json
import pandas as pd
from collections import Counter, defaultdict
import re
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class FAQDataAnalyzer:
    """FAQ 데이터 분석 클래스"""
    
    def __init__(self, data_path: str):
        """
        Args:
            data_path: JSON 파일 경로
        """
        self.data_path = Path(data_path)
        self.data = None
        self.df = None
        self.categories = {}
        
    def load_data(self) -> pd.DataFrame:
        """JSON 데이터를 로드하고 DataFrame으로 변환"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            self.df = pd.DataFrame(self.data)
            print(f"✅ 데이터 로드 완료: {len(self.df)}개 FAQ")
            return self.df
            
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return None
    
    def analyze_structure(self) -> Dict:
        """데이터 구조 분석"""
        if self.df is None:
            print("❌ 데이터가 로드되지 않았습니다.")
            return {}
        
        analysis = {
            'total_count': len(self.df),
            'columns': list(self.df.columns),
            'data_types': dict(self.df.dtypes),
            'missing_values': dict(self.df.isnull().sum()),
            'sample_record': self.df.iloc[0].to_dict() if len(self.df) > 0 else {}
        }
        
        # 텍스트 길이 분석
        if 'title' in self.df.columns:
            analysis['title_length'] = {
                'mean': self.df['title'].str.len().mean(),
                'max': self.df['title'].str.len().max(),
                'min': self.df['title'].str.len().min()
            }
        
        if 'content' in self.df.columns:
            analysis['content_length'] = {
                'mean': self.df['content'].str.len().mean(),
                'max': self.df['content'].str.len().max(),
                'min': self.df['content'].str.len().min()
            }
        
        return analysis
    
    def categorize_faqs(self) -> Dict[str, List]:
        """FAQ를 카테고리별로 분류"""
        if self.df is None:
            return {}
        
        # URL 기반 카테고리 추출
        url_categories = defaultdict(list)
        for idx, row in self.df.iterrows():
            url = row.get('url', '')
            if 'depth_1=' in url and 'depth_2=' in url:
                # URL에서 카테고리 코드 추출
                depth1_match = re.search(r'depth_1=([A-Z0-9]+)', url)
                depth2_match = re.search(r'depth_2=([A-Z0-9]+)', url)
                
                if depth1_match and depth2_match:
                    category = f"{depth1_match.group(1)}_{depth2_match.group(1)}"
                    url_categories[category].append(idx)
        
        # 제목 기반 키워드 카테고리 분류
        keyword_categories = {
            '주택지원': ['주택', '단독주택', '공동주택', '아파트'],
            '건물지원': ['건물', '시설물', '상업', '공장'],
            '금융지원': ['금융', '융자', '대출', '지원금', '보조금'],
            'RPS제도': ['RPS', '공급인증서', 'REC', '의무화'],
            'KS인증': ['KS인증', '인증', '검증', '시험'],
            '태양광': ['태양광', '태양열', '모듈', '인버터'],
            '풍력': ['풍력', '풍차'],
            '지열': ['지열'],
            '연료전지': ['연료전지'],
            'ESS': ['ESS', 'EMS', '에너지저장'],
            '탄소검증': ['탄소', '배출량', '검증']
        }
        
        keyword_classification = defaultdict(list)
        for idx, row in self.df.iterrows():
            title = row.get('title', '').lower()
            content = row.get('content', '').lower()
            text = f"{title} {content}"
            
            for category, keywords in keyword_categories.items():
                if any(keyword in text for keyword in keywords):
                    keyword_classification[category].append(idx)
        
        self.categories = {
            'url_based': dict(url_categories),
            'keyword_based': dict(keyword_classification)
        }
        
        return self.categories
    
    def extract_statistics(self) -> Dict:
        """데이터 통계 정보 추출"""
        if self.df is None:
            return {}
        
        stats = {}
        
        # 기본 통계
        stats['basic'] = {
            'total_faqs': len(self.df),
            'unique_pages': self.df['page'].nunique() if 'page' in self.df.columns else 0,
            'crawl_date': self.df['crawled_at'].iloc[0] if 'crawled_at' in self.df.columns else None
        }
        
        # 카테고리별 통계
        if self.categories:
            stats['categories'] = {}
            for cat_type, categories in self.categories.items():
                stats['categories'][cat_type] = {
                    cat: len(indices) for cat, indices in categories.items()
                }
        
        # 텍스트 길이 분포
        if 'title' in self.df.columns and 'content' in self.df.columns:
            stats['text_length'] = {
                'title': {
                    'mean': round(self.df['title'].str.len().mean(), 2),
                    'std': round(self.df['title'].str.len().std(), 2),
                    'median': self.df['title'].str.len().median()
                },
                'content': {
                    'mean': round(self.df['content'].str.len().mean(), 2),
                    'std': round(self.df['content'].str.len().std(), 2),
                    'median': self.df['content'].str.len().median()
                }
            }
        
        return stats
    
    def detect_duplicates(self) -> Dict:
        """중복 데이터 탐지"""
        if self.df is None:
            return {}
        
        duplicates = {}
        
        # 제목 기반 중복
        if 'title' in self.df.columns:
            title_duplicates = self.df[self.df.duplicated('title', keep=False)]
            duplicates['title'] = {
                'count': len(title_duplicates),
                'examples': title_duplicates['title'].unique()[:5].tolist()
            }
        
        # URL 기반 중복
        if 'url' in self.df.columns:
            url_duplicates = self.df[self.df.duplicated('url', keep=False)]
            duplicates['url'] = {
                'count': len(url_duplicates),
                'examples': url_duplicates['url'].unique()[:5].tolist()
            }
        
        # 내용 기반 중복 (해시 기반)
        if 'content' in self.df.columns:
            content_hash = self.df['content'].str.len()  # 간단한 길이 기반 비교
            content_duplicates = self.df[content_hash.duplicated(keep=False)]
            duplicates['content_length'] = {
                'count': len(content_duplicates),
                'note': '내용 길이 기반 중복 추정'
            }
        
        return duplicates
    
    def generate_report(self, output_path: str = None) -> str:
        """분석 보고서 생성"""
        if output_path is None:
            output_path = f"faq_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # 분석 실행
        structure = self.analyze_structure()
        categories = self.categorize_faqs()
        stats = self.extract_statistics()
        duplicates = self.detect_duplicates()
        
        # 보고서 작성
        report = []
        report.append("=" * 60)
        report.append("FAQ 데이터 분석 보고서")
        report.append("=" * 60)
        report.append(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"데이터 파일: {self.data_path}")
        report.append("")
        
        # 1. 기본 구조
        report.append("1. 데이터 구조 분석")
        report.append("-" * 30)
        report.append(f"총 FAQ 수: {structure.get('total_count', 0)}")
        report.append(f"컬럼: {', '.join(structure.get('columns', []))}")
        report.append("")
        
        if 'title_length' in structure:
            tl = structure['title_length']
            report.append(f"제목 길이 - 평균: {tl['mean']:.1f}, 최대: {tl['max']}, 최소: {tl['min']}")
        
        if 'content_length' in structure:
            cl = structure['content_length']
            report.append(f"내용 길이 - 평균: {cl['mean']:.1f}, 최대: {cl['max']}, 최소: {cl['min']}")
        
        report.append("")
        
        # 2. 카테고리 분석
        report.append("2. 카테고리 분석")
        report.append("-" * 30)
        if 'keyword_based' in self.categories:
            for cat, indices in self.categories['keyword_based'].items():
                report.append(f"{cat}: {len(indices)}개")
        report.append("")
        
        # 3. 중복 데이터
        report.append("3. 중복 데이터 분석")
        report.append("-" * 30)
        for dup_type, dup_info in duplicates.items():
            report.append(f"{dup_type} 중복: {dup_info.get('count', 0)}개")
        report.append("")
        
        # 4. 샘플 데이터
        report.append("4. 샘플 데이터")
        report.append("-" * 30)
        if len(self.df) > 0:
            sample = self.df.iloc[0]
            report.append(f"제목: {sample.get('title', 'N/A')}")
            report.append(f"내용: {sample.get('content', 'N/A')[:100]}...")
            report.append(f"URL: {sample.get('url', 'N/A')}")
        
        report_text = "\n".join(report)
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"✅ 분석 보고서 생성: {output_path}")
        return report_text


def main():
    """메인 실행 함수"""
    print("🔍 FAQ 데이터 분석 시작")
    
    # 데이터 파일 경로 (수정 필요)
    data_file = "crawler/output/data/knrec_faq_20250611_181612.json"
    
    if not Path(data_file).exists():
        print(f"❌ 데이터 파일을 찾을 수 없습니다: {data_file}")
        print("올바른 파일 경로를 확인하세요.")
        return
    
    # 분석기 초기화
    analyzer = FAQDataAnalyzer(data_file)
    
    # 데이터 로드
    df = analyzer.load_data()
    if df is None:
        return
    
    # 분석 실행 및 보고서 생성
    report = analyzer.generate_report()
    print("\n" + "="*50)
    print("📊 분석 결과 요약")
    print("="*50)
    print(report)


if __name__ == "__main__":
    main() 