import os
from typing import List, Dict, Any
import torch
from sentence_transformers import SentenceTransformer
from ..utils.logger import get_logger

logger = get_logger(__name__)

class KoreanEmbeddingModel:
    """한국어 임베딩 모델 클래스"""
    
    def __init__(self, model_name: str = "jhgan/ko-sroberta-multitask"):
        """초기화
        
        Args:
            model_name: 사용할 모델 이름
        """
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.initialize()
        
    def initialize(self) -> None:
        """모델 초기화"""
        try:
            logger.info(f"임베딩 모델 로딩 중: {self.model_name}")
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("임베딩 모델 로딩 완료")
        except Exception as e:
            logger.error(f"임베딩 모델 로딩 실패: {str(e)}")
            raise
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """텍스트 임베딩 생성
        
        Args:
            texts: 임베딩을 생성할 텍스트 리스트
            
        Returns:
            임베딩 벡터 리스트
        """
        if not self.model:
            self.initialize()
            
        try:
            embeddings = self.model.encode(
                texts,
                convert_to_tensor=True,
                show_progress_bar=True
            )
            return embeddings.cpu().numpy().tolist()
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """단일 텍스트 임베딩 생성
        
        Args:
            text: 임베딩을 생성할 텍스트
            
        Returns:
            임베딩 벡터
        """
        return self.get_embeddings([text])[0] 