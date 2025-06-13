import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from .base import BaseVectorStore
from ..utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)

class ChromaVectorStore(BaseVectorStore):
    """ChromaDB를 사용하는 벡터 저장소 구현체"""
    
    def __init__(self, collection_name: str = "faq_collection"):
        """초기화
        
        Args:
            collection_name: 컬렉션 이름
        """
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.logger = get_logger(__name__)
        
    def initialize(self) -> None:
        """ChromaDB 클라이언트 초기화 및 컬렉션 생성"""
        try:
            self.client = chromadb.HttpClient(
                host=os.getenv("CHROMA_HOST", "localhost"),
                port=int(os.getenv("CHROMA_PORT", "8000"))
            )
            try:
                self.collection = self.client.get_collection(self.collection_name)
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "FAQ 데이터를 저장하는 컬렉션"}
                )
            self.logger.info(f"ChromaDB 컬렉션 '{self.collection_name}' 초기화 완료")
        except Exception as e:
            self.logger.error(f"ChromaDB 초기화 실패: {str(e)}")
            raise
    
    def add_documents(self, 
                     documents: List[Dict[str, Any]], 
                     embeddings: List[List[float]]) -> None:
        """문서 추가
        
        Args:
            documents: 추가할 문서 리스트
            embeddings: 문서 임베딩 리스트
        """
        try:
            ids = [str(i) for i in range(len(documents))]
            metadatas = [{
                "category": doc.get("category", "기타"),
                "date": doc.get("date", datetime.now().strftime("%Y-%m-%d")),
                "source": doc.get("source", "KNREC"),
                "title": doc.get("title", ""),
                "content": doc.get("content", "")
            } for doc in documents]
            
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas
            )
            self.logger.info(f"{len(documents)}개의 문서 추가 완료")
        except Exception as e:
            self.logger.error(f"문서 추가 실패: {str(e)}")
            raise
    
    def search(self, 
              query_embedding: List[float], 
              n_results: int = 5,
              filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """쿼리 임베딩을 사용하여 가장 관련성 높은 문서 검색
        
        Args:
            query_embedding: 쿼리 임베딩
            n_results: 반환할 결과 수
            filters: 메타데이터 필터링 조건
            
        Returns:
            검색 결과 리스트
        """
        try:
            # 1. 필터가 없는 경우 기본 검색
            if not filters:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=n_results
                )
                return self._format_results(results)
            
            # 2. 복합 필터 처리
            # 2.1 첫 번째 필드로 ChromaDB 쿼리
            first_field = next(iter(filters))
            first_value = filters[first_field]
            
            # 2.2 나머지 필드들을 후처리용으로 저장
            remaining_filters = {k: v for k, v in filters.items() if k != first_field}
            
            # 2.3 ChromaDB 쿼리 (넉넉한 결과 수로 조회)
            where = {}
            if isinstance(first_value, list):
                where[first_field] = {"$in": first_value}
            else:
                where[first_field] = first_value
                
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results * 3,  # 넉넉히 가져옴
                where=where
            )
            
            # 2.4 후처리 필터링
            filtered_results = []
            for metadata, distance in zip(results["metadatas"][0], results["distances"][0]):
                # 나머지 필터 조건 검사
                if all(
                    (metadata.get(k) in v if isinstance(v, list) else metadata.get(k) == v)
                    for k, v in remaining_filters.items()
                ):
                    filtered_results.append({
                        "title": metadata.get("title", ""),
                        "content": metadata.get("content", ""),
                        "category": metadata.get("category", ""),
                        "date": metadata.get("date", ""),
                        "source": metadata.get("source", ""),
                        "similarity": distance
                    })
            
            # 2.5 결과 수 제한
            return filtered_results[:n_results]
            
        except Exception as e:
            self.logger.error(f"검색 실패: {str(e)}")
            raise
            
    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """검색 결과 포맷팅
        
        Args:
            results: ChromaDB 검색 결과
            
        Returns:
            포맷팅된 결과 리스트
        """
        return [{
            "title": metadata.get("title", ""),
            "content": metadata.get("content", ""),
            "category": metadata.get("category", ""),
            "date": metadata.get("date", ""),
            "source": metadata.get("source", ""),
            "similarity": distance
        } for metadata, distance in zip(results["metadatas"][0], results["distances"][0])]
    
    def delete_collection(self) -> None:
        """컬렉션 삭제"""
        try:
            self.client.delete_collection(self.collection_name)
            self.logger.info(f"컬렉션 '{self.collection_name}' 삭제 완료")
            self.initialize()  # 컬렉션 삭제 후 재초기화
        except Exception as e:
            self.logger.error(f"컬렉션 삭제 실패: {str(e)}")
            raise 