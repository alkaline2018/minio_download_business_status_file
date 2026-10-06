# minio_download_business_status_file 시스템 지도

## 운영·개발 폴더 (2026-10-06~)
- **운영 폴더** `C:\Users\user\PycharmProjects\minio_download_business_status_file`: 스케줄러·Docker가 실행하는 곳. 항상 통합 브랜치(main/master). 여기서는 `git pull`과 배포 명령만 한다. 코드 수정·브랜치 전환·커밋은 하지 않는다(긴급 장애 예외는 전역 CLAUDE.md).
- **개발 폴더** `C:\Users\user\dev\minio_download_business_status_file`: 모든 수정은 여기서 한다. 작업 브랜치 → dev → main → push → 운영 폴더 pull.
- **배포**: 운영 폴더에서 `git pull`. 스케줄러 「전사업자번호 파일 송수신 작업」 다음 실행부터 반영.
- **개발 폴더 금지**: bat 실행(운영 경로가 박혀 있음), 운영과 같은 포트로 서버 띄우기, MinIO·SFTP 업로드나 납품까지 가는 실행.
- 원격 master. 흐름 dev → master(fast-forward).

