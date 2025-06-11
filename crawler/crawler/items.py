# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CrawlerItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

import scrapy

class RenewableEnergyItem(scrapy.Item):
    """
    신재생에너지 관련 문서 아이템
    필수 필드만 포함하도록 간소화됨
    """
    # 필수 필드 (항상 채워야 함)
    title = scrapy.Field()          # 제목
    content = scrapy.Field()        # 내용
    url = scrapy.Field()            # 원본 URL
    date_published = scrapy.Field() # 발행일
    source = scrapy.Field()         # 출처 (웹사이트 이름)
    document_type = scrapy.Field()  # 문서 유형 (공지사항, 뉴스, 사업공고 등)
    
    # 선택적 필드 (가능한 경우에만 채움)
    post_no = scrapy.Field()        # 게시글 번호 (중복 확인용)
    page = scrapy.Field()           # 페이지 번호 (페이지네이션에서 몇 번째 페이지인지)
    
    # 첨부 파일 (필요한 경우에만 사용)
    file_urls = scrapy.Field()      # 첨부 파일 URL 목록
    files = scrapy.Field()          # 다운로드된 파일 정보
    
    # 메타 필드 (자동으로 채워짐)
    crawled_at = scrapy.Field()     # 크롤링 시간
    spider = scrapy.Field()         # 스파이더 이름
    
    # 아래 필드들은 현재 사용하지 않음
    # energy_type = scrapy.Field()    # 에너지 유형 (태양광, 풍력, 수소 등)
    # is_notice = scrapy.Field()      # 공지 게시글 여부
    # spider_version = scrapy.Field() # 스파이더 버전

