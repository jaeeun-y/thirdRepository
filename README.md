# ThirdRepository

## 🚀jaeeunsRepository

### 📝프로젝트 개요  
NPU(Neural Processing Unit)의 핵심인 MAC(Multiply-Accumulate) 연산을 구현하고, 입력된 패턴이 어떤 필터에 더 가까운지 판별하는 시뮬레이터 입니다.


### 📝실행 방법
- python main.py
  

### 📝구현 요약

- 라벨 정규화 방식
  
  : 사용자가 입력하거나, JSON 에 작성된 기대값 라벨은 형태가 다양함. (+, Cross, X, x, 십자 등)   
  : DataManager.LABEL_MAP 딕셔너리를 활용해 비교의 정확성을 높임.  
  1. 입력된 문자열을 소문자로 변환
  2. 공백을 제거
  3. 내부 표준 라벨인 Cross, X로 정규화

- MAC 연산 구현
  
  :NPUSimulator.calculate_mac()  
  :입력 패턴(pattern)과 필터 행렬(filter_matrix)의 동일한 인덱스(i,j) 위치에 있는 값을 곱하고 전체 값을 더함.

- 동점 처리 정책
  
  :부동소수점 연산 과정에서의 오차 방지 => EPSILON = 1e-9 상수 도입  
  :두 필터의 점수 차이가 if abs(score_a - b) < EPSILON return UNDECIDED(판정 불가)

  
### 📝결과 리포트

#### FAIL 원인 분석  
  1. 의도적인 스키마/크기 불일치  
     :4x5 패턴 데이터 삽입으로 오류 처리 능력 검증 (size_5_02_error_test)  
      연산 수행 전 len(pattern) != n 조건으로 감지  
      IndexError로 종료되는 대신 해당 케이스를 안전하게 FAIL 처리 후 "패턴 크기 불일치" 명시  

     <img width="988" height="322" alt="image" src="https://github.com/user-attachments/assets/af958970-a503-4adf-98d8-d564eae08c31" />


  2. 라벨 및 오답 발생 (data.json 분석모드 한정)  
     : MAC 연산은 정상 수행  
      도출된 판정 결과가 JSON 파일의 expected 라벨과 일치하지 않는 경우  

```
#기대값을 틀리게 적기

[모드 2: data.json 분석]
[size_5_02] Cross점수: 8.00 | X점수: 1.00 | 판정: Cross -> FAIL

[실패 사유 요약]
  - [size_5_02] 오답 (기대값: X, 실제: Cross)

#완전 애매한 패턴 만들기

[모드 2: data.json 분석]
[size_5_03] Cross점수: 5.00 | X점수: 5.00 | 판정: UNDECIDED -> FAIL
[size_5_04] Cross점수: 9.00 | X점수: 9.00 | 판정: UNDECIDED -> FAIL

[실패 사유 요약]
 - [size_5_03] 오답 (기대값: X, 실제: UNDECIDED)
 - [size_5_04] 오답 (기대값: X, 실제: UNDECIDED)
```


#### 성능 표 해석 및 시간복잡도 분석

패턴의 데이터 크기가 증가함에 따라 연산 시간이 기하급수적으로 증가  
     
<img width="992" height="204" alt="image" src="https://github.com/user-attachments/assets/45ab8d9d-6cf2-4c25-969f-183079dc1472" />  

##### 연산 횟수와 측정 결과의 연결:

```
5x5: 총 연산 횟수 5^2 = 25회 $\rightarrow$ 측정 시간 약 0.00 ms  
13x13: 총 연산 횟수 13^2 = 169회 $\rightarrow$ 측정 시간 약 0.01 ms  
25x25: 총 연산 횟수 25^2 = 625회 $\rightarrow$ 5x5 측정 시간 약 0.05 ms 
```


##### 시간복잡도 $O(N^2)$
```
∵      def calculate_mac(self, pattern: Matrix) -> float:

        n = self.filter_size
        if len(pattern) != n or any(len(row) != n for row in pattern):
            raise ValueError(
                f"패턴 크기가 필터({n}x{n})와 일치하지 않습니다."
            )

        return sum(
            pattern[i][j] * self.filter_matrix[i][j]
            for i in range(n)
            for j in range(n)
```

### 📝

┌───────────────────────────────────────┐  
  -  AppController              
  (프로그램 흐름 제어 + UI)                   
                                    								
│     run() ─→  run_mode_1() →	수동모드    	

│           ─→  run_mode_2() →	JSON자동 테스트 모드

│              ├── _load_json() →	data.json 로드	 & 세분화된 예외처리  

│              ├── _normalize_filters() →	필터 딕셔너리의 라벨을 정규화  

│              ├── _test_single_pattern() →  			

│              └── _print_summary() →	테스트 결과 요약 출력    

│    ─→  _record_performance() →	성능 데이터 누적 (리스트로 누적)  

│    ─→  print_performance() →	누적된 성능 데이터를 표로 출력 

├───────────────────────────────────────┤  
- NPUSimulator                      
  (핵심 연산 엔진)       
  
│                                                
│  __init__(filter)  	   → 필터 저장                   
│  calculate_mac()   	   → MAC 연산                  
│  judge()           	   → 점수 비교 판정             
│  measure_performance()   → 성능 측정  

├───────────────────────────────────────┤  

 - DataManager                        
  (입출력 + 데이터 전처리)
                     
│                                               
│  input_matrix()     		→ 행렬 입력                
│  normalize_label()  		→ 라벨 정규화      

└───────────────────────────────────────┘  




