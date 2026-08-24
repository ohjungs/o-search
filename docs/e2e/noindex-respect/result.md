# e2e 결과: noindex-respect — 통과 (2026-08-25 야간)

명령: `PYTHONPATH=src python3 e2e/noindex_e2e.py` (이 phase 에서 신설)

| 시나리오 (plan_noindex-respect.md) | 결과 |
|---|---|
| 로컬 서버 4페이지(목차 / 일반 / `content="noindex"` / `content="none"`) crawl 수집 | 통과 (pages 4행) |
| 색인 명령 → 거부 문서는 색인 안 함 | 통과 (stdout "2 문서 색인" — 목차와 일반 문서만) |
| `--query pyeongsan` → 일반 문서만 | 통과 (`/open` 나오고 `/noindex`·`/none` 없음) — 셋 다 본문에 같은 낱말을 담아 갈렸다 |
| 이미 색인된 문서가 뒤늦게 noindex 선언 → 색인에서 제거 | 통과 ("0 문서 색인" + "1 문서 색인 제외 — noindex 선언") |
| 제거 후 같은 질의 → 결과 없음 | 통과 (URL 0건, "결과 없음" 출력으로 침묵하지 않음) |

- 판단 메모: 뒤늦은 noindex 상황은 `pages.html` 을 sqlite 로 직접 갱신해 만들었다.
  `src/websearch/crawl.py` 가 기수집 URL 을 건너뛰어 CLI 재크롤로는 html 이 갱신되지 않기 때문이다
  (`docs/digest.md` [5] 재크롤 스킵, 이 계획 범위 밖). **검증 대상인 색인·질의 명령은
  사용자가 하는 그대로** `python3 -m websearch.indexer` 모듈 실행이다.
  수집만 `crawl()` 을 `-c` 로 감쌌다 — crawl CLI 에 db 경로 인자가 없다(기존 e2e 2개와 같은 이유).
- e2e 앞 관문: 전체 테스트 90/90 통과 0.048s · 기존 e2e 2개 회귀 없음
  (crawl: 수집 15·차단 0·최소 간격 1.000s / indexer: 3문서 색인·한영 질의 매치) ·
  린트/타입체크 없음(project.md)
- 품질 기준: 경량 3(신규 의존성 0) **통과 — stdlib 만 씀**. 크롤 윤리 축은
  **이 계획이 닫은 것** — robots.txt(crawler-core)에 이어 meta robots 까지 준수한다.
  나머지 축(성능 p95·RSS·검색 품질 80%·디자인)은 여전히 미검증 — 측정 명령이 없다
  (search-api·search-ui·quality-eval 계획에서 생성).
- 만든 파일: e2e/noindex_e2e.py, docs/e2e/noindex-respect/result.md
- 소요: 3.7s (도메인당 1초 간격 정책상 수집이 대부분)
