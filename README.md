# Scrapy-Selenium KNREC FAQ 크롤러

한국에너지공단 신재생에너지센터(KNREC) 웹사이트 크롤링을 위한 Scrapy-Selenium 기반 프로젝트

## 아키텍처

### 전체 구조

```
Analysis Phase → Central Service → Crawling Execution → Data Pipeline
```

### 컴포넌트

```
scrapy-selenium/
├── crawler/
│   ├── analysis/
│   │   └── knrec_faq_analyzer.py      # 웹사이트 구조 분석
│   ├── common/
│   │   └── analysis_service.py        # 분석 결과 중앙 관리
│   ├── crawler/
│   │   ├── spiders/
│   │   │   ├── base.py                # 베이스 스파이더 (공통 기능)
│   │   │   └── knrec_faq.py           # KNREC 전용 스파이더
│   │   ├── items.py                   # 데이터 구조
│   │   ├── pipelines.py               # 데이터 처리 파이프라인
│   │   └── settings.py                # Scrapy 설정
│   └── output/
│       ├── analysis/knrec/            # 분석 결과
│       └── data/                      # 크롤링 데이터
```

## 파이프라인

### 1. 분석 단계 (Analysis Phase)

```python
KnrecFaqAnalyzer
├── 웹사이트 구조 분석
├── CSS 선택자 테스트
├── 페이지네이션 분석
└── 분석 결과 JSON 저장
```

### 2. 중앙 서비스 (Central Service)

```python
AnalysisService
├── 분석 결과 캐싱
├── 웹사이트별 설정 관리
└── 스파이더간 설정 공유
```

### 3. 크롤링 실행 (Crawling Execution)

```python
KnrecFaqSpider (BaseFAQSpider 상속)
├── 분석 결과 로드
├── Selenium 웹드라이버 초기화
├── 페이지별 FAQ 목록 수집
├── 상세 페이지 방문 및 내용 추출
├── 중복 제거 (URL 기반)
└── Scrapy Item 생성
```

### 4. 데이터 파이프라인 (Data Pipeline)

```python
RenewableEnergyPipeline
├── Item 검증
├── 데이터 정제
├── 타임스탬프 파일명 생성
└── JSON 파일 저장
```

## 핵심 설계 원리

### 1. 모듈 분리

- **분석**: 웹사이트 구조 파악
- **크롤링**: 실제 데이터 수집
- **처리**: 데이터 정제 및 저장

### 2. Scrapy & Selenium

**Scrapy**: 웹 크롤링 및 웹 스크래핑 전용 Python 프레임워크

- 고성능 HTTP 요청 처리
- Item-Pipeline 기반 데이터 처리 구조
- 내장 중복 제거, 요청 큐, 에러 핸들링
- 비동기 처리로 빠른 크롤링 속도

**Item-Pipeline**

- **Item**: 크롤링 데이터를 담는 구조화된 컨테이너 (필드 정의)
- **Pipeline**: Item이 순차적으로 거치는 처리 단계들 (검증→정제→저장)
- **흐름**: Spider → Item 생성 → Pipeline 1,2,3... → 최종 저장
- **장점**: 모듈화된 데이터 처리, 재사용성, 확장성

**Selenium**: 웹 브라우저 자동화 도구

- 실제 브라우저 제어 (Chrome, Firefox 등)
- JavaScript 실행 및 동적 컨텐츠 렌더링
- 사용자 상호작용 시뮬레이션 (클릭, 입력 등)
- SPA(Single Page Application) 지원

**Scrapy-Selenium 조합**:

- Scrapy 미들웨어를 통해 Selenium WebDriver 연결
- SeleniumRequest 페이지 로드
- 베이스 스파이더에서 Selenium 세션 관리 (초기화/정리)
- Pipeline 유지: Scrapy의 데이터 처리 구조는 그대로 활용
- JavaScript가 필요한 동적 웹사이트를 Scrapy 구조로 처리 가능

### 3. 중앙 분석 시스템

**목적**: 웹사이트 분석과 크롤링을 분리하여 효율성 증대

**구조**:

- 사전 분석 단계에서 CSS 선택자, 페이지 구조 등을 파악
- 분석 결과를 JSON으로 저장하여 재사용
- 스파이더 실행 시 분석 결과를 로드하여 설정값으로 활용
- 여러 웹사이트로 확장 시 각 사이트별 분석 결과를 중앙에서 관리

**장점**: 분석은 한 번만, 크롤링은 분석 결과 기반으로 반복 실행 가능

## 실행 방법

### 분석 (선택사항)

```bash
cd crawler
python analysis/knrec_faq_analyzer.py
```

### 크롤링

```bash
cd crawler
scrapy crawl knrec_faq
```

## 데이터 흐름

```
Start URLs → Selenium 로드 → 페이지별 FAQ 목록 추출 → 상세 페이지 방문 →
내용 추출 → Item 생성 → Pipeline 처리 → JSON 저장
```

## 확장 방법

새 웹사이트 크롤링 추가:

1. `analysis/new_site_analyzer.py` 작성
2. `spiders/new_site.py` 작성 (BaseFAQSpider 상속)
3. 사이트별 특화 로직 구현
