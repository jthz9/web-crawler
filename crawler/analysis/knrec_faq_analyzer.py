"""
KNREC 웹사이트 구조 분석 모듈
"""
import os
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class KnrecAnalyzer:
    """
    KNREC 웹사이트 구조를 분석하는 클래스
    """
    def __init__(self, headless=False):
        """
        KnrecAnalyzer 초기화
        
        Args:
            headless (bool): 헤드리스 모드 사용 여부
        """
        # 셀레니움 설정
        self.chrome_options = Options()
        if headless:
            self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.chrome_options.add_argument("--disable-popup-blocking")  # 팝업 차단 비활성화
        self.chrome_options.add_argument("--disable-notifications")  # 알림 비활성화
        
        # 결과 저장 경로
        self.results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', 'analysis', 'knrec')
        os.makedirs(self.results_dir, exist_ok=True)
    
    def analyze_faq_page(self, url="https://www.knrec.or.kr/biz/faq/faq_list01.do", wait_time=5):
        """
        KNREC FAQ 페이지 구조 분석
        
        Args:
            url (str): 분석할 FAQ 페이지 URL
            wait_time (int): 페이지 로딩 대기 시간(초)
            
        Returns:
            dict: 분석 결과
        """
        print(f"페이지 접속: {url}")
        
        # 웹드라이버 초기화
        driver = webdriver.Chrome(options=self.chrome_options)
        
        try:
            # 페이지 접속
            driver.get(url)
            
            # 페이지 로딩 대기
            print("초기 페이지 로딩 대기 중...")
            time.sleep(wait_time)
            
            # 페이지 제목 확인
            title = driver.title
            print(f"페이지 제목: {title}")
            
            # 분석 결과 초기화
            result = {
                "url": url,
                "title": title,
                "timestamp": datetime.now().isoformat(),
                "iframe_count": 0,
                "tab_menu": [],
                "faq_items": [],
                "pagination_count": 0,
                "page_structure": {},
                "element_counts": {}
            }
            
            # iframe 확인
            self._check_iframes(driver, result)
            
            # 탭 메뉴 확인
            self._check_tab_menu(driver, result)
            
            # 간편검색 탭 클릭 시도
            self._try_click_simple_search_tab(driver, result)
            
            # 페이지 로딩 추가 대기
            print("페이지 로딩 추가 대기 중...")
            time.sleep(wait_time)
            
            # FAQ 항목 검색
            self._find_faq_items(driver, result)
            
            # 페이지 구조 분석
            self._analyze_page_structure(driver, result)
            
            # 페이지네이션 확인
            self._check_pagination(driver, result)
            
            # 추가 분석 - 모든 요소 검색
            self._analyze_all_elements(driver, result)
            
            # 페이지 소스 분석
            self._analyze_page_source(driver, result)
            
            # 상세 페이지 분석
            self._analyze_detail_page(driver, result)
            
            # 결과 저장
            self._save_result(result)
            
            return result
            
        finally:
            driver.quit()
    
    def _check_iframes(self, driver, result):
        """iframe 확인"""
        print("\niframe 확인:")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        result["iframe_count"] = len(iframes)
        print(f"iframe 개수: {len(iframes)}")
        
        # iframe 정보 수집
        iframe_details = []
        for i, iframe in enumerate(iframes):
            try:
                iframe_info = {
                    "index": i,
                    "src": iframe.get_attribute("src"),
                    "id": iframe.get_attribute("id"),
                    "name": iframe.get_attribute("name"),
                    "class": iframe.get_attribute("class")
                }
                iframe_details.append(iframe_info)
                print(f"  - iframe {i+1}: {iframe_info['src']}")
            except:
                pass
        
        result["iframes"] = iframe_details
    
    def _check_tab_menu(self, driver, result):
        """탭 메뉴 확인"""
        print("\n탭 메뉴 확인:")
        tab_selectors = [
            ".tab_menu", ".tabs", ".tab_list", ".tab_wrap", 
            "ul.tabs", "ul.tab", ".tabmenu", ".tab_content"
        ]
        
        tab_menu = None
        for selector in tab_selectors:
            tabs = driver.find_elements(By.CSS_SELECTOR, selector)
            if tabs:
                tab_menu = tabs[0]
                print(f"  탭 메뉴 발견: {selector}")
                break
        
        if not tab_menu:
            print("  탭 메뉴를 찾을 수 없습니다.")
            return
        
        # 탭 항목 확인
        tab_items = tab_menu.find_elements(By.TAG_NAME, "li")
        print(f"  탭 항목 수: {len(tab_items)}")
        
        tab_details = []
        for i, tab in enumerate(tab_items):
            try:
                tab_text = tab.text.strip()
                tab_link = tab.find_element(By.TAG_NAME, "a").get_attribute("href")
                tab_details.append({
                    "index": i,
                    "text": tab_text,
                    "link": tab_link,
                    "class": tab.get_attribute("class")
                })
                print(f"  - 탭 {i+1}: {tab_text}")
            except:
                pass
        
        result["tab_menu"] = tab_details
    
    def _try_click_simple_search_tab(self, driver, result):
        """간편검색 탭 클릭 시도"""
        print("\n간편검색 탭 클릭 시도...")
        try:
            # 다양한 방법으로 간편검색 탭 찾기
            tab_simple = None
            
            # 방법 1: 텍스트로 찾기
            try:
                tab_simple = driver.find_element(By.XPATH, "//a[contains(text(), '간편검색') or contains(@title, '간편검색')]")
            except:
                pass
            
            # 방법 2: 특정 클래스로 찾기
            if not tab_simple:
                try:
                    tabs = driver.find_elements(By.CSS_SELECTOR, ".tab_menu li a, .tabs li a, .tab_list li a")
                    for tab in tabs:
                        if '간편' in tab.text or '검색' in tab.text:
                            tab_simple = tab
                            break
                except:
                    pass
            
            if tab_simple:
                print(f"  간편검색 탭 발견: {tab_simple.text}")
                tab_simple.click()
                print("  간편검색 탭 클릭 완료")
                result["simple_search_tab_clicked"] = True
            else:
                print("  간편검색 탭을 찾을 수 없습니다.")
                result["simple_search_tab_clicked"] = False
                
        except Exception as e:
            print(f"  간편검색 탭 클릭 오류: {str(e)}")
            result["simple_search_tab_clicked"] = False
    
    def _find_faq_items(self, driver, result):
        """FAQ 항목 검색"""
        print("\n다양한 CSS 선택자로 FAQ 항목 검색:")
        
        # 다양한 CSS 선택자로 FAQ 항목 찾기
        selectors = [
            ".board_faq_list li",
            ".board_faq_list > li",
            ".board_list_faq li",
            ".board_list_faq > li",
            ".faq_list li",
            ".faq_list > li",
            "ul.board_faq_list > li",
            "ul.board_list_faq > li",
            ".board_wrap li",
            ".board_wrap .faq_list li",
            ".board_list_wrap li",
            ".board_list_wrap .faq_list li",
            ".board_faq li",
            ".faq_board li",
            ".faq_wrap li",
            "ul li.question",
            "ul li.faq_item",
            "ul.result_list li",  # 추가된 선택자
            ".result_list li",    # 추가된 선택자
        ]
        
        faq_items = []
        selector_used = None
        
        for selector in selectors:
            items = driver.find_elements(By.CSS_SELECTOR, selector)
            print(f"  - {selector}: {len(items)}개 항목 발견")
            
            if items and len(items) > 0:
                faq_items = items
                selector_used = selector
                break
        
        # XPath로도 시도
        if not faq_items:
            try:
                xpath_items = driver.find_elements(By.XPATH, "//ul[contains(@class, 'faq') or contains(@class, 'result_list')]/li")
                print(f"  - XPath로 검색: {len(xpath_items)}개 항목 발견")
                if xpath_items and len(xpath_items) > 0:
                    faq_items = xpath_items
                    selector_used = "XPath: //ul[contains(@class, 'faq') or contains(@class, 'result_list')]/li"
            except:
                pass
        
        print(f"\nFAQ 항목 수: {len(faq_items)}")
        
        # FAQ 항목 정보 수집
        faq_details = []
        for i, item in enumerate(faq_items[:10]):  # 최대 10개만 분석
            try:
                item_info = {
                    "index": i,
                    "text": item.text.strip(),
                    "class": item.get_attribute("class")
                }
                
                # 링크 찾기
                links = item.find_elements(By.TAG_NAME, "a")
                if links:
                    item_info["link"] = links[0].get_attribute("href")
                
                # 제목 찾기
                title_elements = item.find_elements(By.CSS_SELECTOR, ".tit, .title, .subject, .question, h3, h4, strong, .result_tit")
                if title_elements:
                    item_info["title"] = title_elements[0].text.strip()
                
                # 내용 찾기
                content_elements = item.find_elements(By.CSS_SELECTOR, ".cont, .content, .answer, .desc, p, .result_txt")
                if content_elements:
                    item_info["content"] = content_elements[0].text.strip()
                
                faq_details.append(item_info)
                
            except Exception as e:
                print(f"  - 항목 {i+1} 분석 중 오류: {str(e)}")
        
        result["faq_items"] = faq_details
        result["faq_count"] = len(faq_items)
        result["faq_selector_used"] = selector_used
    
    def _analyze_page_structure(self, driver, result):
        """페이지 구조 분석"""
        print("\n페이지 구조 분석:")
        main_elements = [
            '.board_wrap', '.board_faq_list', '.board_list_faq', '.faq_list',
            '#content', '.content_wrap', '.board_list', '.board_view',
            '.board_list_wrap', '.board_list_wrap li', '.board_list_wrap .faq_list',
            '.board_list_wrap .faq_list li', '.board_faq', '.board_faq li',
            '.faq_board', '.faq_board li', '.faq_wrap', '.faq_wrap li'
        ]
        
        structure = {}
        for element in main_elements:
            items = driver.find_elements(By.CSS_SELECTOR, element)
            print(f"  - {element}: {len(items)}개 발견")
            
            if items:
                structure[element] = {
                    "count": len(items),
                    "class": items[0].get_attribute("class") if len(items) > 0 else ""
                }
        
        result["page_structure"] = structure
    
    def _check_pagination(self, driver, result):
        """페이지네이션 확인"""
        pagination = driver.find_elements(By.CSS_SELECTOR, '.paging a, .pagination a, .page_navi a')
        print(f"페이지네이션 링크 수: {len(pagination)}")
        
        pagination_details = []
        for i, page in enumerate(pagination[:15]):  # 최대 15개만 상세 분석
            try:
                page_info = {
                    "index": i,
                    "text": page.text,
                    "href": page.get_attribute("href"),
                    "class": page.get_attribute("class")
                }
                pagination_details.append(page_info)
            except:
                pass
        
        result["pagination_count"] = len(pagination)
        result["pagination"] = pagination_details
    
    def _analyze_all_elements(self, driver, result):
        """추가 분석 - 모든 요소 검색"""
        print("\n모든 li 요소 검색:")
        all_li = driver.find_elements(By.TAG_NAME, "li")
        print(f"  - 총 li 요소 수: {len(all_li)}")
        result["element_counts"]["li"] = len(all_li)
        
        # 텍스트를 포함한 li 요소 검색
        faq_keywords = ["FAQ", "faq", "질문", "답변", "간편검색"]
        print("\n키워드를 포함한 li 요소 검색:")
        
        keyword_results = {}
        for keyword in faq_keywords:
            try:
                elements = driver.find_elements(By.XPATH, f"//li[contains(text(), '{keyword}') or .//a[contains(text(), '{keyword}')]]")
                print(f"  - '{keyword}' 키워드 포함 요소: {len(elements)}개")
                
                element_details = []
                for i, elem in enumerate(elements[:3]):  # 최대 3개만 상세 분석
                    try:
                        element_info = {
                            "index": i,
                            "text": elem.text[:50] + "..." if len(elem.text) > 50 else elem.text,
                            "class": elem.get_attribute("class")
                        }
                        element_details.append(element_info)
                        print(f"    * 요소 {i+1}: {element_info['text']}")
                    except:
                        print(f"    * 요소 {i+1}: 텍스트 추출 실패")
                
                keyword_results[keyword] = {
                    "count": len(elements),
                    "details": element_details
                }
                
            except Exception as e:
                print(f"  - '{keyword}' 검색 오류: {str(e)}")
        
        result["keyword_elements"] = keyword_results
    
    def _analyze_page_source(self, driver, result):
        """페이지 소스 분석"""
        print("\n페이지 소스 분석:")
        html_content = driver.page_source
        
        # FAQ 관련 키워드 검색
        source_keywords = ["board_faq", "faq_list", "board_list_faq", "accordion", "toggle"]
        keyword_found = {}
        
        for keyword in source_keywords:
            found = keyword in html_content
            if found:
                print(f"  - '{keyword}' 키워드 발견")
            keyword_found[keyword] = found
        
        result["source_keywords"] = keyword_found
        result["html_sample"] = html_content[:5000]  # 처음 5000자만 저장
    
    def _analyze_detail_page(self, driver, result):
        """상세 페이지 분석"""
        print("\n상세 페이지 분석:")
        
        # FAQ 항목이 있는지 확인
        if not result.get("faq_items") or len(result["faq_items"]) == 0:
            print("  FAQ 항목이 없어서 상세 페이지 분석을 건너뜁니다.")
            return
        
        # 첫 번째 FAQ 항목의 링크 가져오기
        first_faq = result["faq_items"][0]
        detail_url = first_faq.get("link")
        
        if not detail_url:
            print("  상세 페이지 링크를 찾을 수 없습니다.")
            return
        
        print(f"  상세 페이지 URL: {detail_url}")
        
        try:
            # 상세 페이지로 이동
            driver.get(detail_url)
            time.sleep(3)  # 페이지 로딩 대기
            
            print(f"  상세 페이지 제목: {driver.title}")
            
            # 상세 페이지 구조 분석
            detail_analysis = {
                "url": detail_url,
                "title": driver.title,
                "content_selectors": [],
                "title_selectors": [],
                "main_content": ""
            }
            
            # 다양한 내용 선택자 시도
            content_selectors = [
                ".album_view_txt .p_txt",
                ".album_view_txt",
                ".content_area",
                ".faq_content",
                ".view_content", 
                ".board_view",
                ".board_content",
                ".view_txt",
                ".content_txt",
                ".question_content",
                ".answer_content",
                ".faq_answer",
                ".board_view_content",
                ".view_area .content",
                ".main_content",
                "#content .content",
                ".inner_content"
            ]
            
            print("  내용 선택자 테스트:")
            for selector in content_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        content = elements[0].text.strip()
                        if content and len(content) > 50:  # 충분한 내용이 있는 경우
                            selector_info = {
                                "selector": selector,
                                "element_count": len(elements),
                                "content_length": len(content),
                                "content_preview": content[:200] + "..." if len(content) > 200 else content
                            }
                            detail_analysis["content_selectors"].append(selector_info)
                            print(f"    ✓ {selector}: {len(elements)}개 요소, {len(content)}자")
                            
                            # 첫 번째 성공한 선택자의 내용을 메인 내용으로 저장
                            if not detail_analysis["main_content"]:
                                detail_analysis["main_content"] = content[:500] + "..." if len(content) > 500 else content
                        else:
                            print(f"    - {selector}: {len(elements)}개 요소, 내용 부족")
                    else:
                        print(f"    - {selector}: 요소 없음")
                except Exception as e:
                    print(f"    ✗ {selector}: 오류 - {str(e)}")
            
            # 제목 선택자 테스트
            title_selectors = [
                ".album_view_tit",
                ".view_title", 
                ".board_title",
                ".faq_title",
                ".question_title",
                "h1", "h2", "h3",
                ".title",
                ".subject"
            ]
            
            print("  제목 선택자 테스트:")
            for selector in title_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        title_text = elements[0].text.strip()
                        if title_text and len(title_text) > 5:  # 충분한 제목 텍스트
                            selector_info = {
                                "selector": selector,
                                "element_count": len(elements),
                                "title_text": title_text
                            }
                            detail_analysis["title_selectors"].append(selector_info)
                            print(f"    ✓ {selector}: {title_text[:100]}")
                        else:
                            print(f"    - {selector}: {len(elements)}개 요소, 제목 텍스트 부족")
                    else:
                        print(f"    - {selector}: 요소 없음")
                except Exception as e:
                    print(f"    ✗ {selector}: 오류 - {str(e)}")
            
            # 페이지 소스 저장 (상세 페이지)
            try:
                page_source = driver.page_source
                detail_html_path = os.path.join(self.results_dir, "detail_page_sample.html")
                with open(detail_html_path, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print(f"  상세 페이지 소스를 {detail_html_path}에 저장했습니다.")
                detail_analysis["html_saved"] = detail_html_path
            except Exception as e:
                print(f"  상세 페이지 소스 저장 중 오류: {str(e)}")
            
            result["detail_page_analysis"] = detail_analysis
            
            # 추천 선택자 결정
            if detail_analysis["content_selectors"]:
                best_content_selector = detail_analysis["content_selectors"][0]["selector"]
                print(f"\n  추천 내용 선택자: {best_content_selector}")
                result["recommended_content_selector"] = best_content_selector
            
            if detail_analysis["title_selectors"]:
                best_title_selector = detail_analysis["title_selectors"][0]["selector"]
                print(f"  추천 제목 선택자: {best_title_selector}")
                result["recommended_title_selector"] = best_title_selector
            
        except Exception as e:
            print(f"  상세 페이지 분석 중 오류: {str(e)}")
            import traceback
            print(f"  오류 상세: {traceback.format_exc()}")
            result["detail_page_analysis"] = {"error": str(e)}
    
    def _save_result(self, result):
        """분석 결과 저장"""
        # 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"knrec_faq_analysis_{timestamp}.json"
        
        # 결과 저장
        filepath = os.path.join(self.results_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n결과가 {filepath} 파일에 저장되었습니다.")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='KNREC 웹사이트 구조 분석')
    parser.add_argument('--url', default="https://www.knrec.or.kr/biz/faq/faq_list01.do", help='분석할 URL')
    parser.add_argument('--headless', action='store_true', help='헤드리스 모드 사용')
    parser.add_argument('--wait', type=int, default=5, help='페이지 로딩 대기 시간(초)')
    
    args = parser.parse_args()
    
    analyzer = KnrecAnalyzer(headless=args.headless)
    analyzer.analyze_faq_page(url=args.url, wait_time=args.wait)


if __name__ == "__main__":
    main()
