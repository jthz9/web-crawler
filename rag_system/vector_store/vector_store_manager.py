import os
from typing import List, Dict, Any, Optional
from ..embedding.ko_embedding import KoreanEmbeddingModel
from .chroma_store import ChromaVectorStore
from ..utils.logger import get_logger

logger = get_logger(__name__)

class VectorStoreManager:
    """벡터 저장소 매니저 클래스"""
    
    def __init__(self):
        """초기화"""
        self.embedding_model = KoreanEmbeddingModel()
        self.vector_store = ChromaVectorStore()
        self.initialize()
        
    def initialize(self) -> None:
        """벡터 저장소 초기화"""
        try:
            self.vector_store.initialize()
            logger.info("벡터 저장소 초기화 완료")
        except Exception as e:
            logger.error(f"벡터 저장소 초기화 실패: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """문서 추가
        
        Args:
            documents: 추가할 문서 리스트. 각 문서는 title, content, metadata를 포함
        """
        try:
            # 문서 임베딩 생성
            texts = [f"{doc['title']} {doc['content']}" for doc in documents]
            embeddings = self.embedding_model.get_embeddings(texts)
            
            # 벡터 저장소에 추가
            self.vector_store.add_documents(documents, embeddings)
            logger.info(f"{len(documents)}개 문서 추가 완료")
        except Exception as e:
            logger.error(f"문서 추가 실패: {str(e)}")
            raise
    
    def search(self, query: str, n_results: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """문서 검색
        
        Args:
            query: 검색 쿼리
            n_results: 반환할 결과 수
            filters: 메타데이터 필터링 조건
            
        Returns:
            검색 결과 리스트. 각 결과는 title, content, score를 포함
        """
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.embedding_model.get_embedding(query)
            
            # 벡터 저장소에서 검색
            results = self.vector_store.search(
                query_embedding=query_embedding,
                n_results=n_results,
                filters=filters
            )
            
            logger.info(f"검색 완료: {len(results)}개 결과 반환")
            return results
        except Exception as e:
            logger.error(f"검색 실패: {str(e)}")
            raise
    
    def delete_collection(self) -> None:
        """컬렉션 삭제"""
        try:
            self.vector_store.delete_collection()
            logger.info("컬렉션 삭제 완료")
        except Exception as e:
            logger.error(f"컬렉션 삭제 실패: {str(e)}")
            raise 