import functools
from .logger import logger  # logger.py의 logger를 가져옴

def log_function_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f'Calling function: {func.__name__}')
        logger.debug(f'Arguments: args={args}, kwargs={kwargs}')
        try:
            result = func(*args, **kwargs)
            logger.info(f'Function {func.__name__} returned: {result}')
            return result
        except Exception as e:
            logger.error(f"An error occurred in {func.__name__}: {str(e)}")
            logger.debug(f"Error type: {type(e).__name__}")
            raise  # 에러 재발생
    return wrapper
