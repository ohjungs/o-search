# e2e 결과: search-api — 통과 (2026-08-25 야간)

명령: `PYTHONPATH=src python3 e2e/search_api_e2e.py` (이 phase 에서 신설)

| 시나리오 (plan_search-api.md) | 결과 |
|---|---|
| 로컬 서버 15페이지(목차 + doc00~doc13) crawl 수집 후 색인 | 통과 (stdout "15 문서 색인") |
| `python3 -m websearch.serve <db> --port 0` 로 API 기동 | 통과 — stdout 첫 줄에서 실제 포트를 읽어 붙었다 |
| `GET /search?q=김치` | 통과 (200, 10건, 정답 URL 포함, 본문에 `김치` 그대로 — `\uXXXX` 없음) |
| `GET /search?q=김치&page=2` | 통과 (page 2, 5건, `has_next` 거짓, 1페이지와 겹침 0건) |
| `GET /search` (q 없음) → 400 | 통과 |
| `page=0` / `page=101` → 400 | 통과 (시나리오에 없던 두 건을 더했다 — 신뢰 경계가 CLI 기동 경로에서도 사는지) |
| `GET /없는경로` → 404 | 통과 |
| `POST /search` → 501 | 통과 (do_POST 스텁 없이 stdlib 이 낸다) |
| 어느 응답에도 트레이스백 없음 | 통과 (5건 전부 본문 검사) |
| `e2e/perf_search.py` 가 p50·p95 를 낸다 | 통과 (500문서 30회 축약 실행 — p95 1.65ms) |

- 이 e2e 가 유일하게 보는 것: **CLI 진입점과 crawl→색인→서빙 전체 경로.**
  단위 테스트 115건은 `serve.make_server()` 를 같은 프로세스 스레드로 부르므로
  `python3 -m websearch.serve` 의 인자 처리·포트 출력·서브프로세스 수명은 여기서만 돈다.
  포트를 고정하지 않고 stdout 에서 읽는 것이 설계가 `--port 0` 을 넣은 이유다.
- 문서 수를 15로 잡은 이유: 2페이지가 나오되 **딱 떨어지지 않게** 해서 마지막 페이지가
  5건 + `has_next` 거짓이 되게 했다. 딱 떨어지는 경계(20문서)는 단위 테스트가 본다 —
  둘이 같은 모양이면 한쪽이 낭비다.
- e2e 앞 관문: 전체 테스트 115/115 통과 0.46s · 기존 e2e 3개 회귀 없음
  (crawl: 수집 15·차단 0·최소 간격 1.004s / indexer: 3문서·한영 매치·증분 0문서 /
  noindex: 4수집 2색인·뒤늦은 noindex 제거) · 린트/타입체크 없음(project.md)
- 품질 기준: **성능 축을 이 계획이 열었다** — p95 6.60ms(3000문서) 기준선이
  `docs/project.md` 에 박혔다. 합격 판정이 아니라 회귀 비교선이다(컨셉의 300ms 는 100만 문서 기준).
  경량 3(신규 의존성 0) 통과 — stdlib 만. 검색 품질 80%·디자인 축은 여전히 미검증
  (quality-eval·search-ui 계획 소관).
- 만든 파일: e2e/search_api_e2e.py, docs/e2e/search-api/result.md
- 소요: 15.0s (도메인당 1초 간격 정책상 15페이지 수집이 대부분)
