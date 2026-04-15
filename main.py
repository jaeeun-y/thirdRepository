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