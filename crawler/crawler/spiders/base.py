"""
신재생에너지 관련 웹사이트 크롤링을 위한 단순화된 베이스 스파이더
"""
import scrapy
import json
import logging
import time
import os
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import urljoin


class BaseRenewableEnergySpider(scrapy.Spider):
    """신재생에너지 크롤링을 위한 베이스 스파이더"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 크롤링 모드 설정
        self.mode = kwargs.get('mode', 'test')
        
        # Selenium 드라이버 초기화
        self.driver = None
        self.selenium_timeout = 15  # 기본값 설정
        
        # 출력 디렉토리 설정
        self.setup_output_directory()
        
        # 분석 결과 로드
        self.analysis_result = self.load_analysis_result()
        
        self.logger.info(f"베이스 스파이더 초기화 완료 - 모드: {self.mode}")
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """Scrapy crawler에서 스파이더 생성"""
        spider = super().from_crawler(crawler, *args, **kwargs)
        
        # 설정값 읽기 (crawler를 통해 접근)
        spider.selenium_timeout = crawler.settings.getint('SELENIUM_TIMEOUT', 15)
        
        return spider
    
    def setup_output_directory(self):
        """출력 디렉토리 설정"""
        project_root = Path(__file__).parent.parent.parent.parent
        self.output_dir = project_root / 'output'
        
        # 스파이더별 디렉토리 생성
        spider_output_dir = self.output_dir / self.name
        spider_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 직접 저장 기능 비활성화 - 파이프라인에서 처리
        # self.data_file = spider_output_dir / f'{self.name}_data.json'
        self.logger.info(f"출력 디렉토리: {spider_output_dir}")
    
    def load_analysis_result(self):
        """분석 결과 로드"""
        try:
            # 중앙 분석 서비스 시도
            try:
                from common.analysis_service import get_analysis_service
                service = get_analysis_service()
                result = service.get_or_create_analysis(self.name)
                if result:
                    self.logger.info("중앙 분석 서비스에서 분석 결과 로드 성공")
                    return result
            except Exception as e:
                self.logger.warning(f"중앙 분석 서비스 사용 실패: {e}")
            
            # 로컬 파일 시도
            site_name = self.name.split('_')[0]
            analysis_dir = self.output_dir.parent / 'output' / 'analysis' / site_name
            
            if analysis_dir.exists():
                analysis_files = list(analysis_dir.glob(f'{self.name}_analysis_*.json'))
                if analysis_files:
                    latest_file = max(analysis_files, key=lambda x: x.stat().st_mtime)
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        result = json.load(f)
                    self.logger.info(f"로컬 분석 결과 로드 성공: {latest_file}")
                    return result
            
            self.logger.warning("분석 결과를 찾을 수 없습니다")
            return None
            
        except Exception as e:
            self.logger.error(f"분석 결과 로드 실패: {e}")
            return None
    
    def setup_selenium(self):
        """Selenium 웹드라이버 설정"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(self.selenium_timeout)
            
            self.logger.info("Selenium 웹드라이버 초기화 성공")
            return True
            
        except Exception as e:
            self.logger.error(f"Selenium 웹드라이버 초기화 실패: {e}")
            return False
    
    def selenium_get(self, url, wait_for_element=None, timeout=None):
        """Selenium으로 페이지 로드"""
        if not self.driver and not self.setup_selenium():
            return False
        
        try:
            self.driver.get(url)
            
            if wait_for_element:
                wait_timeout = timeout or self.selenium_timeout
                wait = WebDriverWait(self.driver, wait_timeout)
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element)))
            
            self.logger.debug(f"페이지 로드 성공: {url}")
            return True
            
        except TimeoutException:
            self.logger.warning(f"페이지 로드 시간 초과: {url}")
            return False
        except Exception as e:
            self.logger.error(f"페이지 로드 실패: {e}")
            return False
    
    def selenium_click(self, selector, timeout=None):
        """Selenium으로 요소 클릭"""
        if not self.driver:
            return False
        
        try:
            wait_timeout = timeout or self.selenium_timeout
            wait = WebDriverWait(self.driver, wait_timeout)
            element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            element.click()
            return True
            
        except TimeoutException:
            self.logger.warning(f"요소 클릭 시간 초과: {selector}")
            return False
        except Exception as e:
            self.logger.warning(f"요소 클릭 실패: {e}")
            return False
    
    def selenium_find_elements(self, selector):
        """Selenium으로 요소들 찾기"""
        if not self.driver:
            return []
        
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            return elements
        except Exception as e:
            self.logger.error(f"요소 찾기 실패: {e}")
            return []
    
    def get_analysis_config(self, key, default=None):
        """분석 결과에서 설정값 조회"""
        if not self.analysis_result:
            return default
        
        try:
            keys = key.split('.')
            value = self.analysis_result
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
            
        except Exception:
            return default
    
    def closed(self, reason):
        """스파이더 종료 시 정리"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("Selenium 드라이버 정리 완료")
            except Exception as e:
                self.logger.error(f"Selenium 드라이버 정리 실패: {e}")
        
        self.logger.info(f"스파이더 종료: {reason}")


class BaseFAQSpider(BaseRenewableEnergySpider):
    """FAQ 페이지 전용 베이스 스파이더"""
    
    def extract_faq_items(self, faq_elements, content_selector=None):
        """FAQ 항목들 추출"""
        items = []
        
        for i, element in enumerate(faq_elements, 1):
            try:
                # 제목 추출
                title = self.extract_text(element, 'a, .title, h3, h4, strong, .result_tit')
                link = self.extract_link(element)
                
                if not title or not link:
                    self.logger.warning(f"FAQ {i}: 제목 또는 링크 없음")
                    continue
                
                # 상세 내용 추출 (선택적)
                content = ""
                if content_selector and link:
                    content = self.extract_detail_content(link, content_selector)
                
                item = {
                    'title': title.strip(),
                    'content': content.strip() if content else "",
                    'url': link,
                    'crawled_at': datetime.now().isoformat(),
                    'source': self.name
                }
                
                items.append(item)
                self.logger.info(f"FAQ {i} 추출 완료: {title[:50]}...")
                
            except Exception as e:
                self.logger.error(f"FAQ {i} 추출 실패: {e}")
                continue
        
        return items
    
    def extract_text(self, element, selector_options):
        """다양한 선택자로 텍스트 추출 시도"""
        # Selenium WebElement에서 텍스트 추출
        for selector in selector_options.split(', '):
            try:
                sub_element = element.find_element(By.CSS_SELECTOR, selector)
                text = sub_element.text
                if text and text.strip():
                    return text.strip()
            except:
                continue
        
        # 직접 텍스트 추출
        try:
            text = element.text
            if text and text.strip():
                return text.strip()
        except:
            pass
        
        return ""
    
    def extract_link(self, element):
        """링크 추출"""
        try:
            link_element = element.find_element(By.CSS_SELECTOR, 'a')
            href = link_element.get_attribute('href')
            if href:
                return urljoin('https://www.knrec.or.kr', href)
        except:
            pass
        
        return ""
    
    def extract_detail_content(self, url, content_selector):
        """상세 페이지에서 내용 추출"""
        if not self.selenium_get(url, wait_for_element=content_selector):
            return ""
        
        try:
            content_elements = self.selenium_find_elements(content_selector)
            if content_elements:
                contents = [elem.text for elem in content_elements if elem.text.strip()]
                return '\n\n'.join(contents)
        except Exception as e:
            self.logger.error(f"상세 내용 추출 실패: {e}")
        
        return ""
