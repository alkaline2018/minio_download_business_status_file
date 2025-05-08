import os
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

def create_object_name(file_path: str) -> str:
    """
    주어진 파일 경로와 사업자 번호를 이용하여
    object_name을 생성합니다. 형식:
    scrapy_data/yyyy/mm/business_no/file_name
    """
    # 현재 날짜
    now = datetime.now()
    year = now.strftime("%Y")
    month = now.strftime("%m")

    # 파일 이름 추출
    file_name = os.path.basename(file_path)

    # object name 구성
    object_name = f"scrap_data/{year}/{month}/business_no/{file_name}"
    return object_name


class MinioHelper:
    def __init__(self, bucket_name: str):
        """
        MinIOHelper 클래스 초기화
        """
        # .env 파일에서 환경 변수를 로드
        load_dotenv()

        MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
        ACCESS_KEY = os.getenv("MINIO_FILE_MANAGER_ACCESS_KEY")
        SECRET_KEY = os.getenv("MINIO_FILE_MANAGER_SECRET_KEY")
        self.client = Minio(
            MINIO_ENDPOINT, access_key=ACCESS_KEY, secret_key=SECRET_KEY, secure=False
        )
        self.bucket_name = bucket_name

        # 버킷이 존재하지 않으면 생성
        if not self.client.bucket_exists(bucket_name):
            print("Bucket doesn't exist")
            # self.client.make_bucket(bucket_name)

    def upload_file(self, file_path: str, object_name: str):
        """
        파일을 MinIO에 업로드
        """
        try:
            self.client.fput_object(self.bucket_name, object_name, file_path)
            print(
                f"File '{file_path}' uploaded as '{object_name}' in bucket '{self.bucket_name}'."
            )
        except S3Error as e:
            print("Upload error:", e)

    def download_file(self, object_name: str, file_path: str):
        """
        MinIO에서 파일 다운로드
        """
        try:
            self.client.fget_object(self.bucket_name, object_name, file_path)
            print(f"File '{object_name}' downloaded to '{file_path}'.")
        except S3Error as e:
            print("Download error:", e)

    def file_exists(self, object_name: str) -> bool:
        """
        파일 존재 여부 확인
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False

    def list_files(self, prefix: str = ""):
        """
        버킷 내 파일 목록 확인
        """
        try:
            objects = self.client.list_objects(
                self.bucket_name, prefix=prefix, recursive=True
            )
            for obj in objects:
                print(obj.object_name)
        except S3Error as e:
            print("List files error:", e)


@lru_cache(maxsize=1)
def get_minio_helper():
    """MinioHelper 싱글턴 인스턴스 반환"""
    return MinioHelper(bucket_name="devops")


def send_file_to_minio(file_path, **kwargs):
    dev_minio = get_minio_helper()
    object_name = create_object_name(file_path=file_path)
    dev_minio.upload_file(
        file_path=file_path,
        object_name=object_name,
    )

    return f"파일 적재 성공\n{object_name} 에 \n{file_path} 의 파일이 적재 됐습니다."
