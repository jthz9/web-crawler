# RAG 시스템

한국어 FAQ 데이터를 기반으로 한 Retrieval-Augmented Generation (RAG) 시스템입니다.

## 주요 기능

- 문서 처리 및 임베딩
- 벡터 저장소 관리
- 질의응답 시스템
- 성능 평가 및 모니터링

## 기술 스택

- Python 3.9+
- LangChain
- Sentence Transformers
- ChromaDB
- FastAPI

## 설치 방법

1. 저장소 클론

```bash
git clone https://github.com/yourusername/rag-system.git
cd rag-system
```

2. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows
```

3. 의존성 설치

```bash
pip install -r requirements.txt
```

4. 환경 변수 설정

```bash
cp env.example .env
# .env 파일을 편집하여 필요한 설정 추가
```

## 실행 방법

1. 개발 서버 실행

```bash
uvicorn rag_system.main:app --reload
```

2. Docker로 실행

```bash
docker-compose up --build
```

## API 엔드포인트

- `POST /api/query`: 질문에 대한 답변 생성
- `POST /api/documents`: 새로운 문서 추가
- `GET /api/health`: 서버 상태 확인

## 프로젝트 구조

```
rag_system/
├── preprocessing/      # 데이터 전처리
├── embedding/         # 임베딩 모델
├── vector_store/      # 벡터 저장소
├── evaluation/        # 성능 평가
├── analysis/         # 분석 도구
└── utils/            # 유틸리티 함수
```

## 개발 가이드라인

1. 코드 스타일

   - PEP 8 준수
   - 타입 힌트 사용
   - 문서화 주석 작성

2. 테스트

   - 단위 테스트 작성
   - 통합 테스트 구현
   - 성능 테스트 수행

3. 버전 관리
   - 의미있는 커밋 메시지
   - 브랜치 전략 준수
   - PR 리뷰 프로세스

## 라이선스

MIT License

## 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
