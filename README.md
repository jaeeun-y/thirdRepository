┌───────────────────────────────────────┐  
│              AppController              
│  (프로그램 흐름 제어 + UI)                   
│                                                								
│ run() ─→  run_mode_1() →	수동모드  		
│       ─→  run_mode_2() →	JSON자동 테스트 모드  		
│              ├── _load_json() →	data.json 로드	 & 세분화된 예외처리	  
│              ├── _normalize_filters() →	필터 딕셔너리의 라벨을 정규화  		
│              ├── _test_single_pattern() →			  
│              └── _print_summary() →	테스트 결과 요약 출력  		
│    ─→  _record_performance() →	성능 데이터 누적 (리스트로 누적)	  						
│    ─→  print_performance() →	누적된 성능 데이터를 표로 출력	  	     
├───────────────────────────────────────┤  
│              NPUSimulator                      
│  (핵심 연산 엔진)                                 
│                                                
│  __init__(filter)  	   → 필터 저장                   
│  calculate_mac()   	   → MAC 연산                  
│  judge()           	   → 점수 비교 판정             
│  measure_performance()   → 성능 측정              
├───────────────────────────────────────┤  
│             DataManager                        
│  (입출력 + 데이터 전처리)                       
│                                               
│  input_matrix()     		→ 행렬 입력                
│  normalize_label()  		→ 라벨 정규화              
└───────────────────────────────────────┘  




```
import json
import time
from typing import Dict, List, Tuple, Optional

EPSILON = 1e-9
ITERATIONS = 10

Matrix = List[List[float]]  # 타입 별칭

class NPUSimulator:
    """NPU 연산 및 성능 측정을 담당하는 클래스"""

    def __init__(self, filter_matrix: Matrix):
        self.filter_matrix = filter_matrix
        self.filter_size = len(filter_matrix)
    

    def calculate_mac(self, pattern: Matrix) -> float:
        """
        개선점:
        1. 크기 불일치 검증 추가
        2. 인스턴스 변수로 필터 접근 → 매번 전달 불필요
        """
        n = self.filter_size
        if len(pattern) != n or any(len(row) != n for row in pattern):
            raise ValueError(
                f"패턴 크기가 필터({n}x{n})와 일치하지 않습니다."
            )

        # ── 리스트 컴프리헨션으로 성능 + 가독성 개선 ──
        return sum(
            pattern[i][j] * self.filter_matrix[i][j]
            for i in range(n)
            for j in range(n)
        )

    @staticmethod
    def judge(
        score_a: float,
        score_b: float,
        label_a: str = 'A',
        label_b: str = 'B',
        epsilon: float = EPSILON
    ) -> str:
        """개선: epsilon을 파라미터로 받아 유연성 확보"""
        if abs(score_a - score_b) < epsilon:
            return 'UNDECIDED'
        return label_a if score_a > score_b else label_b

    def measure_performance(
        self, pattern: Matrix, iterations: int = ITERATIONS
    ) -> dict:
        """
        개선점:
        1. 반환값을 dict로 → 의미 명확
        2. iterations 파라미터화
        3. 0 나누기 방지
        """
        if iterations <= 0:
            raise ValueError("iterations는 1 이상이어야 합니다.")

        start_time = time.perf_counter()
        for _ in range(iterations):
            self.calculate_mac(pattern)
        end_time = time.perf_counter()

        n = self.filter_size
        avg_time_ms = ((end_time - start_time) / iterations) * 1000

        return {
            'matrix_size': n,
            'avg_time_ms': round(avg_time_ms, 6),
            'total_ops': n * n,
            'iterations': iterations
        }


class DataManager:
    """데이터 입출력 및 전처리 담당"""

    # ── 라벨 매핑 테이블 (확장 용이) ──
    LABEL_MAP = {
        '+': 'Cross', 'cross': 'Cross', '십자': 'Cross',
        'x': 'X', '엑스': 'X',
        'o': 'O', '동그라미': 'O',
    }

    @staticmethod
    def input_matrix(size: int, name: str) -> Matrix:
        """
        개선점:
        1. 오류 시 해당 줄만 재입력 (전체 초기화 X)
        2. 빈 입력 처리
        """
        print(f"\n{name} ({size}x{size})를 한 줄씩 공백으로 구분하여 입력하세요:")
        matrix = []
        while len(matrix) < size:
            row_num = len(matrix) + 1
            try:
                raw = input(f"  Row {row_num}: ").strip()
                if not raw:
                    raise ValueError("빈 입력")
                row = list(map(float, raw.split()))
                if len(row) != size:
                    raise ValueError(f"숫자 {len(row)}개 입력됨")
                matrix.append(row)
            except ValueError as e:
                # ── 해당 줄만 재입력 (matrix 초기화 안 함) ──
                print(f"  ⚠ 오류({e}): {size}개의 숫자를 공백으로 구분해 입력하세요.")
        return matrix

    @classmethod
    def normalize_label(cls, label: str) -> str:
        """개선: 딕셔너리 기반 매핑 → 확장 용이"""
        return cls.LABEL_MAP.get(str(label).lower().strip(), 'UNKNOWN')
    
class AppController:
    """프로그램 실행 흐름 및 UI를 제어하는 클래스"""

    def __init__(self):
        # ── 성능 데이터: 리스트로 변경하여 누적 가능 ──
        self.perf_data: Dict[int, List[Tuple[float, int]]] = {}

    # ═══════════════════════════════════════════
    # 메인 루프
    # ═══════════════════════════════════════════
    def run(self):
        while True:
            print("\n--- Mini NPU Simulator ---")
            print("1. 사용자 입력 모드 (3x3)")
            print("2. data.json 분석 모드")
            print("3. 종료")
            choice = input("모드를 선택하세요: ").strip()

            if choice == '1':
                self.run_mode_1()
            elif choice == '2':
                self.run_mode_2()
            elif choice == '3':
                print("프로그램을 종료합니다.")
                break
            else:
                print("⚠ 1, 2, 3 중에서 선택하세요.")

    # ═══════════════════════════════════════════
    # 모드 1: 수동 입력
    # ═══════════════════════════════════════════
    def run_mode_1(self):
        print("\n[모드 1: 사용자 입력 (3x3)]")
        filter_a = DataManager.input_matrix(3, "필터 A")
        filter_b = DataManager.input_matrix(3, "필터 B")
        pattern = DataManager.input_matrix(3, "패턴")

        # ── 인스턴스 기반 NPUSimulator 사용 ──
        npu_a = NPUSimulator(filter_a)
        npu_b = NPUSimulator(filter_b)

        score_a = npu_a.calculate_mac(pattern)
        score_b = npu_b.calculate_mac(pattern)
        result = NPUSimulator.judge(score_a, score_b)

        print(f"\n[결과] 필터 A 점수: {score_a:.2f}, 필터 B 점수: {score_b:.2f}")
        print(f"판정 결과: {result}")

        perf = npu_a.measure_performance(pattern)
        self._record_performance(perf['matrix_size'], perf['avg_time_ms'], perf['total_ops'])
        self.print_performance()

    # ═══════════════════════════════════════════
    # 모드 2: JSON 분석 (책임 분리)
    # ═══════════════════════════════════════════
    def run_mode_2(self):
        print("\n[모드 2: data.json 분석]")

        # ── Step 1: 파일 로드 ──
        data = self._load_json('data.json')
        if data is None:
            return

        # ── Step 2: 필터 정규화 ──
        filters = data.get('filters', {})
        patterns = data.get('patterns', {})
        normalized_filters = self._normalize_filters(filters)

        # ── Step 3: 패턴별 테스트 실행 ──
        total, passed, failed = 0, 0, 0
        fail_reasons = []

        for p_key, p_data in patterns.items():
            total += 1
            result = self._test_single_pattern(
                p_key, p_data, normalized_filters
            )

            if result['status'] == 'ERROR':
                failed += 1
                fail_reasons.append(result['reason'])
                continue

            if result['is_pass']:
                passed += 1
                tag = "PASS"
            else:
                failed += 1
                tag = "FAIL"
                fail_reasons.append(result['reason'])

            print(
                f"[{p_key}] Cross점수: {result['score_cross']:.2f} | "
                f"X점수: {result['score_x']:.2f} | "
                f"판정: {result['判定']} -> {tag}"
            )

        # ── Step 4: 결과 요약 ──
        self._print_summary(total, passed, failed, fail_reasons)
        self.print_performance()

    # ═══════════════════════════════════════════
    # 분리된 헬퍼 메서드들
    # ═══════════════════════════════════════════
    def _load_json(self, filepath: str) -> Optional[dict]:
        """JSON 파일 로드 + 세분화된 예외 처리"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠ 오류: {filepath} 파일을 찾을 수 없습니다.")
        except json.JSONDecodeError as e:
            print(f"⚠ JSON 파싱 오류: {e}")
        except PermissionError:
            print(f"⚠ 권한 오류: {filepath}을 읽을 수 없습니다.")
        return None

    @staticmethod
    def _normalize_filters(filters: dict) -> dict:
        """필터 딕셔너리의 라벨을 정규화"""
        normalized = {}
        for size_key, filter_dict in filters.items():
            normalized[size_key] = {}
            for label, matrix in filter_dict.items():
                norm_label = DataManager.normalize_label(label)
                normalized[size_key][norm_label] = matrix
        return normalized

    def _test_single_pattern(
        self, p_key: str, p_data: dict, norm_filters: dict
    ) -> dict:
        """
        단일 패턴 테스트 (run_mode_2에서 분리)
        
        반환: {
            'status': 'OK' | 'ERROR',
            'is_pass': bool,
            'score_cross': float,
            'score_x': float,
            '判定': str,
            'reason': str  (실패 시)
        }
        """
        # ── 키에서 크기 추출 ──
        try:
            n_str = p_key.split('_')[1]
            n = int(n_str)
            size_key = f"size_{n}"
        except (IndexError, ValueError):
            return {
                'status': 'ERROR',
                'reason': f"[{p_key}] 키 형식 오류 (크기 추출 실패)"
            }

        # ── 패턴 검증 ──
        input_pattern = p_data.get('input', [])
        expected_raw = p_data.get('expected', '')
        expected = DataManager.normalize_label(expected_raw)

        if len(input_pattern) != n or any(len(row) != n for row in input_pattern):
            return {
                'status': 'ERROR',
                'reason': f"[{p_key}] 패턴 크기 불일치 (기대값: {n}x{n})"
            }

        # ── 필터 존재 확인 ──
        if size_key not in norm_filters:
            return {
                'status': 'ERROR',
                'reason': f"[{p_key}] {size_key} 필터가 존재하지 않음"
            }

        filter_cross = norm_filters[size_key].get('Cross')
        filter_x = norm_filters[size_key].get('X')

        if not filter_cross or not filter_x:
            return {
                'status': 'ERROR',
                'reason': f"[{p_key}] 해당 크기의 Cross/X 필터 누락"
            }

        # ── MAC 연산 + 판정 ──
        npu_cross = NPUSimulator(filter_cross)
        npu_x = NPUSimulator(filter_x)

        score_cross = npu_cross.calculate_mac(input_pattern)
        score_x = npu_x.calculate_mac(input_pattern)
        result = NPUSimulator.judge(score_cross, score_x, 'Cross', 'X')
        is_pass = (result == expected)

        # ── 성능 기록 ──
        perf = npu_cross.measure_performance(input_pattern)
        self._record_performance(n, perf['avg_time_ms'], perf['total_ops'])

        reason = "" if is_pass else f"[{p_key}] 오답 (기대값: {expected}, 실제: {result})"

        return {
            'status': 'OK',
            'is_pass': is_pass,
            'score_cross': score_cross,
            'score_x': score_x,
            '判定': result,
            'reason': reason
        }

    def _record_performance(self, n: int, avg_time: float, ops: int):
        """성능 데이터 누적 (덮어쓰기 X → 리스트로 누적)"""
        if n not in self.perf_data:
            self.perf_data[n] = []
        self.perf_data[n].append((avg_time, ops))

    @staticmethod
    def _print_summary(total: int, passed: int, failed: int, fail_reasons: list):
        """테스트 결과 요약 출력"""
        print("\n--- 분석 완료 요약 ---")
        print(f"전체 테스트 수: {total} | 통과: {passed} | 실패: {failed}")
        if failed > 0:
            print("\n[실패 사유 요약]")
            for reason in fail_reasons:
                print(f"  - {reason}")

    def print_performance(self):
        """누적된 성능 데이터를 평균 내어 표로 출력"""
        if not self.perf_data:
            return

        print("\n--- 성능 분석 표 ---")
        print(f"{'크기(NxN)':<12} | {'평균 시간(ms)':<15} | {'연산 횟수(N²)':<15} | {'측정 횟수':<10}")
        print("-" * 60)

        for n in sorted(self.perf_data.keys()):
            records = self.perf_data[n]
            avg_time = sum(t for t, _ in records) / len(records)
            ops = records[0][1]  # N² 값은 동일
            count = len(records)
            print(f"{f'{n}x{n}':<12} | {avg_time:<15.6f} | {ops:<15} | {count:<10}")


if __name__ == "__main__":
    app = AppController()
    app.run()
```
