# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
import os
import json
import re
from datetime import datetime


class CrawlerPipeline:
    def process_item(self, item, spider):
        return item

class RenewableEnergyPipeline:
    """
    재생에너지 데이터를 처리하고 저장하는 파이프라인
    """
    def __init__(self):
        self.ids_seen = set()
        self.file = None

    def open_spider(self, spider):
        # 저장 디렉토리 생성
        self.data_dir = './output/data'
        os.makedirs(self.data_dir, exist_ok=True)

        # 파일명에 스파이더 이름과 타임스탬프 사용
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{spider.name}_{timestamp}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        self.file = open(filepath, 'w', encoding='utf-8')
        self.file.write('[\n')
        self.first_item = True
        
        spider.logger.info(f"결과를 {filepath} 파일에 저장합니다.")

    def close_spider(self, spider):
        if self.file:
            self.file.write('\n]')
            self.file.close()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        url = adapter.get('url')
        if url in self.ids_seen:
            raise DropItem(f"Duplicate item found: {item['url']}")
        self.ids_seen.add(url)
        
        # 크롤링 시간 추가
        adapter['crawled_at'] = datetime.now().isoformat()
        
        # 텍스트 정리
        if 'title' in adapter:
            adapter['title'] = self._clean_text(adapter['title'])
        if 'content' in adapter:
            adapter['content'] = self._clean_text(adapter['content'])

        # JSON으로 저장
        line = json.dumps(ItemAdapter(item).asdict(), ensure_ascii=False)
        if self.first_item:
            self.first_item = False
        else:
            self.file.write(',\n')
        self.file.write(line)
        
        return item 

    def _clean_text(self, text):
        if not text:
            return ""
        # 여러 공백을 하나로 치환
        import re
        text = re.sub(r'\s+', ' ', text).strip()
        return text

class FileDownloadPipeline:
    """
    첨부 파일을 다운로드하는 파이프라인
    """
    
    def __init__(self, files_dir):
        self.files_dir = files_dir
        
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            files_dir=crawler.settings.get('FILES_STORE', 'files')
        )
        
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if 'file_urls' in adapter and adapter['file_urls']:
            import requests
            import os
            
            for url in adapter['file_urls']:
                try:
                    # 파일명 추출
                    filename = url.split('/')[-1]
                    save_path = os.path.join(self.files_dir, filename)
                    
                    # 디렉토리 생성
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    
                    # 파일 다운로드
                    response = requests.get(url, stream=True)
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            
                    spider.logger.info(f'파일 다운로드 완료: {save_path}')
                except Exception as e:
                    spider.logger.error(f'파일 다운로드 실패: {url}, 오류: {e}')
        
        return item