import os
from urllib.parse import quote

# DaedalusMark GX 검수 API 설정.
# 운영값은 상수로 두되 env 로 override 가능하게 함.
VALIDATE_API_BASE = os.getenv("VALIDATE_API_BASE", "http://10.81.100.75:8111")
VALIDATE_BUCKET = os.getenv("VALIDATE_BUCKET", "devops")
VALIDATE_TIMEOUT = int(os.getenv("VALIDATE_TIMEOUT", "300"))


def request_validate_data(object_name: str) -> None:
    """
    MinIO 에 업로드된 산출물에 대해 DaedalusMark GX 검수를 트리거한다.

    kafka_kibisis `app/core/utils/validate_util.py` 와 동일한 패턴:
        POST http://<host>:8111/validate/run?file_path=s3://<bucket>/<object>

    안전 규칙:
    - CSV 산출물만 검수 대상. `_success` 마커 등 비 CSV 는 건너뛴다.
    - requests 미설치/네트워크 오류 등 어떤 예외도 삼켜서
      업로드 파이프라인에 절대 영향을 주지 않는다.

    Args:
        object_name: MinIO 버킷 내 object key
                     (예: scrap_data/2026/09/business_no/business_no_20260907.csv)
    """
    try:
        # _success 마커 등 CSV 가 아닌 산출물은 검수 제외
        if not object_name.lower().endswith(".csv"):
            print(f"[SKIP] GX 검수 제외 대상(비 CSV): {object_name}")
            return

        s3_path = f"s3://{VALIDATE_BUCKET}/{object_name}"
        encoded_path = quote(s3_path, safe="")  # safe='' -> 전부 인코딩
        api_url = f"{VALIDATE_API_BASE}/validate/run?file_path={encoded_path}"

        # 지연 임포트: requests 가 없더라도 import 단계에서 파이프라인이 죽지 않게 함
        import requests

        response = requests.post(
            api_url, headers={"Content-Type": "application/json"}, timeout=VALIDATE_TIMEOUT
        )
        response.raise_for_status()
        result = response.json()
        print("[OK] GX 검수 요청 성공:", result)
    except Exception as e:
        # 검수 트리거 실패는 업로드 성공 여부와 무관하게 무시
        print("[FAIL] GX 검수 요청 실패(무시하고 계속 진행):", e)
