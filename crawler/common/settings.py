"""
공통 설정 모듈
모든 단계에서 공유하는 설정을 정의합니다.
"""

# 기본 Scrapy 설정
BOT_NAME = "scrapy_selenium"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
ROBOTSTXT_OBEY = False
FEED_EXPORT_ENCODING = "utf-8"
FEED_STORE_EMPTY = False  # 빈 파일 저장 방지

# 병렬 처리 설정
CONCURRENT_REQUESTS = 1  # 기본값은 낮게 설정 (테스트 모드용)
DOWNLOAD_DELAY = 1  # 기본 다운로드 딜레이 (초)

# Selenium 미들웨어 설정
SELENIUM_MIDDLEWARE = {
    'crawler.crawler.middlewares.SeleniumMiddleware': 800,
}

# Selenium 관련 설정
SELENIUM_TIMEOUT = 15  # 셀레니움 타임아웃 (초)
SELENIUM_DRIVER_NAME = 'chrome'
SELENIUM_DRIVER_EXECUTABLE_PATH = None  # webdriver_manager가 자동으로 관리
SELENIUM_DRIVER_ARGUMENTS = ['--headless', '--no-sandbox', '--disable-dev-shm-usage']
SELENIUM_BROWSER_EXECUTABLE_PATH = None

# 파이프라인 설정
DEFAULT_PIPELINES = {
    'crawler.crawler.pipelines.RenewableEnergyPipeline': 300,
}

FULL_PIPELINES = {
    'crawler.crawler.pipelines.RenewableEnergyPipeline': 300,
    'crawler.crawler.pipelines.FileDownloadPipeline': 500,
}

# 파일 저장 경로 설정
FILES_STORE = './crawler/data/files'

# 로그 설정
LOG_ENABLED = True
LOG_LEVEL = 'INFO'
LOG_FILE = './crawler/logs/scrapy.log'

# 기본 출력 파일 설정
FEED_URI = './crawler/results/%(spider)s_%(time)s.json'
FEED_FORMAT = 'json'

# 테스트 모드 설정
TEST_MODE_SETTINGS = {
    'LOG_LEVEL': 'INFO',
    'CONCURRENT_REQUESTS': 1,
    'DOWNLOAD_DELAY': 1,
    'ITEM_PIPELINES': DEFAULT_PIPELINES,
}

# 실제 크롤링 모드 설정
FULL_MODE_SETTINGS = {
    'LOG_LEVEL': 'INFO',
    'CONCURRENT_REQUESTS': 4,
    'DOWNLOAD_DELAY': 2,
    'ITEM_PIPELINES': FULL_PIPELINES,
}

# 공통 다운로더 미들웨어 설정
DOWNLOADER_MIDDLEWARES = {
    'crawler.crawler.middlewares.SeleniumMiddleware': 800,
} 