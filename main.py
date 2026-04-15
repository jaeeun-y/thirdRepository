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
    
    @staticmethod
    def normalize_label(label):

        label = str(label).lower()
        if label in ['+', 'cross']: return 'Cross'
        if label in ['x']: return 'X'
        return 'UNKNOWN'
    
class AppController:
    """프로그램 실행 흐름 및 UI를 제어하는 클래스"""
    
    def __init__(self):
        self.perf_data = {}

    while True:
            print("\n--- Mini NPU Simulator ---")
            print("1. 사용자 입력 모드 (3x3)")
            print("2. data.json 분석 모드")
            print("3. 종료")
            choice = input("모드를 선택하세요: ")

            if choice == '1':
                self.run_mode_1()
            elif choice == '2':
                self.run_mode_2()
            elif choice == '3':
                break
            else:
                print("잘못된 입력입니다.")
    
    def run_mode_1(self):
        print("\n[모드 1: 사용자 입력 (3x3)]")
        filter_a = DataManager.input_matrix(3, "필터 A")
        filter_b = DataManager.input_matrix(3, "필터 B")
        pattern = DataManager.input_matrix(3, "패턴")

        score_a = NPUSimulator.calculate_mac(pattern, filter_a)
        score_b = NPUSimulator.calculate_mac(pattern, filter_b)
        result = NPUSimulator.judge(score_a, score_b)

        print(f"\n[결과] 필터 A 점수: {score_a:.2f}, 필터 B 점수: {score_b:.2f}")
        print(f"판정 결과: {result}")

        # 성능 분석 저장 (크기, 시간, 연산횟수)
        n, avg_time, ops = NPUSimulator.measure_performance(pattern, filter_a)
        self.perf_data[n] = (avg_time, ops)
        self.print_performance()

    def run_mode_2(self):
        print("\n[모드 2: data.json 분석]")
        try:
            with open('data.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            print("오류: data.json 파일을 찾을 수 없습니다.")
            return

        filters = data.get('filters', {})
        patterns = data.get('patterns', {})
        
        # 필터 라벨 정규화
        normalized_filters = {}
        for size_key, filter_dict in filters.items():
            normalized_filters[size_key] = {}
            for label, matrix in filter_dict.items():
                norm_label = DataManager.normalize_label(label)
                normalized_filters[size_key][norm_label] = matrix

        total, passed, failed = 0, 0, 0
        fail_reasons = []

        for p_key, p_data in patterns.items():
            total += 1
            try:
                # size_N_idx 형태에서 N 추출
                n_str = p_key.split('_')[1]
                n = int(n_str)
                size_key = f"size_{n}"
            except (IndexError, ValueError):
                failed += 1
                fail_reasons.append(f"[{p_key}] 키 형식 오류 (크기 추출 실패)")
                continue

            input_pattern = p_data.get('input', [])
            expected_raw = p_data.get('expected', '')
            expected = DataManager.normalize_label(expected_raw)

            if len(input_pattern) != n or any(len(row) != n for row in input_pattern):
                failed += 1
                fail_reasons.append(f"[{p_key}] 패턴 크기 불일치 (기대값: {n}x{n})")
                continue

            if size_key not in normalized_filters:
                failed += 1
                fail_reasons.append(f"[{p_key}] {size_key} 필터가 존재하지 않음")
                continue

            filter_cross = normalized_filters[size_key].get('Cross')
            filter_x = normalized_filters[size_key].get('X')

            if not filter_cross or not filter_x:
                failed += 1
                fail_reasons.append(f"[{p_key}] 해당 크기의 Cross/X 필터 누락")
                continue

            score_cross = NPUSimulator.calculate_mac(input_pattern, filter_cross)
            score_x = NPUSimulator.calculate_mac(input_pattern, filter_x)
            
            result = NPUSimulator.judge(score_cross, score_x, 'Cross', 'X')
            is_pass = (result == expected)
            
            if is_pass:
                passed += 1
                pass_str = "PASS"
            else:
                failed += 1
                pass_str = "FAIL"
                fail_reasons.append(f"[{p_key}] 오답 (기대값: {expected}, 실제: {result})")
            
            print(f"[{p_key}] Cross점수: {score_cross:.2f} | X점수: {score_x:.2f} | 판정: {result} -> {pass_str}")

            # 성능 기록
            _, avg_time, ops = NPUSimulator.measure_performance(input_pattern, filter_cross)
            self.perf_data[n] = (avg_time, ops)

        # 결과 요약 및 성능 분석 출력
        print("\n--- 분석 완료 요약 ---")
        print(f"전체 테스트 수: {total} | 통과: {passed} | 실패: {failed}")
        if failed > 0:
            print("\n[실패 사유 요약]")
            for reason in fail_reasons:
                print(f"- {reason}")

        self.print_performance()
        
    def print_performance(self):
        # [COMMIT: 크기별 평균 연산 시간(ms)과 연산 횟수 표 출력]
        if not self.perf_data:
            return
        print("\n--- 성능 분석 표 ---")
        print(f"{'크기(NxN)':<12} | {'평균 시간(ms)':<15} | {'연산 횟수(N^2)':<15}")
        print("-" * 50)
        for n in sorted(self.perf_data.keys()):
            avg_time, ops = self.perf_data[n]
            print(f"{f'{n}x{n}':<12} | {avg_time:<15.6f} | {ops:<15}")


if __name__ == "__main__":
    app = AppController()
    app.run()