"""
웹사이트 HTML 구조 분석 모듈
"""
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import os
from datetime import datetime

class HTMLAnalyzer:
    """
    웹사이트 HTML 구조를 분석하는 클래스
    """
    def __init__(self, headless=False):
        """
        HTMLAnalyzer 초기화
        
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
        self.chrome_options.add_argument("--disable-popup-blocking")
        self.chrome_options.add_argument("--disable-notifications")
        self.chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3")
        
        # 결과 저장 경로
        self.results_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analysis', 'results', 'html')
        os.makedirs(self.results_dir, exist_ok=True)
        
    def analyze(self, url, wait_time=5):
        """
        URL의 HTML 구조를 분석
        
        Args:
            url (str): 분석할 웹사이트 URL
            wait_time (int): 페이지 로딩 대기 시간(초)
            
        Returns:
            dict: 분석 결과
        """
        print(f"URL 분석: {url}")
        
        # 드라이버 초기화
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)
        
        try:
            # 페이지 로딩
            driver.get(url)
            time.sleep(wait_time)  # 페이지 로딩 대기
            
            # HTML 구조 분석 결과
            result = {
                "url": url,
                "title": driver.title,
                "timestamp": datetime.now().isoformat(),
                "elements": {}
            }
            
            # 테이블 확인
            tables = driver.find_elements(By.CSS_SELECTOR, "table")
            result["elements"]["tables"] = {
                "count": len(tables),
                "details": self._analyze_tables(tables)
            }
            
            # 폼 확인
            forms = driver.find_elements(By.CSS_SELECTOR, "form")
            result["elements"]["forms"] = {
                "count": len(forms),
                "details": self._analyze_forms(forms)
            }
            
            # 리스트 확인
            lists = driver.find_elements(By.CSS_SELECTOR, "ul, ol")
            result["elements"]["lists"] = {
                "count": len(lists),
                "details": self._analyze_lists(lists)
            }
            
            # iframe 확인
            iframes = driver.find_elements(By.CSS_SELECTOR, "iframe")
            result["elements"]["iframes"] = {
                "count": len(iframes),
                "details": self._analyze_iframes(iframes)
            }
            
            # 페이지네이션 확인
            paginations = driver.find_elements(By.CSS_SELECTOR, ".pagination, .paging, nav ul li a")
            result["elements"]["pagination"] = {
                "count": len(paginations),
                "details": self._analyze_pagination(paginations)
            }
            
            # 결과 저장
            self._save_result(result, url)
            
            return result
            
        finally:
            driver.quit()
    
    def _analyze_tables(self, tables):
        """테이블 분석"""
        table_details = []
        for i, table in enumerate(tables[:5]):  # 최대 5개만 분석
            try:
                rows = table.find_elements(By.CSS_SELECTOR, "tr")
                headers = table.find_elements(By.CSS_SELECTOR, "th")
                
                table_details.append({
                    "index": i,
                    "rows": len(rows),
                    "headers": len(headers),
                    "class": table.get_attribute("class"),
                    "id": table.get_attribute("id")
                })
            except:
                pass
        return table_details
    
    def _analyze_forms(self, forms):
        """폼 분석"""
        form_details = []
        for i, form in enumerate(forms[:5]):  # 최대 5개만 분석
            try:
                inputs = form.find_elements(By.CSS_SELECTOR, "input")
                selects = form.find_elements(By.CSS_SELECTOR, "select")
                buttons = form.find_elements(By.CSS_SELECTOR, "button")
                
                form_details.append({
                    "index": i,
                    "inputs": len(inputs),
                    "selects": len(selects),
                    "buttons": len(buttons),
                    "action": form.get_attribute("action"),
                    "method": form.get_attribute("method"),
                    "class": form.get_attribute("class"),
                    "id": form.get_attribute("id")
                })
            except:
                pass
        return form_details
    
    def _analyze_lists(self, lists):
        """리스트 분석"""
        list_details = []
        for i, list_elem in enumerate(lists[:10]):  # 최대 10개만 분석
            try:
                items = list_elem.find_elements(By.CSS_SELECTOR, "li")
                
                list_details.append({
                    "index": i,
                    "type": list_elem.tag_name,
                    "items": len(items),
                    "class": list_elem.get_attribute("class"),
                    "id": list_elem.get_attribute("id")
                })
            except:
                pass
        return list_details
    
    def _analyze_iframes(self, iframes):
        """iframe 분석"""
        iframe_details = []
        for i, iframe in enumerate(iframes):
            try:
                iframe_details.append({
                    "index": i,
                    "src": iframe.get_attribute("src"),
                    "width": iframe.get_attribute("width"),
                    "height": iframe.get_attribute("height"),
                    "class": iframe.get_attribute("class"),
                    "id": iframe.get_attribute("id")
                })
            except:
                pass
        return iframe_details
    
    def _analyze_pagination(self, paginations):
        """페이지네이션 분석"""
        pagination_details = []
        for i, page in enumerate(paginations[:20]):  # 최대 20개만 분석
            try:
                pagination_details.append({
                    "index": i,
                    "text": page.text,
                    "href": page.get_attribute("href"),
                    "class": page.get_attribute("class")
                })
            except:
                pass
        return pagination_details
    
    def _save_result(self, result, url):
        """분석 결과 저장"""
        # URL에서 파일명 생성
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.replace(".", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{domain}_{timestamp}.json"
        
        # 결과 저장
        filepath = os.path.join(self.results_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"분석 결과가 {filepath}에 저장되었습니다.")


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='웹사이트 HTML 구조 분석')
    parser.add_argument('url', help='분석할 웹사이트 URL')
    parser.add_argument('--headless', action='store_true', help='헤드리스 모드 사용')
    parser.add_argument('--wait', type=int, default=5, help='페이지 로딩 대기 시간(초)')
    
    args = parser.parse_args()
    
    analyzer = HTMLAnalyzer(headless=args.headless)
    analyzer.analyze(args.url, wait_time=args.wait)


if __name__ == "__main__":
    main()
