"""
KNREC FAQ 크롤링 스파이더
간편검색 탭의 모든 FAQ 항목을 수집합니다.
테스트 모드와 실제 크롤링 모드를 지원합니다.
"""
import scrapy
import logging
import os
import json
import re
from datetime import datetime
import time
import glob
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from crawler.items import RenewableEnergyItem
from crawler.spiders.base import BaseRenewableEnergySpider

class KnrecFaqSpider(BaseRenewableEnergySpider):
    """
    KNREC FAQ 크롤링 스파이더
    간편검색 탭의 FAQ 항목을 수집합니다.
    """
    name = "knrec_faq"
    allowed_domains = ["knrec.or.kr"]
    start_urls = [
        "https://www.knrec.or.kr/biz/faq/faq_list01.do"  # 간편검색 탭 URL
    ]
    
    # 페이지 로딩 대기 시간 설정
    page_load_delay = 3
    
    def __init__(self, *args, **kwargs):
        super(KnrecFaqSpider, self).__init__(*args, **kwargs)
        # 테스트 모드에서는 최대 10개의 FAQ만 크롤링
        if self.mode == 'test':
            self.max_items = 10
        else:
            self.max_items = 500  # 실제 모드에서는 더 많은 항목 크롤링 (증가)
        
        # 이미 방문한 FAQ URL을 저장하는 집합
        self.visited_urls = set()
        
        # 현재 페이지 번호
        self.current_page = 1
        self.max_pages = 15 if self.mode == 'test' else 35  # 테스트 모드에서 15페이지까지 테스트
        
        # 분석 결과 로드
        self.analysis_result = self._load_analysis_result()
        
        # 간편검색 탭 클릭 여부를 추적하는 플래그
        self.simple_search_tab_clicked = False
        
    def _load_analysis_result(self):
        """분석 결과 파일 로드"""
        try:
            # 가장 최근의 분석 결과 파일 찾기
            analysis_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'output', 'analysis', 'knrec')
            analysis_files = glob.glob(os.path.join(analysis_dir, 'knrec_faq_analysis_*.json'))
            
            if not analysis_files:
                self.logger.warning("분석 결과 파일을 찾을 수 없습니다. 기본 설정을 사용합니다.")
                return {
                    "faq_selector_used": "ul.result_list li",
                    "pagination": []
                }
            
            # 가장 최신 파일 선택
            latest_file = max(analysis_files, key=os.path.getctime)
            self.logger.info(f"분석 결과 파일 로드: {latest_file}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
                
            # 필요한 정보 확인 및 로그 출력
            if "faq_selector_used" in result:
                self.logger.info(f"FAQ 선택자: {result['faq_selector_used']}")
            if "faq_count" in result:
                self.logger.info(f"분석된 FAQ 항목 수: {result['faq_count']}")
            if "pagination" in result:
                self.logger.info(f"페이지네이션 링크 수: {len(result['pagination'])}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"분석 결과 로드 중 오류: {str(e)}")
            return {
                "faq_selector_used": "ul.result_list li",
                "pagination": []
            }
    
    def start_requests(self):
        """시작 요청 생성"""
        self.logger.info(f"KNREC FAQ 크롤링 시작 (모드: {self.mode})")
        
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                meta={
                    'selenium': True,
                    'wait_time': 15,
                    'driver_window_size': (1920, 1080),
                    'driver_options': [
                        '--disable-popup-blocking',
                        '--disable-notifications'
                    ]
                }
            )
    
    def parse(self, response):
        """FAQ 목록 페이지 파싱"""
        self.logger.info(f"현재 URL: {response.url}")
        self.logger.info(f"페이지 제목: {response.css('title::text').get()}")
        
        # 셀레니움 드라이버 가져오기
        driver = response.meta.get('driver')
        if not driver:
            self.logger.error("셀레니움 드라이버를 찾을 수 없습니다.")
            return
        
        # 페이지 소스 저장 (테스트 모드에서만)
        if self.mode == 'test':
            try:
                page_source = driver.page_source
                os.makedirs('./output/data', exist_ok=True)
                with open('./output/data/page_source.html', 'w', encoding='utf-8') as f:
                    f.write(page_source)
                self.logger.info("페이지 소스를 ./output/data/page_source.html에 저장했습니다.")
            except Exception as e:
                self.logger.error(f"페이지 소스 저장 중 오류 발생: {e}")
        
        # 간편검색 탭 클릭 시도 (첫 페이지에서만)
        if not self.simple_search_tab_clicked:
            try:
                self.logger.info("간편검색 탭 클릭 시도...")
                tab_simple = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), '간편검색') or contains(@title, '간편검색')]")))
                self.logger.info(f"간편검색 탭 발견: {tab_simple.text}")
                tab_simple.click()
                self.logger.info("간편검색 탭 클릭 완료")
                time.sleep(5)  # 탭 클릭 후 대기
                
                # 간편검색 탭 클릭 후 페이지 소스 저장 (테스트 모드에서만)
                if self.mode == 'test':
                    try:
                        page_source = driver.page_source
                        with open('./output/data/page_source_after_tab.html', 'w', encoding='utf-8') as f:
                            f.write(page_source)
                        self.logger.info("탭 클릭 후 페이지 소스를 ./output/data/page_source_after_tab.html에 저장했습니다.")
                    except Exception as e:
                        self.logger.error(f"탭 클릭 후 페이지 소스 저장 중 오류 발생: {e}")
                
                # 간편검색 탭 클릭 플래그 설정
                self.simple_search_tab_clicked = True
            except Exception as e:
                self.logger.error(f"간편검색 탭 클릭 오류: {str(e)}")
                # 이미 간편검색 탭에 있을 수 있으므로 계속 진행
                self.simple_search_tab_clicked = True  # 오류가 발생해도 다시 시도하지 않도록 플래그 설정
        else:
            self.logger.info("이미 간편검색 탭을 클릭했으므로 건너뜁니다.")
        
        # FAQ 항목 찾기 - 결과 목록에서 각 항목의 링크 추출
        try:
            self.logger.info("FAQ 항목 링크 추출 시도...")
            
            # 분석 결과에서 FAQ 선택자 가져오기
            faq_selector = self.analysis_result.get("faq_selector_used", "ul.result_list li")
            self.logger.info(f"사용할 FAQ 선택자: {faq_selector}")
            
            # 결과 목록 찾기
            result_list = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.result_list"))
            )
            
            # 모든 FAQ 항목의 URL과 제목을 수집
            faq_items = []
            li_elements = result_list.find_elements(By.TAG_NAME, "li")
            self.logger.info(f"FAQ 항목 수: {len(li_elements)}")
            
            for li in li_elements:
                try:
                    link = li.find_element(By.TAG_NAME, "a")
                    url = link.get_attribute("href")
                    title_elem = link.find_element(By.CSS_SELECTOR, "span.result_tit")
                    title = title_elem.text.strip()
                    
                    # 내용 미리보기 추출
                    content_preview = ""
                    try:
                        content_elem = link.find_element(By.CSS_SELECTOR, ".result_txt")
                        content_preview = content_elem.text.strip().replace("....", "")
                    except:
                        pass
                    
                    faq_items.append({
                        "url": url, 
                        "title": title,
                        "content_preview": content_preview
                    })
                except Exception as e:
                    self.logger.error(f"항목 정보 추출 중 오류: {str(e)}")
            
            # 각 페이지의 첫 번째 FAQ만 크롤링 (테스트 목적)
            if faq_items:
                first_faq = faq_items[0]  # 첫 번째 FAQ만 선택
                self.logger.info(f"페이지 {self.current_page}의 첫 번째 FAQ 크롤링: {first_faq['title']}")
                
                # 상세 페이지로 이동하여 전체 내용 추출
                yield scrapy.Request(
                    url=first_faq["url"],
                    callback=self.parse_faq_detail,
                    dont_filter=True,  # 중복 URL 필터링 비활성화
                    meta={
                        'selenium': True,
                        'wait_time': 5,
                        'title': first_faq["title"],
                        'content_preview': first_faq["content_preview"],
                        'page': self.current_page  # 현재 페이지 번호 추가
                    }
                )
            else:
                self.logger.warning(f"페이지 {self.current_page}에서 FAQ 항목을 찾을 수 없습니다.")
            
            # 다음 페이지 처리
            if self.current_page < self.max_pages:
                self.current_page += 1
                # 다음 페이지 링크를 클릭
                next_page_clicked = self._click_next_page(driver)
                
                if next_page_clicked:
                    self.logger.info(f"다음 페이지로 이동 완료 (현재 페이지: {self.current_page})")
                    # 페이지 로딩 대기
                    time.sleep(5)
                    
                    # 현재 페이지에서 다시 파싱 (재귀 호출)
                    yield from self.parse(response)
                else:
                    self.logger.info("다음 페이지를 찾을 수 없거나 클릭할 수 없습니다.")
            else:
                self.logger.info(f"최대 페이지 수({self.max_pages})에 도달했습니다.")
        except Exception as e:
            self.logger.error(f"FAQ 항목 링크 추출 중 오류: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def parse_faq_detail(self, response):
        """FAQ 상세 페이지 파싱"""
        self.logger.info(f"FAQ 상세 페이지 파싱: {response.url}")
        
        # 셀레니움 드라이버 가져오기
        driver = response.meta.get('driver')
        if not driver:
            self.logger.error("셀레니움 드라이버를 찾을 수 없습니다.")
            return
        
        try:
            # 페이지 소스 저장 (테스트 모드에서만)
            if self.mode == 'test':
                try:
                    page_source = driver.page_source
                    file_name = f"./output/data/faq_detail_{response.url.split('=')[-1]}.html"
                    with open(file_name, 'w', encoding='utf-8') as f:
                        f.write(page_source)
                    self.logger.info(f"FAQ 상세 페이지 소스를 {file_name}에 저장했습니다.")
                except Exception as e:
                    self.logger.error(f"FAQ 상세 페이지 소스 저장 중 오류 발생: {e}")
            
            # 제목 가져오기 (이미 메타에서 가져온 제목 사용)
            title = response.meta.get('title', '')
            
            # 백업용 내용 미리보기
            content_preview = response.meta.get('content_preview', '')
            
            # 현재 페이지 번호 가져오기
            page = response.meta.get('page', 0)
            
            # 항상 상세 페이지에서 전체 내용을 추출하도록 시도
            content = ""
            try:
                # 현재 실제 드라이버 URL 확인 (디버깅용)
                current_driver_url = driver.current_url
                self.logger.info(f"드라이버 현재 URL: {current_driver_url}")
                self.logger.info(f"요청된 URL: {response.url}")
                
                # URL이 다르면 실제로 해당 페이지로 이동
                if current_driver_url != response.url:
                    self.logger.info(f"URL이 다릅니다. {response.url}로 이동합니다.")
                    driver.get(response.url)
                    time.sleep(3)  # 페이지 로딩 대기
                
                # 페이지 로딩 대기
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".album_view_txt"))
                )
                
                # 분석 결과에서 찾은 최적의 선택자 사용
                best_content_selector = self.analysis_result.get("recommended_content_selector", ".album_view_txt .p_txt")
                self.logger.info(f"추천 내용 선택자 사용: {best_content_selector}")
                
                # 상세 페이지에서 내용 추출
                try:
                    content_element = driver.find_element(By.CSS_SELECTOR, best_content_selector)
                    content = content_element.text.strip()
                    self.logger.info(f"추천 선택자로 전체 내용 추출 성공 ({len(content)}자): {content[:100]}...")
                except Exception as e:
                    self.logger.error(f"추천 선택자({best_content_selector})로 내용 추출 중 오류: {e}")
                    # 다른 선택자들도 시도해보기
                    try:
                        # 분석 결과에서 찾은 다른 가능한 선택자들
                        alternative_selectors = []
                        if "detail_page_analysis" in self.analysis_result and "content_selectors" in self.analysis_result["detail_page_analysis"]:
                            for selector_info in self.analysis_result["detail_page_analysis"]["content_selectors"]:
                                alternative_selectors.append(selector_info["selector"])
                        
                        # 기본 대체 선택자들도 추가
                        alternative_selectors.extend([
                            ".album_view_txt",
                            ".content_area",
                            ".faq_content", 
                            ".view_content",
                            ".board_view"
                        ])
                        
                        for selector in alternative_selectors:
                            try:
                                content_element = driver.find_element(By.CSS_SELECTOR, selector)
                                content = content_element.text.strip()
                                if content and len(content) > 20:  # 충분한 내용이 있으면
                                    self.logger.info(f"대체 선택자 {selector}로 내용 추출 성공 ({len(content)}자): {content[:100]}...")
                                    break
                            except:
                                continue
                    except Exception as e2:
                        self.logger.error(f"대체 선택자로 내용 추출 중 오류: {e2}")
            
            except Exception as e:
                self.logger.error(f"상세 페이지 로딩 중 오류: {e}")
            
            # 상세 페이지에서 내용을 추출하지 못한 경우에만 미리보기 사용
            if not content or len(content) < 20:
                content = content_preview
                self.logger.warning(f"상세 페이지 내용 추출 실패, 미리보기 내용 사용 ({len(content)}자): {content[:100]}...")
            
            if not content:
                content = "내용을 추출할 수 없습니다."
            
            self.logger.info(f"FAQ 제목: {title[:50]}...")
            self.logger.info(f"FAQ 최종 내용: {content[:150]}...")
            
            # 아이템 생성
            item = self.create_item(
                title=title,
                content=content,
                url=response.url,
                source="한국에너지공단 신재생에너지센터",
                date_published=datetime.now().strftime('%Y-%m-%d'),
                document_type="FAQ",
                file_urls=[]
            )
            
            # 페이지 필드 추가
            item['page'] = page
            
            # 아이템 카운트 증가
            self.item_count += 1
            
            yield item
            
        except Exception as e:
            self.logger.error(f"FAQ 상세 페이지 파싱 중 오류: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def _click_next_page(self, driver):
        """다음 페이지 링크를 클릭하여 이동 - 직접 URL 방식"""
        try:
            # 다음 페이지 번호 (현재 페이지)
            next_page_number = self.current_page
            self.logger.info(f"다음 페이지 번호: {next_page_number} 클릭 시도")
            
            # 직접 URL로 이동 (가장 확실한 방법)
            direct_url = f"https://www.knrec.or.kr/biz/faq/faq_list01.do?page={next_page_number}&"
            self.logger.info(f"직접 URL로 이동: {direct_url}")
            
            driver.get(direct_url)
            time.sleep(self.page_load_delay)
            
            self.current_page = next_page_number
            self.logger.info(f"다음 페이지로 이동 완료 (현재 페이지: {self.current_page})")
            return True
                
        except Exception as e:
            self.logger.error(f"다음 페이지 링크 클릭 중 오류: {e}")
            return False
    
    def detect_energy_type(self, text):
        """텍스트에서 에너지 유형 감지"""
        energy_types = {
            '태양광': ['태양광', '태양 에너지', '솔라', 'solar', 'pv'],
            '태양열': ['태양열', 'solar thermal'],
            '풍력': ['풍력', '풍차', 'wind', '풍력발전'],
            '수력': ['수력', '수력발전', 'hydro'],
            '지열': ['지열', 'geothermal'],
            '바이오': ['바이오', '바이오매스', 'bio', 'biomass'],
            '연료전지': ['연료전지', 'fuel cell'],
            '수소': ['수소', 'hydrogen'],
            '폐기물': ['폐기물', 'waste'],
            '해양': ['해양', '조력', '파력', 'ocean', 'tidal']
        }
        
        text = text.lower()
        for energy_type, keywords in energy_types.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    return energy_type
        
        return '기타'
