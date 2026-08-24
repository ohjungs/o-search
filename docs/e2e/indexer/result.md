# e2e 결과: indexer — 통과 (2026-08-25 야간)

명령: `PYTHONPATH=src python3 e2e/indexer_e2e.py` (이 phase 에서 신설 — 계획 범위 밖 예외 3곳 중 e2e 디렉터리)

| 시나리오 (plan_indexer.md) | 결과 |
|---|---|
| 로컬 서버(한국어·영어 본문 3페이지) crawl 수집 → 색인 명령 | 통과 (stdout "3 문서 색인") |
| 한국어 질의 "김치" → 정답 URL 포함 | 통과 (`/kimchi`) — 2글자 질의 + 조사("김치를") + 인라인 태그(`<b>김치</b>`) |
| 영어 질의 "python" → 정답 URL 포함 | 통과 (`/python`) — 대소문자 무시 |
| 색인 명령 재실행 → "0 문서 색인" (증분) | 통과 |
| 무결과 질의 → 침묵하지 않음 | 통과 ("결과 없음", URL 없음) — 리뷰 수정분의 e2e 확인 |

- 판단 메모: 질의는 `python3 -m websearch.indexer` 모듈 실행으로 사용자가 하는 그대로 돌렸다.
  수집만 `crawl()` 을 `-c` 로 감쌌는데 crawl CLI 에 db 경로 인자가 없기 때문이다(crawl_e2e.py 와 같은 이유).
- e2e 앞 관문: 전체 테스트 71/71 통과 0.037s · 기존 crawl e2e 회귀 없음(수집 15, 차단 0, 최소 간격 1.005s) ·
  린트/타입체크 없음(project.md)
- 품질 기준: 경량 3(신규 의존성 0) **통과 — stdlib 만 씀**. 나머지 축(성능 p95 300ms·경량 RSS 2GB·
  검색 품질 정답 포함률 80%·디자인)은 **미검증 — 측정 명령이 아직 없다**
  (search-api·search-ui·quality-eval 계획에서 생성). 100만 문서 기준이라 지금은 측정 자체가 불가능하다.
- 만든 파일: e2e/indexer_e2e.py, docs/e2e/indexer/result.md
- 소요: 약 4s. `tests/` 와 분리돼 있어 전체 테스트(71건)에 딸려 돌지 않는 것을 확인했다
