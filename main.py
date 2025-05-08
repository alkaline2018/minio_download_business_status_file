from file_inspector import FileInspector
from file_inspector.formatter.slack_formatter import format_slack_message
from minio import Minio, S3Error

import datetime
import os
# from ftplib import FTP
import paramiko

from config.settings import setting
from utils.decorators import log_function_call
from utils.minio_helper import send_file_to_minio
from utils.slack import send_slack_message, SlackColor

access_key = setting.access_key
secret_key = setting.secret_key

client = Minio(
    setting.minio_url,
    access_key=access_key,
    secret_key=secret_key,
    secure=True
)


def delete_files_in_folder(folder_path):
    # 해당 폴더 안의 파일 목록을 가져옴
    file_list = os.listdir(folder_path)

    # 각 파일에 대해 반복
    for file_name in file_list:
        # 파일의 전체 경로 생성
        file_path = os.path.join(folder_path, file_name)

        # 파일인지 확인하고 삭제
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"{file_name} 삭제됨")

@log_function_call
def download_file(bucket_name, object_name, file_path):
    '''

    :param bucket_name:
    :param object_name:
    :param file_path:
    :return:
    '''
    # 파일 다운로드
    client.fget_object(bucket_name, object_name, file_path)


def create_sftp_directory(sftp_host, sftp_port, sftp_username, sftp_password, directory_path):
    try:
        # SSH 클라이언트 생성
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # SSH 연결
        ssh_client.connect(hostname=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password)

        # SFTP 세션 열기
        sftp_client = ssh_client.open_sftp()

        # 새로운 디렉토리 생성
        sftp_client.mkdir(directory_path)
        print("새로운 디렉토리가 생성되었습니다.")

        # 연결 종료
        sftp_client.close()
        ssh_client.close()
    except Exception as e:
        print("디렉토리 생성 중 오류가 발생했습니다:", e)


def send_file_to_sftp(sftp_host, sftp_port, sftp_username, sftp_password, local_file_path, remote_directory):
    try:
        # SSH 클라이언트 생성
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # SSH 연결
        ssh_client.connect(hostname=sftp_host, port=sftp_port, username=sftp_username, password=sftp_password)

        # SFTP 세션 열기
        sftp_client = ssh_client.open_sftp()

        # 로컬 파일 열기
        with open(local_file_path, 'rb') as local_file:
            # 원격 디렉토리로 파일 전송
            sftp_client.putfo(local_file, remote_directory + '/' + local_file_path.split('/')[-1])
            print("파일이 성공적으로 전송되었습니다.")

        # 연결 종료
        sftp_client.close()
        ssh_client.close()
    except Exception as e:
        print("파일 전송 중 오류가 발생했습니다:", e)


@log_function_call
def should_run(date):
    # 주어진 날짜(date)가 해당 조건을 충족하는지 확인
    if date.day == 20 and date.weekday() < 5:  # 첫 번째 조건: 실행일이 20일이고 평일인 경우
        return True
    elif date.day == 21 and date.weekday() == 0:  # 두 번째 조건: 실행일이 21일
        return True
    elif date.day == 22 and date.weekday() == 0:  # 세 번째 조건: 실행일이 22일
        return True
    return False

def inspect_and_notify_file(
    file_path: str, channel_id: str = "#file_inspector"
) -> bool:
    """
    주어진 파일을 검사하고, 검사 결과를 슬랙 채널에 전송하는 함수입니다.

    Args:
        file_path (str): 검사할 파일의 경로
        channel_id (str): 슬랙 채널 ID (기본값은 "#file_inspector")

    Returns:
        bool: 슬랙 메시지 전송 성공 여부 (True: 성공, False: 실패)
    """
    try:
        # 파일 검사기 생성 및 검사 수행
        inspector = FileInspector()
        result = inspector.inspect(file_path)

        # 검사 결과의 유효성 확인
        if not result or not hasattr(result, "file_info") or not hasattr(result, "df"):
            raise ValueError("유효하지 않은 검사 결과입니다.")

        # 슬랙 메시지 포맷팅
        slack_message = format_slack_message(result.file_info, result.df)

        # 슬랙 메시지 전송
        send_slack_message(
            message=slack_message, channel_id=channel_id, color=SlackColor.GOOD.value
        )

        # 성공적으로 메시지를 전송한 경우 True 반환
        return True

    except Exception as e:
        # 예외 발생 시 에러 메시지를 슬랙으로 전송
        error_message = f"[파일 검사 실패 ❌] {file_path} 검사 중 오류 발생: {str(e)}"
        try:
            send_slack_message(
                message=error_message,
                channel_id=channel_id,
                color=SlackColor.DANGER.value,
            )
        except Exception:
            # 슬랙 전송도 실패할 경우 콘솔 출력으로 대체
            print("Slack 메시지 전송 실패:", error_message)

        # 실패했음을 나타내는 False 반환
        return False

def run(today:datetime.date):

    today_str = today.strftime('%Y%m%d')    # today_str = "20240821"
    today_yyyy_slash_mm = today.strftime('%Y/%m')
    folder_path = "./download"
    ftp_host = setting.ftp_host
    ftp_port = setting.ftp_port
    ftp_username = setting.ftp_username
    ftp_password = setting.ftp_password
    ftp_directory = f"{setting.ftp_base_directory_path}/{today_yyyy_slash_mm}"

    delete_files_in_folder(folder_path)
    bucket_name = setting.bucket_name
    day_list = [today_str]
    # day_list = ["20240415", "20240418", "20240419"]

    for today_str in day_list:
        file_path = f"{folder_path}/business_no_{today_str}.csv"
        success_file_path = "./_success"
        object_name = f"business_{today_str}"
        download_file(bucket_name, object_name, file_path)
        inspect_and_notify_file(file_path=file_path)
        send_file_to_minio(file_path)
        create_sftp_directory(ftp_host, ftp_port, ftp_username, ftp_password, ftp_directory)
        send_file_to_sftp(ftp_host, ftp_port, ftp_username, ftp_password, file_path, ftp_directory)
        send_file_to_sftp(ftp_host, ftp_port, ftp_username, ftp_password, success_file_path, ftp_directory)


if __name__ == "__main__":
    # NOTE: 임시로 돌리고 싶을 때 쓰는 거
    # date_str = "2025-04-21"  # 원하는 날짜 입력 (YYYY-MM-DD 형식)
    # today = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    # run(today=today)
    # NOTE:----------------------

    today = datetime.date.today() - datetime.timedelta(days=1)

    print(today)
    # run(today=today)
    if should_run(today):
        run(today=today)
        print("오늘은 실행일 입니다.")
    else:
        print("오늘은 실행일이 아닙니다.")
