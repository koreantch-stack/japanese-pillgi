# 일본어 필기

일본어 시구와 일상 문장을 태블릿 펜으로 따라 쓰는 웹앱입니다. 획순 안내 없이, 흐린 안내 글씨 위에 쓰고 단어마다 뜻을 확인합니다.

## 쓰는 법
1. GitHub 저장소 Settings → Pages → Branch를 main, 폴더를 / (root)로 저장합니다.
2. 잠시 뒤 https://koreantch-stack.github.io/japanese-pillgi/ 로 접속합니다.
3. 크롬 메뉴에서 홈 화면에 추가(앱 설치)를 누르면 앱처럼 열립니다.

## 데이터 수정
- 문장 원본은 tools/data_*.py 에 있습니다.
- `python3 tools/build_n5.py` 를 실행하면 poems.json 과 tools/검수표.md 가 다시 만들어집니다.
- 허용 한자를 늘리려면 `python3 tools/build_n5.py 私分` 처럼 한자를 인자로 줍니다.
- 번역과 읽는 법은 AI가 작성한 것이라 검수 전입니다.

## 저장 위치
쓴 글씨와 진도는 기기별 브라우저에 저장되어 기기 간 동기화되지 않습니다.
