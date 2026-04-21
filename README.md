---

# NIPA-대전 상수도 수요 예측 및 관리 시스템

대전 지역의 상수도 데이터를 실시간으로 수집하고, 딥러닝 모델(LSTM)을 활용하여 미래 수요 예측 및 과다 사용 알림을 제공하는 통합 관리 시스템입니다.

<p align="center">
  <img src="https://github.com/user-attachments/assets/edf26476-09cf-4820-bc35-a5fcf1aa2f4f" width="800" height="400" />
</p>


## 주요 기능

* **실시간 데이터 수집 및 전처리**: 외부 API를 통해 상수도 검침 데이터를 자동으로 가져오며, 시간별/가구별 사용량 데이터로 정규화합니다.
* **단기 수요 예측**: LSTM 기반 모델을 사용하여 향후 1일간의 사용량을 예측하고 결과를 시스템에 등록합니다.
* **장기 수요 예측**: 향후 7일간의 주간 총 사용량을 예측하여 장기적인 용수 수급 계획 수립을 지원합니다.
* **과다 사용 및 요금 예측**: 전월 대비 당월 사용 패턴을 분석하여 예상 누진세 등급과 요금을 계산하고 과다 사용 여부를 판별합니다.
* **모델 자동 재학습 (Retraining)**: 주기적으로 최신 데이터를 반영하여 단기 및 장기 예측 모델의 정확도를 최신 상태로 유지합니다.

## 프로젝트 구조

| 파일명 | 설명 |
| :--- | :--- |
| `main.py` | 전체 시스템의 엔트리 포인트 및 스케줄러 (예측/분석 작업 주기적 실행) |
| `predict_usage_short.py` | 학습된 모델을 로드하여 향후 24시간 수요 예측 수행 |
| `predict_usage_long.py` | 학습된 모델을 로드하여 향후 7일간의 주간 수요 예측 수행 |
| `predict_excessive.py` | 누진 등급(1~3단계) 판별 및 예상 요금 계산 로직 |
| `predict_usage_short_retrain.py` | 단기 예측 모델 재학습 및 성능 업데이트 |
| `predict_usage_long_retrain.py` | 장기 예측 모델 재학습 및 성능 업데이트 |
| `rest_api_short.py` / `long.py` | 예측에 필요한 실시간 데이터를 API로부터 호출 및 전처리 |
| `retrain_api.py` | 재학습용 과거 대량 데이터를 수집하여 CSV로 저장 |

실행 흐름도
시스템은 크게 예측 파이프라인과 재학습 파이프라인으로 나뉩니다.

[예측 파이프라인 (Daily)]

main.py 실행 시 스케줄러 가동

**rest_api_short/long.py**가 외부 API에서 실시간 검침 데이터를 수집

**predict_usage_short/long.py**가 수집된 데이터를 바탕으로 결과 생성

**predict_excessive.py**가 전월 대비 사용 패턴 분석 및 요금 예측 수행

최종 결과를 시스템 로그 및 API를 통해 결과 서버로 전송

[재학습 파이프라인 (Periodic)]

**retrain_api.py**를 통해 대규모 학습용 데이터셋 구성

predict_usage_short/long_retrain.py 실행

TensorFlow를 이용한 모델 최적화 및 .h5 모델 파일 갱신

## 설치 및 요구 사항

1.  **필수 라이브러리 설치**:
    ```bash
    pip install tensorflow pandas numpy scikit-learn requests schedule python-dateutil
    ```

2.  **시스템 환경**:
    - 본 시스템은 NVIDIA GPU 가속을 사용하도록 최적화되어 있습니다.
    - `tensorflow`가 GPU를 인식할 수 있는 CUDA/cuDNN 환경을 권장합니다.

## 실행 방법

시스템의 자동 스케줄러를 시작하려면 다음 명령어를 실행하십시오.

```bash
python main.py
```

## 시스템 설정 가이드

* **인증 토큰**: API 호출 시 `X-Auth-token` 헤더가 사용됩니다. 각 스크립트 내의 토큰 정보가 유효한지 확인하십시오.
* **데이터 필터링**: 검침 데이터 중 결측치(NaN)가 많거나 데이터 개수가 부족한 가구는 예측 신뢰도를 위해 대상에서 자동으로 제외됩니다.
* **로그 확인**: 모든 작업 결과(성공/실패 메시지)는 시스템 로그 API를 통해 전송되어 모니터링됩니다.
