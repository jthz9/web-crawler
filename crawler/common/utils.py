"""
공통 유틸리티 함수
경로 관리 및 기타 도우미 함수를 제공합니다.
"""

import os
import sys
from datetime import datetime
import json
import glob
import logging

def get_project_root():
    """프로젝트 루트 디렉토리 경로 반환"""
    # 현재 파일의 위치에서 상위 디렉토리로 이동하여 프로젝트 루트 찾기
    current_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return current_path

def get_analysis_results_dir():
    """분석 결과 디렉토리 경로 반환"""
    return os.path.join(get_project_root(), 'crawler', 'analysis', 'results')

def get_crawler_results_dir(mode='full'):
    """크롤링 결과 디렉토리 경로 반환"""
    return os.path.join(get_project_root(), 'crawler', 'results', mode)

def get_logs_dir():
    """로그 디렉토리 경로 반환"""
    return os.path.join(get_project_root(), 'crawler', 'logs')

def get_data_dir():
    """데이터 디렉토리 경로 반환"""
    return os.path.join(get_project_root(), 'crawler', 'data')

def get_latest_analysis_result(target):
    """가장 최근의 분석 결과 파일 찾기"""
    analysis_dir = get_analysis_results_dir()
    
    # 타겟별 디렉토리 구분
    if 'knrec' in target:
        analysis_dir = os.path.join(analysis_dir, 'knrec')
    
    # 분석 결과 파일 패턴
    pattern = os.path.join(analysis_dir, f"{target}_analysis_*.json")
    files = glob.glob(pattern)
    
    if not files:
        print(f"경고: {target}에 대한 분석 결과 파일을 찾을 수 없습니다. 경로: {pattern}")
        return None
    
    # 가장 최근 파일 반환
    latest_file = max(files, key=os.path.getctime)
    print(f"최신 분석 결과 파일: {latest_file}")
    return latest_file

def load_analysis_result(target):
    """분석 결과 로드"""
    result_file = get_latest_analysis_result(target)
    
    if not result_file:
        print(f"분석 결과 파일이 없습니다: {target}")
        return None
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"분석 결과 로드 성공: {result_file}")
            
            # 분석 결과 요약 출력
            if 'url' in data:
                print(f"- 분석 URL: {data['url']}")
            if 'table_count' in data:
                print(f"- 테이블 수: {data['table_count']}")
            if 'pagination' in data and 'found' in data['pagination']:
                print(f"- 페이지네이션: {'발견됨' if data['pagination']['found'] else '발견되지 않음'}")
            
            return data
    except Exception as e:
        print(f"분석 결과 로드 오류: {e}")
        return None

def generate_timestamp():
    """현재 시간 기반 타임스탬프 생성"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')

def ensure_directory_exists(directory):
    """디렉토리가 존재하는지 확인하고, 없으면 생성"""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory 