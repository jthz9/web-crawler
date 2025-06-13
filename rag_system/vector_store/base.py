from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseVectorStore(ABC):
    """벡터 저장소의 기본 인터페이스"""
    
    @abstractmethod
    def initialize(self) -> None:
        """벡터 저장소 초기화"""
        pass
    
    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """문서 추가
        
        Args:
            documents: 추가할 문서 리스트. 각 문서는 title, content, metadata를 포함
        """
        pass
    
    @abstractmethod
    def search(self, 
              query: str, 
              top_k: int = 5, 
              filter_criteria: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """문서 검색
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수
            filter_criteria: 메타데이터 필터링 조건
            
        Returns:
            검색 결과 리스트. 각 결과는 title, content, score를 포함
        """
        pass
    
    @abstractmethod
    def delete_collection(self) -> None:
        """컬렉션 삭제"""
        pass 