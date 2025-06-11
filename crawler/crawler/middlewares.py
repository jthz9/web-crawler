# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time


class CrawlerSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # maching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class CrawlerDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

class SeleniumMiddleware:
    """Scrapy middleware using selenium"""

    def __init__(self, timeout=15):
        self.timeout = timeout

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls(
            timeout=crawler.settings.get('SELENIUM_TIMEOUT', 15)
        )
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_opened(self, spider):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        chrome_options.add_argument(f"user-agent={user_agent}")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(self.timeout)
        spider.logger.info("SeleniumMiddleware - Chrome driver initialized")
    
    def spider_closed(self, spider):
        if hasattr(self, 'driver'):
            self.driver.quit()
            spider.logger.info("SeleniumMiddleware - Chrome driver closed")

    def process_request(self, request, spider):
        if not request.meta.get('selenium', False):
            return None
        spider.logger.info(f"SeleniumMiddleware - Processing request: {request.url}")

        try:
            self.driver.get(request.url)
            # 페이지 로딩 대기
            wait_time = request.meta.get('wait_time', 3)
            spider.logger.info(f"페이지 로딩 대기 시간: {wait_time}초")
            time.sleep(wait_time)
            # 스크롤
            if request.meta.get('scroll', False):
                self.scroll_to_bottom(self.driver)
            # 특정 요소 대기
            if 'wait_for' in request.meta:
                self.wait_for_element(self.driver, request.meta['wait_for'])
            # 페이지 HTML 소스 가져오기
            body = self.driver.page_source
            # 드라이버 객체를 메타에 추가
            request.meta['driver'] = self.driver
            spider.logger.info("셀레니움 드라이버를 메타에 추가했습니다.")
            # HtmlResponse 반환
            return HtmlResponse(
                url=request.url,
                body=body,
                encoding='utf-8',
                request=request,
                status=200
            )
        except Exception as e:
            spider.logger.error(f"SeleniumMiddleware - Error processing request: {e}")
            import traceback
            spider.logger.error(traceback.format_exc())
            return None
    
    def scroll_to_bottom(self, driver):
        """스크롤을 페이지 하단까지 내리는 함수"""
        last_height = driver.execute_script("return document.body.scrollHeight")
    
        while True:
            # 페이지 하단으로 스크롤
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")        
            # 페이지 로딩 대기
            time.sleep(2)
            # 새 스크롤 높이 계산
            new_height = driver.execute_script("return document.body.scrollHeight")
            # 스크롤 높이가 더 이상 변하지 않으면 종료
            if new_height == last_height:
                break
            last_height = new_height

    def wait_for_element(self, driver, selector):
        """특정 요소가 로드될 때까지 대기하는 함수"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
        except Exception as e:
            print(f"요소를 찾을 수 없습니다: {e}")