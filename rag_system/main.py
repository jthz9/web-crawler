import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# 환경 변수 로드
load_dotenv()

class RAGSystem:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # 임베딩 모델 초기화 (한국어에 최적화된 모델 사용)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sroberta-multitask",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        
        # 벡터 저장소 초기화
        self.vector_store = None
        
        # LLM 초기화
        self.llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0
        )
        
    def load_documents(self, documents: List[str]) -> None:
        """문서를 로드하고 청크로 분할합니다."""
        chunks = self.text_splitter.create_documents(documents)
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory="./vector_store"
        )
        
    def query(self, question: str) -> Dict[str, Any]:
        """질문에 대한 답변을 생성합니다."""
        if not self.vector_store:
            raise ValueError("문서가 로드되지 않았습니다. 먼저 load_documents()를 호출하세요.")
            
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(
                search_kwargs={"k": 3}
            )
        )
        
        return qa_chain.invoke({"query": question})

def main():
    # RAG 시스템 인스턴스 생성
    rag = RAGSystem()
    
    # 예시 문서 로드
    documents = [
        "여기에 문서 내용이 들어갑니다.",
        "추가 문서 내용..."
    ]
    
    rag.load_documents(documents)
    
    # 예시 질문
    question = "질문을 입력하세요"
    result = rag.query(question)
    print(f"질문: {question}")
    print(f"답변: {result['result']}")

if __name__ == "__main__":
    main() 