# 🌱 KNREC 크롤러

## 📁 프로젝트 구조

```
scrapy-selenium/
├── crawler/
│   ├── analysis/
│   │   └── knrec_faq_analyzer.py      # 웹사이트 구조 분석
│   ├── crawler/
│   │   ├── spiders/
│   │   │   ├── base.py                # 기본 스파이더
│   │   │   └── knrec_faq.py           # FAQ 크롤러
│   │   ├── middlewares.py             # Selenium 미들웨어
│   │   ├── pipelines.py               # 데이터 처리
│   │   ├── items.py                   # 데이터 구조
│   │   └── settings.py                # 설정
│   └── output/
│       ├── analysis/                  # 분석 결과
│       ├── data/                      # 크롤링 데이터
│       └── logs/                      # 로그 파일
├── .gitignore
├── README.md
└── requirements.txt
```

## 🚀 워크플로우

### 1. 설치

```bash
git clone https://github.com/jthz9/web-crawler.git
cd web-crawler
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 웹사이트 분석

```bash
cd crawler
python analysis/knrec_faq_analyzer.py
```

### 3. 데이터 크롤링

```bash
# 테스트 (15페이지)
scrapy crawl knrec_faq -a mode=test

# 전체 (35페이지)
scrapy crawl knrec_faq -a mode=real
```

## 📊 결과

- **출력**: `crawler/output/data/knrec_faq_YYYYMMDD_HHMMSS.json`
- **포맷**: JSON (제목, 내용, URL, 페이지번호 등)
