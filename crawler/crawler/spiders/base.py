import scrapy
from datetime import datetime
from crawler.items import RenewableEnergyItem
import os
import json
import logging
from pathlib import Path
import re

class BaseRenewableEnergySpider(scrapy.Spider):
    """
    모든 신재생에너지 스파이더의 기본 클래스
    공통 기능 및 설정을 제공합니다.
    """
    
    def __init__(self, *args, **kwargs):
        super(BaseRenewableEnergySpider, self).__init__(*args, **kwargs)
        
        # 크롤링 모드 설정 (test 또는 full)
        self.mode = kwargs.get('mode', 'test')
        if self.mode not in ['test', 'full']:
            self.mode = 'test'  # 기본값은 테스트 모드
        
        # 아이템 카운트 초기화
        self.item_count = 0
        self.max_items = 10  # 테스트 모드에서는 최대 10개의 항목만 크롤링
        
        # 분석 결과 로드
        self.analysis_result = self._load_analysis_result()
        
        # 로깅 설정
        self.logger.setLevel(logging.INFO)
        
    def _load_analysis_result(self):
        """
        분석 단계에서 생성된 결과 파일 로드
        """
        try:
            # 스파이더 이름으로 분석 결과 파일 찾기
            spider_name = getattr(self, 'name', 'unknown')
            self.logger.info(f"분석 결과 파일 로드 시도 - 스파이더 이름: {spider_name}")
            
            # 분석 결과 디렉토리 경로 설정
            analysis_dir = Path(__file__).parent.parent.parent.parent / 'output' / 'analysis'
            self.logger.info(f"분석 결과 디렉토리 경로: {analysis_dir}")
            
            # 스파이더 이름에 해당하는 하위 디렉토리 찾기
            spider_analysis_dir = analysis_dir / spider_name.split('_')[0]
            self.logger.info(f"스파이더 분석 디렉토리 경로: {spider_analysis_dir}")
            
            if not spider_analysis_dir.exists():
                self.logger.warning(f"분석 결과 디렉토리를 찾을 수 없습니다: {spider_analysis_dir}")
                
                # 테스트용 파일 경로 시도
                test_file = analysis_dir / spider_name.split('_')[0] / f"{spider_name}_analysis_test.json"
                self.logger.info(f"테스트 파일 경로 시도: {test_file}")
                
                if test_file.exists():
                    self.logger.info(f"테스트 분석 파일 발견: {test_file}")
                    with open(test_file, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                        self.logger.info(f"테스트 분석 결과 로드 성공: {list(result.keys())}")
                        return result
                return None
            
            # 가장 최근 분석 결과 파일 찾기
            analysis_files = list(spider_analysis_dir.glob(f"{spider_name}_analysis_*.json"))
            self.logger.info(f"발견된 분석 파일 목록: {[f.name for f in analysis_files]}")
            
            if not analysis_files:
                self.logger.warning(f"분석 결과 파일을 찾을 수 없습니다: {spider_name}")
                return None
            
            # 가장 최근 파일 선택
            latest_file = max(analysis_files, key=lambda x: x.stat().st_mtime)
            self.logger.info(f"최신 분석 결과 파일 선택: {latest_file}")
            
            # JSON 파일 로드
            with open(latest_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
                self.logger.info(f"분석 결과 로드 성공: {list(result.keys())}")
                return result
                
        except Exception as e:
            self.logger.error(f"분석 결과 로드 중 오류 발생: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return None
    
    def check_max_items(self):
        """
        최대 아이템 수에 도달했는지 확인
        테스트 모드에서만 사용됩니다.
        
        Returns:
            bool: 최대 아이템 수에 도달했으면 True, 아니면 False
        """
        # 테스트 모드가 아니면 항상 False 반환
        if self.mode != 'test':
            return False
            
        # 전체 아이템 수 제한 확인
        if self.item_count >= self.max_items:
            self.logger.info(f"최대 아이템 수({self.max_items})에 도달하여 크롤링을 중단합니다.")
            return True
            
        # 사이트별 아이템 수 제한 확인 (KnrecDocsSpider에서만 사용)
        if hasattr(self, 'item_counts') and hasattr(self, 'max_items_per_site'):
            # 현재 URL에서 문서 유형 추출
            current_url = getattr(self, 'current_url', None)
            if current_url:
                document_type = self._get_document_type(current_url) if hasattr(self, '_get_document_type') else None
                
                if document_type and document_type in self.item_counts:
                    if self.item_counts[document_type] >= self.max_items_per_site:
                        self.logger.info(f"{document_type} 최대 아이템 수({self.max_items_per_site})에 도달하여 해당 사이트 크롤링을 중단합니다.")
                        return True
        
        return False
    
    def detect_energy_type(self, text):
        """
        텍스트에서 에너지 유형 감지
        
        Args:
            text (str): 분석할 텍스트
            
        Returns:
            str: 감지된 에너지 유형
        """
        energy_types = {
            '태양광': ['태양광', '태양 에너지', 'solar', 'photovoltaic', 'pv'],
            '풍력': ['풍력', '풍력발전', 'wind', 'wind power', 'wind energy'],
            '수력': ['수력', '수력발전', 'hydro', 'hydroelectric'],
            '지열': ['지열', '지열발전', 'geothermal'],
            '바이오': ['바이오', '바이오매스', '바이오가스', 'biomass', 'biogas'],
            '수소': ['수소', '수소에너지', 'hydrogen'],
            '연료전지': ['연료전지', 'fuel cell'],
            '해양': ['해양에너지', '조력', '파력', 'ocean', 'tidal', 'wave']
        }
        
        if not text:
            return '기타'
            
        text = text.lower()
        
        for energy_type, keywords in energy_types.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return energy_type
        
        return '기타'
    
    def create_item(self, title, content, url, source, date_published=None, document_type=None, file_urls=None, post_no=None):
        """
        RenewableEnergyItem 생성 (간소화된 버전)
        
        Args:
            title (str): 문서 제목
            content (str): 문서 내용
            url (str): 원본 URL
            source (str): 출처 (웹사이트 이름)
            date_published (str): 발행일 (YYYY-MM-DD 형식)
            document_type (str): 문서 유형 (공지사항, 뉴스, 사업공고 등)
            file_urls (list): 첨부 파일 URL 목록
            post_no (str): 게시글 번호
            
        Returns:
            RenewableEnergyItem: 생성된 아이템
        """
        from datetime import datetime
        
        # 필수 필드 확인
        if not title or not url:
            self.logger.error(f"필수 필드 누락: title={title}, url={url}")
            return None
        
        # 아이템 생성
        item = RenewableEnergyItem()
        item['title'] = title.strip() if title else ""
        item['content'] = content.strip() if content else ""
        item['url'] = url
        item['source'] = source
        
        # 날짜 설정
        if date_published:
            item['date_published'] = date_published
        else:
            item['date_published'] = datetime.now().strftime('%Y-%m-%d')
            
        # 문서 유형 설정
        item['document_type'] = document_type if document_type else "기타"
        
        # 첨부 파일 URL 설정 (선택적)
        if file_urls:
            item['file_urls'] = file_urls
        
        # 게시글 번호 설정 (선택적)
        if post_no:
            item['post_no'] = post_no
        
        # 크롤링 메타데이터 설정
        item['crawled_at'] = datetime.now().isoformat()
        item['spider'] = self.name
        
        return item

    def clean_html(self, html_content):
        """
        HTML 내용에서 태그를 제거하고 텍스트만 추출
        
        Args:
            html_content (str): 정리할 HTML 내용
            
        Returns:
            str: 정리된 텍스트
        """
        if not html_content:
            return ""
            
        # HTML 태그 제거
        # 스크립트 태그 제거
        clean_text = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
        
        # 스타일 태그 제거
        clean_text = re.sub(r'<style.*?</style>', '', clean_text, flags=re.DOTALL)
        
        # 주석 제거
        clean_text = re.sub(r'<!--.*?-->', '', clean_text, flags=re.DOTALL)
        
        # 나머지 HTML 태그 제거
        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
        
        # HTML 엔티티 변환
        clean_text = clean_text.replace('&nbsp;', ' ')
        clean_text = clean_text.replace('&amp;', '&')
        clean_text = clean_text.replace('&lt;', '<')
        clean_text = clean_text.replace('&gt;', '>')
        clean_text = clean_text.replace('&quot;', '"')
        
        # 연속된 공백 제거
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        # 앞뒤 공백 제거
        clean_text = clean_text.strip()
        
        return clean_text
