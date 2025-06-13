import json
import os
from typing import List, Dict, Any
from ..vector_store.vector_store_manager import VectorStoreManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

def load_faq_data(file_path: str) -> List[Dict[str, Any]]:
    """FAQ 데이터 로드
    
    Args:
        file_path: FAQ 데이터 파일 경로
        
    Returns:
        FAQ 데이터 리스트
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"FAQ 데이터 로드 완료: {len(data)}개 항목")
        return data
    except Exception as e:
        logger.error(f"FAQ 데이터 로드 실패: {str(e)}")
        raise

def test_vector_store():
    """벡터 저장소 테스트"""
    try:
        # FAQ 데이터 로드
        faq_data = load_faq_data("output/sample_faq.json")
        logger.info(f"FAQ 데이터 로드 완료: {len(faq_data)}개 항목")

        # 벡터 저장소 매니저 초기화
        manager = VectorStoreManager()
        logger.info("벡터 저장소 매니저 초기화 완료")

        # 기존 컬렉션 삭제
        manager.vector_store.delete_collection()
        logger.info("기존 컬렉션 삭제 완료")

        # 문서 추가
        manager.add_documents(faq_data)
        logger.info("문서 추가 완료")

        # 기본 검색 테스트
        query = "태양광 발전소 설치 비용은 얼마인가요?"
        results = manager.search(query)
        logger.info("\n=== 기본 검색 결과 ===")
        for i, result in enumerate(results, 1):
            logger.info(f"\n결과 {i}:")
            logger.info(f"제목: {result['title']}")
            logger.info(f"내용: {result['content']}")
            logger.info(f"유사도: {result['similarity']:.4f}")

        # 카테고리 필터링 테스트
        category_filters = {"category": ["주택지원", "금융지원"]}
        category_results = manager.search(query, filters=category_filters)
        logger.info("\n=== 카테고리 필터링 검색 결과 ===")
        for i, result in enumerate(category_results, 1):
            logger.info(f"\n결과 {i}:")
            logger.info(f"제목: {result['title']}")
            logger.info(f"카테고리: {result['category']}")
            logger.info(f"유사도: {result['similarity']:.4f}")

        # 날짜 필터링 테스트
        date_filters = {"date": "2024-06-13"}
        date_results = manager.search(query, filters=date_filters)
        logger.info("\n=== 날짜 필터링 검색 결과 ===")
        for i, result in enumerate(date_results, 1):
            logger.info(f"\n결과 {i}:")
            logger.info(f"제목: {result['title']}")
            logger.info(f"날짜: {result['date']}")
            logger.info(f"유사도: {result['similarity']:.4f}")

        # 복합 필터링 테스트
        complex_filters = {
            "category": ["주택지원"],
            "source": "KNREC"
        }
        complex_results = manager.search(query, filters=complex_filters)
        logger.info("\n=== 복합 필터링 검색 결과 ===")
        for i, result in enumerate(complex_results, 1):
            logger.info(f"\n결과 {i}:")
            logger.info(f"제목: {result['title']}")
            logger.info(f"카테고리: {result['category']}")
            logger.info(f"출처: {result['source']}")
            logger.info(f"유사도: {result['similarity']:.4f}")

    except Exception as e:
        logger.error(f"테스트 실패: {str(e)}")
        raise

if __name__ == "__main__":
    test_vector_store() 