from file_inspector import FileInspector
from file_inspector.formatter.slack_formatter import format_slack_message
from minio import Minio, S3Error

import datetime
import os
# from ftplib import FTP
import paramiko

from config.settings import setting
from utils.decorators import log_function_call
from utils.minio_helper import send_file_to_minio, create_object_name
from utils.slack import send_slack_message, SlackColor
from utils.validate_util import request_validate_data

access_key = setting.access_key
secret_key = setting.secret_key

client = Minio(
    setting.minio_url,
    access_key=access_key,
    secret_key=secret_key,
    secure=True
)


def delete_files_in_folder(folder_path: str) -> None:
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
def download_file(bucket_name: str, object_name: str, file_path: str) -> None:
    """
    Downloads a file from the specified bucket and object name, saving it to the
    specified file path. Utilizes a client to perform the file download operation.

    Args:
        bucket_name: The name of the bucket from which to download the file.
        object_name: The name of the object to be downloaded.
        file_path: The local file path where the downloaded file will be saved.

    Returns:
        None
    """
    # 파일 다운로드
    print(f"Downloading file from {bucket_name}/{object_name} to {file_path}")
    client.fget_object(bucket_name, object_name, file_path)


def create_sftp_directory(sftp_host, sftp_port, sftp_username, sftp_password, directory_path) -> None:
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


def send_file_to_sftp(sftp_host: str, sftp_port: int, sftp_username: str, sftp_password: str, local_file_path: str, remote_directory: str = "./"):
    """
    Uploads a local file to a remote SFTP server.

    This function establishes an SSH connection to the specified SFTP host, opens an
    SFTP session, and uploads the provided file from the local machine to the
    specified remote directory on the SFTP server. It handles both the connection
    management and file transfer.

    Parameters:
        sftp_host: str
            The hostname or IP address of the SFTP server.
        sftp_port: int
            The port number for the SFTP server connection.
        sftp_username: str
            The username for authentication with the SFTP server.
        sftp_password: str
            The password for authentication with the SFTP server.
        local_file_path: str
            The full path to the local file that will be transferred.
        remote_directory: str
            The remote directory where the file will be uploaded.

    Raises:
        Exception
            If any error occurs during the file transfer process.
    """
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
        # 납품 실패가 출력만 남고 묻히지 않도록 실패로 올린다 (__main__에서 Slack 알림)
        raise


@log_function_call
def should_run(date: datetime.date) -> bool:
    """
    Checks if the provided date meets specific conditions for execution.

    This function evaluates whether the given date matches certain conditions,
    such as being on specific days of the month and falling on a weekday or
    specific weekdays. It is used to determine if the given date should trigger
    specific actions based on those conditions.

    Args:
        date (datetime.date): The date to be checked against the conditions.

    Returns:
        bool: True if the date meets any of the conditions; False otherwise.
    """
    # 주어진 날짜(date)가 해당 조건을 충족하는지 확인
    # TODO: 2, 3, 4 로 바꿔줄 것.
    if date.day == 2 and date.weekday() < 5:  # 첫 번째 조건: 실행일이 2일이고 평일인 경우
        return True
    elif date.day == 3 and date.weekday() == 0:  # 두 번째 조건: 실행일이 3일
        return True
    elif date.day == 4 and date.weekday() == 0:  # 세 번째 조건: 실행일이 4일
        return True
    elif date.day == 5 and date.weekday() == 0:  # 세 번째 조건: 실행일이 4일
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

def run(today: datetime.date) -> None:
    """
    Executes a sequence of operations for file handling with daily business data.

    This function performs an automated process involving file download,
    local operations, and file transfers. It retrieves business data for
    specific days and handles those files by processing them and transferring
    them to appropriate locations like object storage, MinIO, and SFTP servers.
    It uses the current date to determine the directory structure and file
    names for the operations. Operations include cleaning up folders, file
    inspections, creating directory structures, and file movement.

    Parameters:
        today (datetime.date): The current date used to determine the
        directory structure and file names for the process.
    """

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
        # MinIO 업로드된 CSV object 경로로 DaedalusMark GX 검수 트리거.
        # create_object_name 을 재사용해 실제 업로드된 object key 와 동일하게 맞춤.
        # (_success 마커는 MinIO 에 올리지 않으며, 유틸에서도 비 CSV 는 제외됨)
        request_validate_data(create_object_name(file_path))
        create_sftp_directory(ftp_host, ftp_port, ftp_username, ftp_password, ftp_directory)
        send_file_to_sftp(ftp_host, ftp_port, ftp_username, ftp_password, file_path, ftp_directory)
        send_file_to_sftp(ftp_host, ftp_port, ftp_username, ftp_password, success_file_path, ftp_directory)


def notify_failure(target_date: datetime.date, error: Exception) -> None:
    """실행 실패를 Slack으로 알린다. (2026-10 정기 실행 4회 실패가 로그에만 남고 묻혔던 문제 대응)"""
    message = (
        f"[전사업자번호 파일 송수신 실패 ❌] 대상일 {target_date:%Y-%m-%d}\n"
        f"{type(error).__name__}: {error}\n"
        f"수동 재실행: python main.py --date {target_date:%Y-%m-%d}"
    )
    try:
        send_slack_message(
            message=message, channel_id="#file_inspector", color=SlackColor.DANGER.value
        )
    except Exception:
        print("Slack 메시지 전송 실패:", message)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="전사업자번호 파일 MinIO → SFTP 송수신")
    # NOTE: 수동 재실행은 코드의 날짜를 고치지 말고 이 인자로 한다.
    #       (2026-09 수동 실행 때 고친 날짜가 남아 10월 정기 실행이 전부 9/7 파일을 찾다 실패했음)
    parser.add_argument(
        "--date", help="이 날짜(YYYY-MM-DD) 파일을 실행일 조건과 상관없이 처리한다"
    )
    args = parser.parse_args()

    if args.date:
        today = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        today = datetime.date.today() - datetime.timedelta(days=1)

    print(today)
    if args.date or should_run(today):
        try:
            run(today=today)
        except Exception as e:
            notify_failure(today, e)
            raise
        print("오늘은 실행일 입니다.")
    else:
        print("오늘은 실행일이 아닙니다.")
