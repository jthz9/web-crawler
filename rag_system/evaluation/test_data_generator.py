import json
import random
from typing import List, Dict, Any
from tqdm import tqdm

class TestDataGenerator:
    def __init__(self, faq_data: List[Dict[str, Any]], num_negatives: int = 4):
        """테스트 데이터 생성기를 초기화합니다.
        
        Args:
            faq_data (List[Dict[str, Any]]): FAQ 데이터 리스트
            num_negatives (int, optional): 각 쿼리당 오답 샘플 수. 기본값은 4.
        """
        self.faq_data = faq_data
        self.num_negatives = num_negatives
        
    def generate_paraphrase(self, title: str) -> str:
        """FAQ 제목을 기반으로 간단한 paraphrase를 생성합니다.
        
        Args:
            title (str): 원본 FAQ 제목
            
        Returns:
            str: Paraphrase된 질문
        """
        # 기본적인 paraphrase 규칙
        paraphrases = [
            f"{title}에 대해 알려주세요",
            f"{title}이 궁금합니다",
            f"{title}에 대한 정보를 알고 싶어요",
            f"{title}에 대해서 설명해주세요"
        ]
        return random.choice(paraphrases)
        
    def generate_test_data(self, num_samples: int = 100) -> List[Dict[str, Any]]:
        """평가용 테스트 데이터를 생성합니다.
        
        Args:
            num_samples (int, optional): 생성할 샘플 수. 기본값은 100.
            
        Returns:
            List[Dict[str, Any]]: 테스트 데이터 리스트
        """
        test_data = []
        
        # 샘플링할 FAQ 선택
        selected_faqs = random.sample(self.faq_data, min(num_samples, len(self.faq_data)))
        
        for faq in tqdm(selected_faqs, desc="Generating test data"):
            # 정답 문서
            relevant = faq["content_cleaned"]
            
            # 오답 문서 선택 (자기 자신 제외)
            negative_samples = [
                f["content_cleaned"] 
                for f in self.faq_data 
                if f["content_cleaned"] != relevant
            ]
            negative_samples = random.sample(negative_samples, self.num_negatives)
            
            # 후보 문서 구성 (정답 + 오답)
            candidates = [relevant] + negative_samples
            
            # 쿼리 생성 (원본 + paraphrase)
            original_query = faq["title_cleaned"]
            paraphrase_query = self.generate_paraphrase(original_query)
            
            # 테스트 케이스 추가
            test_data.extend([
                {
                    "query": original_query,
                    "relevant_docs": candidates,
                    "query_type": "original"
                },
                {
                    "query": paraphrase_query,
                    "relevant_docs": candidates,
                    "query_type": "paraphrase"
                }
            ])
            
        return test_data

def main():
    # FAQ 데이터 로드
    with open("rag_system/preprocessing/processed_data/processed_faq_20250612_105658.json", "r") as f:
        faq_data = json.load(f)
    
    # 테스트 데이터 생성
    generator = TestDataGenerator(faq_data)
    test_data = generator.generate_test_data()
    
    # 결과 저장
    with open("rag_system/evaluation/test_data.json", "w") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)
    
    print(f"생성된 테스트 데이터 수: {len(test_data)}")
    print(f"원본 쿼리 수: {len([d for d in test_data if d['query_type'] == 'original'])}")
    print(f"Paraphrase 쿼리 수: {len([d for d in test_data if d['query_type'] == 'paraphrase'])}")

if __name__ == "__main__":
    main() 