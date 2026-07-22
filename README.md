# 음식물 조달시장 분석 대시보드

## 페이지
- `docs/index.html`: 시작 페이지
- `docs/military.html`: 군수품 - 발주계획 / 공고 / 계약정보
- `docs/g2b.html`: 나라장터 - 공고 / 계약정보

## GitHub Secret
저장소의 `Settings > Secrets and variables > Actions`에서 아래 Secret을 등록합니다.

- `GOOGLE_AUTH_JSON`: Google 서비스계정 JSON 파일 전체 내용

현재 `dashboard_data.py`는 Google Sheets에서 데이터를 읽으므로 `DATA_GO_KR_API_KEY`를 사용하지 않습니다. 공공데이터포털 수집기를 이 저장소에 추가할 때 별도로 등록하면 됩니다.

## 최초 실행
1. Actions 탭에서 `Update dashboard data`를 선택합니다.
2. `Run workflow`를 실행합니다.
3. 실행 완료 후 `docs/data/summary.json`과 `docs/data.json`이 생성됩니다.

## GitHub Pages
`Settings > Pages`에서 다음과 같이 설정합니다.
- Source: Deploy from a branch
- Branch: `main`
- Folder: `/docs`
