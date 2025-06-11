"""
다중 웹사이트 크롤링을 위한 중앙 분석 서비스
각 웹사이트별 분석기를 관리하고 분석 결과를 캐싱합니다.
"""
import os
import json
import glob
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging

class AnalysisService:
    """
    웹사이트 분석 중앙 관리 서비스
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 분석 결과 디렉토리 설정
        self.analysis_base_dir = Path(__file__).parent.parent / 'output' / 'analysis'
        self.analysis_base_dir.mkdir(parents=True, exist_ok=True)
        
        # 분석 결과 유효 기간 (7일)
        self.cache_validity_days = 7
        
        # 현재 지원하는 웹사이트 목록 (실제 구현된 것만)
        self.supported_sites = {
            'knrec': {
                'name': '한국에너지공단 신재생에너지센터',
                'analyzer_module': 'analysis.knrec_faq_analyzer',
                'analyzer_class': 'KnrecAnalyzer',
                'base_url': 'https://www.knrec.or.kr',
                'implemented': True  # 실제 구현 여부
            }
            # 다른 사이트들은 향후 구현 시 추가
        }
    
    def get_or_create_analysis(self, spider_name, force_refresh=False):
        """
        분석 결과 조회 또는 새로 생성
        
        Args:
            spider_name (str): 스파이더 이름 (예: 'knrec_faq')
            force_refresh (bool): 강제 재분석 여부
            
        Returns:
            dict: 분석 결과 또는 None
        """
        site_name = spider_name.split('_')[0]
        
        # 지원하지 않는 사이트 체크
        if site_name not in self.supported_sites:
            self.logger.warning(f"지원하지 않는 사이트: {site_name}")
            return None
            
        # 구현되지 않은 사이트 체크
        if not self.supported_sites[site_name].get('implemented', False):
            self.logger.warning(f"아직 구현되지 않은 사이트: {site_name}")
            return None
        
        if not force_refresh:
            # 기존 분석 결과 확인
            existing_analysis = self.load_existing_analysis(spider_name)
            if existing_analysis and not self.is_analysis_outdated(existing_analysis):
                self.logger.info(f"{spider_name}: 기존 분석 결과 사용")
                return existing_analysis
        
        # 새로운 분석 수행
        self.logger.info(f"{spider_name}: 새로운 분석 수행")
        return self.perform_new_analysis(spider_name, site_name)
    
    def load_existing_analysis(self, spider_name):
        """기존 분석 결과 로드"""
        try:
            site_name = spider_name.split('_')[0]
            site_analysis_dir = self.analysis_base_dir / site_name
            
            if not site_analysis_dir.exists():
                self.logger.info(f"분석 디렉토리 없음: {site_analysis_dir}")
                return None
            
            # 가장 최근 분석 파일 찾기
            pattern = f"{spider_name}_analysis_*.json"
            analysis_files = list(site_analysis_dir.glob(pattern))
            
            if not analysis_files:
                self.logger.info(f"분석 파일 없음: {pattern}")
                return None
            
            latest_file = max(analysis_files, key=lambda x: x.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                analysis = json.load(f)
                
            self.logger.info(f"기존 분석 결과 로드: {latest_file}")
            return analysis
            
        except Exception as e:
            self.logger.error(f"기존 분석 결과 로드 실패: {e}")
            return None
    
    def is_analysis_outdated(self, analysis):
        """분석 결과가 만료되었는지 확인"""
        try:
            timestamp_str = analysis.get('timestamp')
            if not timestamp_str:
                return True
            
            # ISO 형식 파싱
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
                
            analysis_time = datetime.fromisoformat(timestamp_str)
            current_time = datetime.now()
            
            # 시간대 정보 통일
            if analysis_time.tzinfo is None:
                analysis_time = analysis_time.replace(tzinfo=current_time.tzinfo)
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=analysis_time.tzinfo)
            
            age = current_time - analysis_time
            is_outdated = age > timedelta(days=self.cache_validity_days)
            
            if is_outdated:
                self.logger.info(f"분석 결과가 {age.days}일 경과하여 만료됨")
            
            return is_outdated
            
        except Exception as e:
            self.logger.error(f"분석 결과 만료 확인 중 오류: {e}")
            return True
    
    def perform_new_analysis(self, spider_name, site_name):
        """새로운 분석 수행"""
        try:
            # 사이트 정보 확인
            site_info = self.supported_sites.get(site_name)
            if not site_info or not site_info.get('implemented'):
                self.logger.error(f"구현되지 않은 사이트: {site_name}")
                return None
            
            # 분석기 모듈 동적 임포트
            analyzer_module = self.import_analyzer(site_info['analyzer_module'])
            if not analyzer_module:
                self.logger.error(f"분석기 모듈 로드 실패: {site_info['analyzer_module']}")
                return None
            
            # 분석기 인스턴스 생성
            analyzer_class_name = site_info['analyzer_class']
            if not hasattr(analyzer_module, analyzer_class_name):
                self.logger.error(f"분석기 클래스 없음: {analyzer_class_name}")
                return None
                
            analyzer_class = getattr(analyzer_module, analyzer_class_name)
            # 헤드리스 모드로 분석기 생성
            analyzer = analyzer_class(headless=True)
            
            # 분석 수행 (스파이더별 맞춤 분석)
            analysis_method = self.get_analysis_method(spider_name)
            if not hasattr(analyzer, analysis_method):
                self.logger.error(f"분석 메소드 없음: {analysis_method}")
                return None
                
            # 비동기 분석 메소드 처리
            import asyncio
            analysis_result = getattr(analyzer, analysis_method)()
            
            # asyncio 코루틴인 경우 처리
            if asyncio.iscoroutine(analysis_result):
                analysis_result = asyncio.run(analysis_result)
            
            # 분석 결과 후처리 (크롤링에 필요한 형태로 변환)
            processed_result = self.process_analysis_result(analysis_result, spider_name)
            
            # 결과 저장 (기존 분석기가 이미 저장하므로 여기서는 로그만)
            self.logger.info(f"새로운 분석 완료: {spider_name}")
            
            return processed_result
            
        except Exception as e:
            self.logger.error(f"새로운 분석 수행 중 오류: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def import_analyzer(self, module_path):
        """분석기 모듈 동적 임포트"""
        try:
            # 프로젝트 루트를 sys.path에 추가
            project_root = Path(__file__).parent.parent
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            
            # 직접 모듈 임포트
            if module_path == 'analysis.knrec_faq_analyzer':
                from analysis import knrec_faq_analyzer
                return knrec_faq_analyzer
            
            # 일반적인 임포트 방식
            import importlib
            module = importlib.import_module(module_path)
            return module
            
        except ImportError as e:
            self.logger.error(f"분석기 모듈 임포트 실패: {module_path}, {e}")
            return None
    
    def get_analysis_method(self, spider_name):
        """스파이더별 분석 메소드 결정"""
        method_mapping = {
            'knrec_faq': 'analyze_faq_page',
            'knrec_news': 'analyze_news_page', 
            'knrec_policy': 'analyze_policy_page'
        }
        
        return method_mapping.get(spider_name, 'analyze_faq_page')  # 기본값 설정
    
    def process_analysis_result(self, raw_result, spider_name):
        """분석 결과를 크롤링에 사용하기 좋게 후처리"""
        try:
            if not raw_result:
                return None
            
            # KNREC FAQ 전용 후처리
            if spider_name == 'knrec_faq':
                processed = {
                    'timestamp': raw_result.get('timestamp'),
                    'url': raw_result.get('url'),
                    'title': raw_result.get('title'),
                    'best_selectors': {
                        'faq_selector': raw_result.get('faq_selector_used', 'ul.result_list li'),
                        'content_selector': '.album_view_txt .p_txt',  # 기본값
                        'pagination_selector': '.pagination a'
                    },
                    'simple_search_tab': 'li:nth-child(2) a',  # 간편검색 탭
                    'total_pages': 35,  # 분석 결과에서 추출 가능
                    'faq_count': raw_result.get('faq_count', 0),
                    'analysis_summary': {
                        'faq_items_found': len(raw_result.get('faq_items', [])),
                        'pagination_working': raw_result.get('pagination_count', 0) > 0,
                        'simple_search_working': raw_result.get('simple_search_tab_clicked', False)
                    }
                }
                return processed
            
            # 다른 스파이더의 경우 원본 반환
            return raw_result
            
        except Exception as e:
            self.logger.error(f"분석 결과 후처리 실패: {e}")
            return raw_result
    
    def save_analysis_result(self, spider_name, site_name, analysis_result):
        """분석 결과 저장"""
        try:
            # 사이트별 디렉토리 생성
            site_analysis_dir = self.analysis_base_dir / site_name
            site_analysis_dir.mkdir(exist_ok=True)
            
            # 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{spider_name}_analysis_{timestamp}.json"
            filepath = site_analysis_dir / filename
            
            # 결과 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"분석 결과 저장: {filepath}")
            
        except Exception as e:
            self.logger.error(f"분석 결과 저장 실패: {e}")
    
    def get_site_config(self, site_name):
        """사이트 설정 정보 반환"""
        return self.supported_sites.get(site_name, {})
    
    def list_supported_sites(self):
        """지원하는 사이트 목록 반환 (구현된 것만)"""
        return [site for site, config in self.supported_sites.items() 
                if config.get('implemented', False)]
    
    def list_all_sites(self):
        """모든 등록된 사이트 목록 반환 (구현 여부 포함)"""
        return {site: config.get('implemented', False) 
                for site, config in self.supported_sites.items()}
    
    def cleanup_old_analyses(self, days_to_keep=30):
        """오래된 분석 결과 정리"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        
        for site_dir in self.analysis_base_dir.iterdir():
            if not site_dir.is_dir():
                continue
                
            for analysis_file in site_dir.glob("*_analysis_*.json"):
                file_time = datetime.fromtimestamp(analysis_file.stat().st_mtime)
                
                if file_time < cutoff_date:
                    analysis_file.unlink()
                    cleaned_count += 1
                    self.logger.info(f"오래된 분석 파일 삭제: {analysis_file}")
        
        self.logger.info(f"총 {cleaned_count}개 오래된 분석 파일 정리 완료")
        return cleaned_count


# 글로벌 분석 서비스 인스턴스
analysis_service = AnalysisService()


def get_analysis_service():
    """분석 서비스 인스턴스 반환"""
    return analysis_service 