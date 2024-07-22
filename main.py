from minio import Minio, S3Error

import datetime
import os
# from ftplib import FTP
import paramiko

from config.settings import setting

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

def download_file(bucket_name, object_name, file_path):
    '''

    :param bucket_name:
    :param object_name:
    :param file_path:
    :return:
    '''
    try:
        # 파일 다운로드
        print(object_name)
        client.fget_object(bucket_name, object_name, file_path)
        print(f"'{object_name}' has been downloaded successfully.")
    except S3Error as exc:
        print("Error occurred:", exc)


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

def should_run(date):
    # 주어진 날짜(date)가 해당 조건을 충족하는지 확인
    if date.day == 21 and date.weekday() < 5:  # 첫 번째 조건: 실행일이 21일이고 평일인 경우
        return True
    elif date.day == 22 and date.weekday() == 0:  # 두 번째 조건: 실행일이 22일
        return True
    elif date.day == 23 and date.weekday() == 0:  # 세 번째 조건: 실행일이 23일
        return True
    return False

def run(today:datetime.date):

    today_str = today.strftime('%Y%m%d')
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
        create_sftp_directory(ftp_host, ftp_port, ftp_username, ftp_password, ftp_directory)
        send_file_to_sftp(ftp_host, ftp_port, ftp_username, ftp_password, file_path, ftp_directory)
        send_file_to_sftp(ftp_host, ftp_port, ftp_username, ftp_password, success_file_path, ftp_directory)


if __name__ == "__main__":
    today = datetime.date.today()
    if should_run(today):
        run(today=today)
    else:
        print("오늘은 실행일이 아닙니다.")
