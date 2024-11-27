import logging

# 전역 로그 설정
logger = logging.getLogger('globalLogger')
logger.setLevel(logging.DEBUG)

# 콘솔 핸들러 추가
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

# 포맷터 설정
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

# 핸들러를 로거에 추가
logger.addHandler(console_handler)

# 파일 핸들러 추가
file_handler = logging.FileHandler('./logs/application.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
