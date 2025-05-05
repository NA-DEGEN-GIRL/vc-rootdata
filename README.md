# Rootdata VC 프로젝트 텔레그램 봇

이 봇은 루트데이터(Rootdata) API와 연동하여,  
VC(벤처캐피탈) 투자 정보와 투자자 등급을 분석해  
텔레그램 명령어로 바로 조회할 수 있습니다.

## 기능 안내

- `/vc [프로젝트명]`으로 텔레그램에서 특정 프로젝트의 VC 투자 내역, 투자자 등급, 총 투자액, 소셜 미디어 등 정보를 바로 조회
- Tier1, Tier2, 기타 투자자 및 **Lead 투자자 표시** (밑줄)
- **Rootdata 상세 보기 링크(미리보기 비활성화)** 제공
- **Fuzzy match** 기능으로 오타/비슷한 이름 검색 가능
- **권한 관리**: 지정한 관리자, 혹은 허용 chat_id에서만 명령 실행

---

## 설치 및 실행 방법

### 1. 사전 요구 사항

- Python 3.9+
- 아래 라이브러리 설치 필요

```bash
pip install python-telegram-bot thefuzz requests
```

### 2. api_key.py 파일 작성

프로젝트 루트에 아래와 같은 내용으로 `api_key.py` 파일 생성

```python
API_KEY_ROOTDATA = "여기에_루트데이터_API_키"
telegram_bot_token = "여기에_텔레그램_봇_토큰"
admin_id = 123456789        # (int) 관리자 user_id
allowed_chat_id = -10012345678  # (int) 허용할 채팅방(chat_id, 그룹일 경우 음수로 시작)
```

> **`admin_id`, `allowed_chat_id`는 정수(int)로 넣어주세요**

---

### 3. 실행

```bash
python main.py
```

---

## 사용법 예시

- 텔레그램 채팅에서(허용된 유저/채널에 한해)
  ```
  /vc Polygon
  ```
- 결과 예시:

  ```
  프로젝트 이름: Polygon
  • 한 줄 소개: ...
  • Tag: layer2, defi

  소셜 미디어:
  • web: https://polygon.technology
  • X: https://twitter.com/0xPolygon

  💰 총 투자액: $123,456,789

  👑 Tier 1 투자자: <u>Sequoia Capital</u>, Multicoin Capital
  🥂 Tier 2 투자자: Paradigm, <u>Jump Crypto</u>
  🔹 기타 투자자: ...

  <a href="https://rootdata.com/...">Rootdata</a>
  ```

- Lead 투자자는 **밑줄(<u>이름</u>)** 표시로 구분

---

## 기타

- Tier1은 cryptorank 데이터를 기반으로, Tier2는 fuzzy match 및 normalize로 판별
- 텔레그램 마크다운/HTML 파싱 활용, 미리보기(Preview) 노출 없음
- 프로젝트 검색 시 오타 등에도 유연하게 대응

---

## 참고/문의

- 문제가 있거나 개선/기능 추가 요청은 [깃허브 이슈] 또는 Telegram 관리자로 문의해주세요