from dotenv import load_dotenv

# database.py/security.py 등이 모듈 import 시점에 os.getenv()로 설정을 읽으므로,
# 그 서브모듈들이 import되기 전에(패키지 초기화 시점에) .env를 먼저 로드해야 한다.
load_dotenv()
