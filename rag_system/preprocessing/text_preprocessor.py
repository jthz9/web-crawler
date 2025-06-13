"""
RAG 시스템을 위한 텍스트 전처리 모듈
한국어 FAQ 데이터를 정제하고 구조화합니다.
"""

import re
import json
import pandas as pd
from typing import List, Dict, Tuple
from pathlib import Path
import html
from datetime import datetime

class KoreanTextPreprocessor:
    """한국어 텍스트 전처리 클래스"""
    
    def __init__(self):
        """초기화"""
        # 한국어 불용어 리스트
        self.stopwords = {
            '그리고', '또한', '하지만', '그러나', '따라서', '즉', '예를 들어',
            '입니다', '있습니다', '합니다', '됩니다', '습니다', '것입니다',
            '이는', '이것', '그것', '저것', '여기', '거기', '저기',
            '이런', '그런', '저런', '이렇게', '그렇게', '저렇게',
            '매우', '정말', '너무', '상당히', '꽤', '아주',
            '등등', '기타', '외에', '이외', '제외하고'
        }
        
        # HTML 엔티티 매핑
        self.html_entities = {
            '&nbsp;': ' ',
            '&amp;': '&',
            '&lt;': '<',
            '&gt;': '>',
            '&quot;': '"',
            '&#39;': "'",
            '&middot;': '·',
            '&bull;': '•'
        }
    
    def clean_html(self, text: str) -> str:
        """HTML 태그 및 엔티티 제거"""
        if not text:
            return ""
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # HTML 엔티티 변환
        text = html.unescape(text)
        for entity, replacement in self.html_entities.items():
            text = text.replace(entity, replacement)
        
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """공백 정규화"""
        if not text:
            return ""
        
        # 연속된 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        # 문장 끝 정리
        text = re.sub(r'[.]{2,}', '.', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[!]{2,}', '!', text)
        
        return text
    
    def clean_special_chars(self, text: str) -> str:
        """특수문자 정리"""
        if not text:
            return ""
        
        # 불필요한 특수문자 제거 (한글, 영문, 숫자, 기본 문장부호만 유지)
        text = re.sub(r'[^\w\s가-힣.,!?()[\]{}:;"\'-]', ' ', text)
        
        # 연속된 구두점 정리
        text = re.sub(r'[.,!?]{3,}', '...', text)
        
        return text
    
    def extract_keywords(self, text: str) -> List[str]:
        """간단한 키워드 추출 (형태소 분석 없이)"""
        if not text:
            return []
        
        # 2글자 이상의 한글 단어 추출
        words = re.findall(r'[가-힣]{2,}', text)
        
        # 불용어 제거
        keywords = [word for word in words if word not in self.stopwords]
        
        # 중복 제거 및 빈도순 정렬
        from collections import Counter
        word_counts = Counter(keywords)
        
        return [word for word, count in word_counts.most_common(10)]
    
    def chunk_text(self, text: str, max_length: int = 300) -> List[str]:
        """텍스트를 의미 단위로 분할"""
        if not text or len(text) <= max_length:
            return [text] if text else []
        
        # 문장 단위로 분할
        sentences = re.split(r'[.!?]\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 현재 청크에 추가해도 길이 제한을 넘지 않으면 추가
            if len(current_chunk + sentence) <= max_length:
                current_chunk += sentence + ". "
            else:
                # 현재 청크를 저장하고 새 청크 시작
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        # 마지막 청크 추가
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def process_faq(self, faq_item: Dict) -> Dict:
        """단일 FAQ 아이템 전처리"""
        processed = faq_item.copy()
        
        # 제목 전처리
        if 'title' in processed:
            title = processed['title']
            title = self.clean_html(title)
            title = self.normalize_whitespace(title)
            title = self.clean_special_chars(title)
            processed['title_cleaned'] = title
        
        # 내용 전처리
        if 'content' in processed:
            content = processed['content']
            content = self.clean_html(content)
            content = self.normalize_whitespace(content)
            content = self.clean_special_chars(content)
            processed['content_cleaned'] = content
            
            # 키워드 추출
            processed['keywords'] = self.extract_keywords(content)
            
            # 텍스트 청킹
            processed['chunks'] = self.chunk_text(content)
            processed['chunk_count'] = len(processed['chunks'])
        
        # 결합된 텍스트 (제목 + 내용)
        combined_text = ""
        if 'title_cleaned' in processed:
            combined_text += processed['title_cleaned'] + " "
        if 'content_cleaned' in processed:
            combined_text += processed['content_cleaned']
        
        processed['combined_text'] = combined_text.strip()
        processed['text_length'] = len(combined_text)
        
        # 처리 시간 기록
        processed['preprocessed_at'] = datetime.now().isoformat()
        
        return processed

class FAQPreprocessor:
    """FAQ 데이터셋 전체 전처리 클래스"""
    
    def __init__(self):
        self.text_processor = KoreanTextPreprocessor()
        self.stats = {}
    
    def load_data(self, file_path: str) -> List[Dict]:
        """FAQ 데이터 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 데이터 로드 완료: {len(data)}개 FAQ")
            return data
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return []
    
    def preprocess_dataset(self, data: List[Dict]) -> List[Dict]:
        """전체 데이터셋 전처리"""
        print("🔄 텍스트 전처리 시작...")
        
        processed_data = []
        original_lengths = []
        processed_lengths = []
        
        for i, faq in enumerate(data):
            if i % 50 == 0:
                print(f"진행률: {i}/{len(data)} ({i/len(data)*100:.1f}%)")
            
            # 원본 길이 기록
            original_text = (faq.get('title', '') + ' ' + faq.get('content', '')).strip()
            original_lengths.append(len(original_text))
            
            # 전처리 수행
            processed_faq = self.text_processor.process_faq(faq)
            processed_data.append(processed_faq)
            
            # 처리 후 길이 기록
            processed_lengths.append(processed_faq.get('text_length', 0))
        
        # 통계 계산
        self.stats = {
            'total_count': len(processed_data),
            'original_avg_length': sum(original_lengths) / len(original_lengths) if original_lengths else 0,
            'processed_avg_length': sum(processed_lengths) / len(processed_lengths) if processed_lengths else 0,
            'total_chunks': sum(faq.get('chunk_count', 0) for faq in processed_data),
            'avg_chunks_per_faq': sum(faq.get('chunk_count', 0) for faq in processed_data) / len(processed_data) if processed_data else 0
        }
        
        print("✅ 텍스트 전처리 완료!")
        return processed_data
    
    def remove_duplicates(self, data: List[Dict]) -> List[Dict]:
        """중복 제거"""
        print("🔄 중복 제거 시작...")
        
        seen_texts = set()
        unique_data = []
        duplicate_count = 0
        
        for faq in data:
            combined_text = faq.get('combined_text', '')
            
            # 텍스트 길이와 첫 50자로 간단한 중복 검사
            text_signature = f"{len(combined_text)}_{combined_text[:50]}"
            
            if text_signature not in seen_texts:
                seen_texts.add(text_signature)
                unique_data.append(faq)
            else:
                duplicate_count += 1
        
        print(f"✅ 중복 제거 완료: {duplicate_count}개 중복 제거, {len(unique_data)}개 유지")
        return unique_data
    
    def save_processed_data(self, data: List[Dict], output_path: str) -> str:
        """전처리된 데이터 저장"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 전처리된 데이터 저장: {output_path}")
            return output_path
        except Exception as e:
            print(f"❌ 데이터 저장 실패: {e}")
            return ""
    
    def generate_preprocessing_report(self, output_path: str = None) -> str:
        """전처리 보고서 생성"""
        if output_path is None:
            output_path = f"preprocessing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        report = []
        report.append("=" * 60)
        report.append("텍스트 전처리 보고서")
        report.append("=" * 60)
        report.append(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        if self.stats:
            report.append("📊 전처리 통계")
            report.append("-" * 30)
            report.append(f"총 FAQ 수: {self.stats['total_count']}")
            report.append(f"원본 평균 길이: {self.stats['original_avg_length']:.1f}자")
            report.append(f"처리 후 평균 길이: {self.stats['processed_avg_length']:.1f}자")
            report.append(f"총 청크 수: {self.stats['total_chunks']}")
            report.append(f"FAQ당 평균 청크 수: {self.stats['avg_chunks_per_faq']:.1f}개")
        
        report_text = "\n".join(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(f"✅ 전처리 보고서 생성: {output_path}")
        return report_text


def main():
    """메인 실행 함수"""
    print("🔄 FAQ 텍스트 전처리 시작")
    
    # 입출력 파일 경로
    input_file = "crawler/output/data/knrec_faq_20250611_181612.json"
    output_file = f"rag_system/processed_faq_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    if not Path(input_file).exists():
        print(f"❌ 입력 파일을 찾을 수 없습니다: {input_file}")
        return
    
    # 전처리기 초기화
    preprocessor = FAQPreprocessor()
    
    # 데이터 로드
    data = preprocessor.load_data(input_file)
    if not data:
        return
    
    # 전처리 수행
    processed_data = preprocessor.preprocess_dataset(data)
    
    # 중복 제거
    unique_data = preprocessor.remove_duplicates(processed_data)
    
    # 저장
    preprocessor.save_processed_data(unique_data, output_file)
    
    # 보고서 생성
    report = preprocessor.generate_preprocessing_report()
    print("\n" + "="*50)
    print("📊 전처리 결과 요약")
    print("="*50)
    print(report)


if __name__ == "__main__":
    main() 