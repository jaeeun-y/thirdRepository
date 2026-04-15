import json
import time

EPSILON = 1e-9
ITERATIONS = 10

class NPUSimulator:
    """NPU 연산 및 성능 측정을 담당하는 클래스"""
    
    @staticmethod
    def calculate_mac(pattern, filter_matrix):

        n = len(pattern)
        mac_score = 0.0
        for i in range(n):
            for j in range(n):
                mac_score += pattern[i][j] * filter_matrix[i][j]
        return mac_score
    
    @staticmethod
    def judge(score_a, score_b, label_a='A', label_b='B'):

        if abs(score_a - score_b) < EPSILON:
            return 'UNDECIDED'
        return label_a if score_a > score_b else label_b
    
    @staticmethod
    def measure_performance(pattern, filter_matrix):

        start_time = time.perf_counter()
        for _ in range(ITERATIONS):
            NPUSimulator.calculate_mac(pattern, filter_matrix)
        end_time = time.perf_counter()
        
        avg_time_ms = ((end_time - start_time) / ITERATIONS) * 1000
        n = len(pattern)
        ops = n * n
        return n, avg_time_ms, ops

class DataManager:
    """입력 데이터 검증, 로드, 정규화를 담당하는 클래스"""

    @staticmethod
    def input_matrix(size, name):
  
        print(f"\n{name} ({size}x{size})를 한 줄씩 공백으로 구분하여 입력하세요:")
        matrix = []
        while len(matrix) < size:
            try:
                row = list(map(float, input(f"Row {len(matrix)+1}: ").strip().split()))
                if len(row) != size:
                    raise ValueError
                matrix.append(row)
            except ValueError:
                print(f"입력 형식 오류: 각 줄에 {size}개의 숫자를 공백으로 구분해 입력하세요.")
                matrix = [] # 초기화 후 재입력 유도
        return matrix