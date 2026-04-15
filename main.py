import json
import time

EPSILON = 1e-9
ITERATIONS = 10

class NPUSimulator:
    """NPU 연산 및 성능 측정을 담당하는 클래스"""
    
    @staticmethod
    def calculate_mac(pattern, filter_matrix):
        # [COMMIT: MAC 연산 (외부 라이브러리 금지, 반복문 구현)]
        n = len(pattern)
        mac_score = 0.0
        for i in range(n):
            for j in range(n):
                mac_score += pattern[i][j] * filter_matrix[i][j]
        return mac_score