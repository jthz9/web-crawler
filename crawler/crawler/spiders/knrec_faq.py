"""
한국에너지공단 신재생에너지센터 FAQ 크롤링 스파이더
단순화된 베이스 클래스를 상속받아 순수 Selenium 방식으로 크롤링합니다.
"""
import time
import logging
import scrapy
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from .base import BaseFAQSpider
from crawler.items import RenewableEnergyItem


class KnrecFaqSpider(BaseFAQSpider):
    """한국에너지공단 신재생에너지센터 FAQ 크롤링 스파이더"""
    
    name = 'knrec_faq'
    allowed_domains = ['knrec.or.kr']
    start_urls = ['https://www.knrec.or.kr/biz/faq/faq_list01.do']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 크롤링 통계
        self.total_pages = 0
        self.processed_pages = 0
        self.extracted_faqs = 0
        self.duplicate_faqs = 0
        self.seen_urls = set()
    
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """Scrapy crawler에서 스파이더 생성"""
        spider = super().from_crawler(crawler, *args, **kwargs)
        return spider
    
    def start_requests(self):
        """크롤링 시작"""
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)
    
    def parse(self, response):
        """메인 파싱 로직"""
        self.logger.info("=== KNREC FAQ 크롤링 시작 ===")
        
        # 실제 크롤링 수행 및 Item 생성
        yield from self.crawl_faqs()
    
    def crawl_faqs(self):
        """실제 FAQ 크롤링 로직 - Item을 yield"""
        
        # Selenium 초기화
        if not self.setup_selenium():
            self.logger.error("Selenium 초기화 실패")
            return
        
        # 분석 결과에서 설정 로드
        self.load_crawling_config()
        
        # 첫 페이지 접근
        if not self.selenium_get(self.start_urls[0], wait_for_element="ul.result_list"):
            self.logger.error("초기 페이지 로드 실패")
            return
        
        # 간편검색 탭 클릭
        self.click_simple_search_tab()
        
        # 전체 페이지 수 확인
        self.determine_total_pages()
        
        # 모든 페이지 크롤링하고 Item yield
        yield from self.crawl_all_pages()
        
        # 크롤링 완료 요약
        self.log_crawling_summary()
    
    def load_crawling_config(self):
        """분석 결과에서 크롤링 설정 로드"""
        if not self.analysis_result:
            self.logger.warning("분석 결과 없음 - 기본 설정 사용")
            self.faq_selector = "ul.result_list li"
            self.content_selector = ".album_view_txt .p_txt"
            self.simple_search_tab = "li:nth-child(2) a"
            return
        
        # 분석 결과에서 설정 추출
        self.faq_selector = self.get_analysis_config('best_selectors.faq_selector', "ul.result_list li")
        self.content_selector = self.get_analysis_config('best_selectors.content_selector', ".album_view_txt .p_txt")
        self.simple_search_tab = self.get_analysis_config('simple_search_tab', "li:nth-child(2) a")
        
        self.logger.info(f"크롤링 설정:")
        self.logger.info(f"  - FAQ 선택자: {self.faq_selector}")
        self.logger.info(f"  - 내용 선택자: {self.content_selector}")
        self.logger.info(f"  - 간편검색 탭: {self.simple_search_tab}")
    
    def click_simple_search_tab(self):
        """간편검색 탭 클릭"""
        try:
            if self.selenium_click(self.simple_search_tab, timeout=5):
                self.logger.info("간편검색 탭 클릭 성공")
                time.sleep(2)  # 페이지 로딩 대기
            else:
                self.logger.warning("간편검색 탭 클릭 실패 - 기본 탭으로 진행")
        except Exception as e:
            self.logger.warning(f"간편검색 탭 클릭 중 오류: {e}")
    
    def determine_total_pages(self):
        """전체 페이지 수 확인"""
        try:
            # 여러 방법으로 페이지 수 확인 시도
            max_page = 1
            
            # 1. 페이지네이션에서 숫자 확인
            pagination_elements = self.selenium_find_elements(".pagination a, .paging a, .page_num a")
            for element in pagination_elements:
                text = element.text.strip()
                if text.isdigit():
                    max_page = max(max_page, int(text))
            
            # 2. 마지막 페이지 링크 확인
            last_page_elements = self.selenium_find_elements("a[title*='마지막'], .last, .end")
            for element in last_page_elements:
                href = element.get_attribute('href')
                if href and 'page=' in href:
                    import re
                    page_match = re.search(r'page=(\d+)', href)
                    if page_match:
                        max_page = max(max_page, int(page_match.group(1)))
            
            # 3. 전체 35페이지 사용
            if max_page < 35:
                max_page = 35
            
            self.total_pages = max_page
            self.logger.info(f"전체 페이지 수: {self.total_pages}")
            
        except Exception as e:
            self.logger.error(f"페이지 수 확인 실패: {e}")
            self.total_pages = 35  # 기본값
    
    def crawl_all_pages(self):
        """모든 페이지 크롤링하고 Item yield"""
        
        # 크롤링할 페이지 결정
        if self.mode == 'test':
            pages_to_crawl = list(range(1, self.total_pages + 1))  # 테스트도 전체 페이지
            self.logger.info(f"테스트 모드: 전체 {len(pages_to_crawl)}개 페이지 크롤링")
        else:
            pages_to_crawl = list(range(1, self.total_pages + 1))
            self.logger.info(f"전체 모드: {len(pages_to_crawl)}개 페이지 크롤링")
        
        # 각 페이지 크롤링
        for page_num in pages_to_crawl:
            try:
                self.logger.info(f"페이지 {page_num} 크롤링 시작")
                
                if self.navigate_to_page(page_num):
                    # Item들을 yield
                    yield from self.extract_page_items(page_num)
                    self.processed_pages += 1
                
                time.sleep(1)  # 페이지 간 간격
                
            except Exception as e:
                self.logger.error(f"페이지 {page_num} 크롤링 실패: {e}")
                continue
    
    def navigate_to_page(self, page_number):
        """특정 페이지로 이동"""
        try:
            target_url = f"https://www.knrec.or.kr/biz/faq/faq_list01.do?page={page_number}&"
            
            if self.selenium_get(target_url, wait_for_element="ul.result_list"):
                self.click_simple_search_tab()  # 간편검색 탭 다시 클릭
                self.logger.info(f"페이지 {page_number} 이동 성공")
                return True
            else:
                self.logger.warning(f"페이지 {page_number} 이동 실패")
                return False
                
        except Exception as e:
            self.logger.error(f"페이지 {page_number} 이동 중 오류: {e}")
            return False
    
    def extract_page_items(self, page_number):
        """현재 페이지의 모든 FAQ를 Item으로 추출하고 yield (각 FAQ마다 페이지 새로고침)"""
        try:
            page_extracted = 0
            
            # 먼저 모든 FAQ URL을 수집 (DOM 변화 전에)
            faq_urls = self.collect_faq_urls_from_page(page_number)
            
            if not faq_urls:
                self.logger.warning(f"페이지 {page_number}: FAQ URL 없음")
                return
            
            self.logger.info(f"페이지 {page_number}: {len(faq_urls)}개 FAQ URL 수집 완료")
            
            # 각 URL을 처리
            for i, (title, url) in enumerate(faq_urls, 1):
                try:
                    # 중복 확인
                    if url in self.seen_urls:
                        self.duplicate_faqs += 1
                        self.logger.debug(f"페이지 {page_number} FAQ {i}: 중복 제외 - {title[:30]}...")
                        continue
                    
                    self.seen_urls.add(url)
                    
                    # 상세 내용 추출
                    content = self.extract_detail_content(url, self.content_selector)
                    
                    # Item 생성 (page를 첫 번째 필드로)
                    item = RenewableEnergyItem()
                    item['page'] = page_number
                    item['title'] = title
                    item['content'] = content
                    item['url'] = url
                    item['source'] = "한국에너지공단 신재생에너지센터"
                    item['document_type'] = "FAQ"
                    item['date_published'] = time.strftime('%Y-%m-%d')
                    item['spider'] = self.name
                    
                    self.extracted_faqs += 1
                    page_extracted += 1
                    self.logger.info(f"페이지 {page_number} FAQ {i}: 추출 완료 - {title[:30]}...")
                    
                    yield item
                    
                except Exception as e:
                    self.logger.warning(f"페이지 {page_number} FAQ {i}: 추출 중 오류: {e}")
                    continue
            
            self.logger.info(f"페이지 {page_number}: {page_extracted}개 새로운 FAQ 추출 완료")
            
        except Exception as e:
            self.logger.error(f"페이지 {page_number} FAQ 추출 실패: {e}")
    
    def collect_faq_urls_from_page(self, page_number):
        """페이지에서 모든 FAQ의 제목과 URL을 미리 수집"""
        try:
            faq_elements = self.selenium_find_elements(self.faq_selector)
            if not faq_elements:
                return []
            
            faq_urls = []
            for i, element in enumerate(faq_elements):
                try:
                    title = self.extract_clean_title(element)
                    url = self.extract_link(element)
                    
                    if title and url:
                        faq_urls.append((title, url))
                        self.logger.debug(f"FAQ {i+1} URL 수집: {title[:30]}...")
                    else:
                        self.logger.warning(f"FAQ {i+1}: 제목 또는 URL 없음")
                        
                except Exception as e:
                    self.logger.warning(f"FAQ {i+1} URL 수집 중 오류: {e}")
                    continue
            
            return faq_urls
            
        except Exception as e:
            self.logger.error(f"페이지 {page_number} FAQ URL 수집 실패: {e}")
            return []
    
    def extract_link(self, element):
        """링크 추출 (베이스 클래스 메소드 오버라이드)"""
        try:
            link_element = element.find_element(By.CSS_SELECTOR, 'a')
            href = link_element.get_attribute('href')
            if href:
                # KNREC 전용 URL 처리
                if href.startswith('/'):
                    return f"https://www.knrec.or.kr{href}"
                elif not href.startswith('http'):
                    return f"https://www.knrec.or.kr/{href}"
                return href
        except NoSuchElementException:
            pass
        except Exception as e:
            self.logger.warning(f"링크 추출 중 오류: {e}")
        
        return ""
    
    def extract_clean_title(self, element):
        """깔끔한 제목만 추출 (질문 부분만)"""
        try:
            # a 태그에서 title 속성 우선 시도
            link_element = element.find_element(By.CSS_SELECTOR, 'a')
            title_attr = link_element.get_attribute('title')
            if title_attr and title_attr.strip():
                return title_attr.strip()
            
            # a 태그의 텍스트에서 질문 부분만 추출
            link_text = link_element.text.strip()
            if link_text:
                # '?' 까지만 추출 (질문 부분)
                if '?' in link_text:
                    question_part = link_text.split('?')[0] + '?'
                    return question_part.strip()
                # '?' 가 없으면 첫 번째 줄만 추출
                elif '\n' in link_text:
                    return link_text.split('\n')[0].strip()
                else:
                    return link_text
            
        except Exception as e:
            self.logger.warning(f"제목 추출 중 오류: {e}")
        
        # 베이스 클래스 메소드 fallback
        return self.extract_text(element, 'a, .title, h3, h4, strong, .result_tit')
    
    def extract_detail_content(self, url, content_selector):
        """상세 페이지에서 전체 내용 추출 (베이스 클래스 메소드 오버라이드)"""
        if not url:
            return ""
        
        try:
            # 상세 페이지로 이동
            if not self.selenium_get(url, wait_for_element=content_selector):
                self.logger.warning(f"상세 페이지 로드 실패: {url}")
                return ""
            
            # 내용 요소들 찾기
            content_elements = self.selenium_find_elements(content_selector)
            
            if not content_elements:
                self.logger.warning(f"내용 요소 없음: {url}")
                return ""
            
            # 모든 텍스트 수집 및 중복 제거
            all_texts = []
            for element in content_elements:
                text = element.text.strip()
                if text and text not in all_texts:
                    all_texts.append(text)
            
            full_content = '\n\n'.join(all_texts)
            
            self.logger.debug(f"상세 내용 추출 완료 ({len(full_content)}자)")
            return full_content
            
        except Exception as e:
            self.logger.error(f"상세 내용 추출 실패: {e}")
            return ""
    
    def log_crawling_summary(self):
        """크롤링 완료 요약 로그"""
        self.logger.info("=== KNREC FAQ 크롤링 완료 ===")
        self.logger.info(f"총 페이지 수: {self.total_pages}")
        self.logger.info(f"처리된 페이지: {self.processed_pages}")
        self.logger.info(f"추출된 FAQ: {self.extracted_faqs}")
        self.logger.info(f"중복 제거: {self.duplicate_faqs}")
        self.logger.info(f"최종 고유 FAQ: {len(self.seen_urls)}")
        
        # 성공률 계산
        if self.total_pages > 0:
            success_rate = (self.processed_pages / self.total_pages) * 100
            self.logger.info(f"페이지 처리 성공률: {success_rate:.1f}%")
    
    def closed(self, reason):
        """스파이더 종료 시 호출"""
        super().closed(reason)
        
        # 최종 요약 저장
        try:
            summary = {
                'spider_name': self.name,
                'crawling_mode': self.mode,
                'total_pages': self.total_pages,
                'processed_pages': self.processed_pages,
                'extracted_faqs': self.extracted_faqs,
                'duplicate_faqs': self.duplicate_faqs,
                'unique_faqs': len(self.seen_urls),
                'crawled_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            self.logger.info(f"크롤링 요약: {summary}")
            
        except Exception as e:
            self.logger.error(f"요약 정보 생성 실패: {e}")
