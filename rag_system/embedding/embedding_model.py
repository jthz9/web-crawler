import time
import numpy as np
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class EmbeddingModel:
    def __init__(self, model_name: str):
        """임베딩 모델을 초기화합니다.
        
        Args:
            model_name (str): 사용할 모델의 이름
        """
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        
    def create_embeddings(self, texts: List[str]) -> Tuple[np.ndarray, float]:
        """텍스트 리스트에 대한 임베딩을 생성합니다.
        
        Args:
            texts (List[str]): 임베딩을 생성할 텍스트 리스트
            
        Returns:
            Tuple[np.ndarray, float]: (임베딩 배열, 추론 시간)
        """
        start_time = time.time()
        embeddings = self.model.encode(texts)
        end_time = time.time()
        
        return embeddings, end_time - start_time
        
    def calculate_similarity(self, query_embedding: np.ndarray, 
                           doc_embeddings: np.ndarray) -> np.ndarray:
        """쿼리와 문서 간의 코사인 유사도를 계산합니다.
        
        Args:
            query_embedding (np.ndarray): 쿼리의 임베딩
            doc_embeddings (np.ndarray): 문서들의 임베딩
            
        Returns:
            np.ndarray: 유사도 점수 배열
        """
        return cosine_similarity([query_embedding], doc_embeddings)[0]
        
    def get_top_k_documents(self, query: str, documents: List[str], 
                          k: int = 3) -> Tuple[List[int], List[float]]:
        """쿼리에 대해 가장 관련성 높은 상위 K개의 문서를 반환합니다.
        
        Args:
            query (str): 검색 쿼리
            documents (List[str]): 검색 대상 문서 리스트
            k (int, optional): 반환할 문서 수. 기본값은 3.
            
        Returns:
            Tuple[List[int], List[float]]: (문서 인덱스 리스트, 유사도 점수 리스트)
        """
        # 임베딩 생성
        query_embedding, _ = self.create_embeddings([query])
        doc_embeddings, _ = self.create_embeddings(documents)
        
        # 유사도 계산
        similarities = self.calculate_similarity(query_embedding[0], doc_embeddings)
        
        # 상위 K개 결과 추출
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        top_k_scores = similarities[top_k_indices]
        
        return top_k_indices.tolist(), top_k_scores.tolist() 