from pydantic import BaseSettings
import os
from dotenv import load_dotenv, find_dotenv


class Settings(BaseSettings):
    ftp_host: str
    ftp_port: int
    ftp_username: str
    ftp_password: str
    ftp_base_directory_path: str
    bucket_name: str
    DEBUG: str
    access_key: str
    secret_key: str
    minio_url: str

    class Config:
        env_file_encoding = 'utf-8'

load_dotenv(find_dotenv('.env'))

# 환경 변수에서 APP_ENV 값을 가져오고, 기본값으로 'dev'를 사용합니다.
env = os.environ.get("APP_ENV", "dev")
env_file = os.path.join(os.path.dirname(__file__), f".env.{env}")

# 지정된 환경 파일을 로드합니다.
load_dotenv(env_file, override=True)

# 설정 객체를 생성합니다.
setting = Settings()

# 설정 파일 경로를 출력합니다.
print(f"Using env file: {env_file}")