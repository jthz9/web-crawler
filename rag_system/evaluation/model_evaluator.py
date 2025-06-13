import json
import time
import numpy as np
from typing import List, Dict, Any
from tqdm import tqdm
import psutil
import torch
import sys
import os

# 상위 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rag_system.embedding.embedding_model import EmbeddingModel

class ModelEvaluator:
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model = EmbeddingModel(model_name)
        self.memory_usage = 0
        
    def measure_memory_usage(self) -> float:
        """현재 프로세스의 메모리 사용량을 측정합니다."""
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # MB 단위
        
    def evaluate_model(self, 
                      test_data: List[Dict[str, Any]], 
                      k: int = 3) -> Dict[str, float]:
        """모델의 성능을 평가합니다."""
        results = {
            "model_name": self.model_name,
            "overall": {
                "precision": [],
                "recall": [],
                "f1_score": [],
                "mrr": [],
                "ndcg": []
            },
            "original": {
                "precision": [],
                "recall": [],
                "f1_score": [],
                "mrr": [],
                "ndcg": []
            },
            "paraphrase": {
                "precision": [],
                "recall": [],
                "f1_score": [],
                "mrr": [],
                "ndcg": []
            },
            "inference_time": 0,
            "memory_usage": 0
        }
        
        # 메모리 사용량 측정 시작
        initial_memory = self.measure_memory_usage()
        
        # 추론 시간 측정 시작
        start_time = time.time()
        
        # 각 테스트 케이스에 대한 평가
        for case in tqdm(test_data, desc=f"Evaluating {self.model_name}"):
            query = case["query"]
            relevant_docs = case["relevant_docs"]
            query_type = case["query_type"]
            
            # 상위 K개 문서 검색
            top_k_indices, top_k_scores = self.model.get_top_k_documents(
                query, relevant_docs, k=k
            )
            
            # 정확도 계산
            relevant_count = sum(1 for idx in top_k_indices if idx == 0)  # 첫 번째 문서가 항상 관련 문서
            precision = relevant_count / k
            results["overall"]["precision"].append(precision)
            results[query_type]["precision"].append(precision)
            
            # 재현율 계산
            recall = relevant_count / len(relevant_docs)
            results["overall"]["recall"].append(recall)
            results[query_type]["recall"].append(recall)
            
            # F1-score 계산
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            results["overall"]["f1_score"].append(f1)
            results[query_type]["f1_score"].append(f1)
            
            # MRR 계산
            if 0 in top_k_indices:
                rank = top_k_indices.index(0) + 1
                mrr = 1.0 / rank
            else:
                mrr = 0.0
            results["overall"]["mrr"].append(mrr)
            results[query_type]["mrr"].append(mrr)
            
            # NDCG 계산
            dcg = 0.0
            idcg = sum(1.0 / np.log2(i + 2) for i in range(min(k, len(relevant_docs))))
            for i, idx in enumerate(top_k_indices):
                if idx == 0:  # 관련 문서인 경우
                    dcg += 1.0 / np.log2(i + 2)
            ndcg = dcg / idcg if idcg > 0 else 0.0
            results["overall"]["ndcg"].append(ndcg)
            results[query_type]["ndcg"].append(ndcg)
        
        # 전체 추론 시간 계산
        results["inference_time"] = time.time() - start_time
        
        # 메모리 사용량 계산
        final_memory = self.measure_memory_usage()
        results["memory_usage"] = final_memory - initial_memory
        
        # 평균 지표 계산
        for category in ["overall", "original", "paraphrase"]:
            for metric in ["precision", "recall", "f1_score", "mrr", "ndcg"]:
                results[category][f"avg_{metric}"] = np.mean(results[category][metric])
        
        return results

def main():
    # 평가할 모델 목록
    models = [
        "jhgan/ko-sroberta-multitask",
        "snunlp/KR-SBERT-V40K-klueNLI-augSTS",
        "klue/bert-base"
    ]
    
    # 테스트 데이터 로드
    with open("rag_system/evaluation/test_data.json", "r") as f:
        test_data = json.load(f)
    
    # 각 모델 평가
    results = []
    for model_name in models:
        print(f"\n평가 중: {model_name}")
        evaluator = ModelEvaluator(model_name)
        model_results = evaluator.evaluate_model(test_data)
        results.append(model_results)
        
        print("\n전체 성능:")
        print(f"평균 정확도: {model_results['overall']['avg_precision']:.4f}")
        print(f"평균 재현율: {model_results['overall']['avg_recall']:.4f}")
        print(f"평균 F1-score: {model_results['overall']['avg_f1_score']:.4f}")
        print(f"평균 MRR: {model_results['overall']['avg_mrr']:.4f}")
        print(f"평균 NDCG: {model_results['overall']['avg_ndcg']:.4f}")
        
        print("\n원본 쿼리 성능:")
        print(f"평균 정확도: {model_results['original']['avg_precision']:.4f}")
        print(f"평균 재현율: {model_results['original']['avg_recall']:.4f}")
        print(f"평균 F1-score: {model_results['original']['avg_f1_score']:.4f}")
        print(f"평균 MRR: {model_results['original']['avg_mrr']:.4f}")
        print(f"평균 NDCG: {model_results['original']['avg_ndcg']:.4f}")
        
        print("\nParaphrase 쿼리 성능:")
        print(f"평균 정확도: {model_results['paraphrase']['avg_precision']:.4f}")
        print(f"평균 재현율: {model_results['paraphrase']['avg_recall']:.4f}")
        print(f"평균 F1-score: {model_results['paraphrase']['avg_f1_score']:.4f}")
        print(f"평균 MRR: {model_results['paraphrase']['avg_mrr']:.4f}")
        print(f"평균 NDCG: {model_results['paraphrase']['avg_ndcg']:.4f}")
        
        print(f"\n추론 시간: {model_results['inference_time']:.2f}초")
        print(f"메모리 사용량: {model_results['memory_usage']:.2f}MB")
    
    # 결과 저장
    with open("rag_system/evaluation/model_evaluation_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main() 