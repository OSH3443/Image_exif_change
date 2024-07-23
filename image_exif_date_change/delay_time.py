import random
from datetime import datetime, timedelta


def delay_generator(delay_ratio: dict[int, int]) -> int:
    """
    주어진 확률에 따라 숫자를 반환하는 함수
    :param delay_ratio: 숫자와 생성 비율을 담은 딕셔너리
    :return: 확률에 따라 생성된 숫자
    """

    # 숫자와 생성 비율에 대한 키와 값 추출
    numbers = list(delay_ratio.keys())
    probabilities = list(delay_ratio.values())

    # 확률에 따라 숫자 선택
    generated_number = random.choices(numbers, probabilities)[0]

    return generated_number


def add_delay(modify_date: str, delay_seconds: int) -> str:
    """
    주어진 날짜에 지정된 시간(초)을 더하여 수정된 날짜를 문자열로 반환합니다.
    :param modify_date: "%Y:%m:%d %H:%M:%S" 형식의 원본 날짜 문자열입니다.
    :param delay_seconds: 원본 날짜에 더할 초 단위의 시간입니다.
    :return: 수정된 날짜를 동일한 형식의 문자열로 반환합니다.
    """

    # 입력된 modify_date 문자열을 datetime 객체로 변환합니다.
    modify_datetime = datetime.strptime(modify_date, "%Y:%m:%d %H:%M:%S")

    # 초를 더해주기
    modify_datetime += timedelta(seconds=delay_seconds)

    # 변환된 날짜를 다시 문자열로 변환
    modify_date = modify_datetime.strftime("%Y:%m:%d %H:%M:%S")

    return modify_date


def check_time(start_time, end_time) -> str:
    # 이미지 파일을 처리하는 데 걸린 시간 (초)
    processing_time = end_time - start_time

    # 예상 시간을 시, 분, 초로 변환
    hours = int(processing_time / 3600)
    minutes = int((processing_time % 3600) / 60)
    seconds = int(processing_time % 60)

    return (f'시작시간 : {start_time} 끝난시간 : {end_time}\n'
            f'이미지를 처리하는 데 걸린 시간: {hours}시간 {minutes}분 {seconds}초')