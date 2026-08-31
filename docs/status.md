---
signal: GREEN
phase: 리뷰
step: 1
attempt: 0
iteration: 185
updated: 2026-08-31
ctx: 85
night_iterations: 58
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 37 `indexer-interrupt` 테스트 phase 끝** — 계획서 `docs/plan_indexer-interrupt.md`,
브랜치 `loop/indexer-interrupt`(`loop/signal-budget-cover` `a8ad633` 에서 팠다).
개발 스텝 1·2 완료(재구축이 한 트랜잭션 · `main` 이 rc **130** 과 한 줄 안내).
테스트는 **갭 하나를 메웠다** — 재구축이 아닌 **평소 색인 경로의 중단**을 재는 단언이
0건이었다(`tests/test_indexer.py:123`
`TestIndexPages.test_interrupted_incremental_run_indexes_nothing`). 단위 455 → **456건 OK**,
e2e 7종 rc=0, `data/crawl.db` sha256 무변경(`85c96744…`). **다음은 리뷰 phase.**
계획 36 까지 전부 DONE. **`main` 병합은 사람이 정한다.**

## 이번 계획이 여는 것

**색인 도중 Ctrl-C 가 색인을 지운다.** `index_pages()` 는 스키마가 드리프트하면
`DROP TABLE docs` → `CREATE` → 전건 `INSERT` → `commit` 으로 재구축하는데,
**Python 3.9.6 `sqlite3` 은 DDL 을 암묵 트랜잭션에 안 넣는다** — DROP/CREATE 는 그 자리에서
커밋되고 INSERT 만 롤백된다. 그래서 재구축 중 SIGINT 는 **옛 6000행을 지우고 0행을 남긴다.**
그때부터 검색은 전부 `결과 없음` 이고, 이는 크롤 데이터가 없는 것과 **구별되지 않는다**
(21·26·29 가 세 번 닫은 실패 모양). 곁들여 `indexer.main` 만 중단 계약이 없었다
(`crawl` rc 130 · `serve` rc 0 · `indexer` 트레이스백 + rc -2).

## 테스트 phase 가 찾은 것 (2026-08-31)

- **메운 갭(중요도 8).** `main` 이 내는 안내 "색인은 바뀌지 않았다" 는 **두 갈래 모두에서**
  참이라고 주장하는데, 평소(증분) 경로의 중단을 재는 단언이 없었다. 계획서 기대 결과 2번이
  "이미 참, 회귀 방지로 못박는다" 라고 적어 둔 자리이고 착수 탐침 A 가 손으로 한 번 봤을 뿐이다.
  새 단언은 **둘째 문서에서** 끊어 "부분만 남는다" 를 잰다 — 변이 **M7**(`indexed += 1` 뒤에
  `db.commit()` 한 줄)을 심으면 그 단언 **하나만** 죽는다(`.git` 없는 사본에서 확인).
- **남긴 갭(8 미만).** ① 중단 뒤 재실행이 재구축을 마치는 회복 경로 → 기존 드리프트 단언
  둘의 합성이라 새로 쓰지 않았다. ② 중단된 색인이 DB 락을 남기지 않는다 → 단언들이
  `finally: db.close()` 뒤에 다시 열어 읽으므로 이미 지나간다.
- **e2e phase 로 넘기는 것.** `indexer` 중단을 **실제 CLI + SIGINT** 로 지나는 e2e 가 아직
  없다(중단 e2e 둘은 `crawl` 쪽 `interrupt_e2e`·`deadline_e2e`). 단위는 예외 주입이라
  진짜 시그널·진짜 프로세스 종료 코드를 못 잰다 — 착수 탐침 A·B 가 그것을 손으로 쟀다.

## 검증 (전부 이번 반복에 직접 돌렸다)

- 단위 **456건 OK**(3.9초) — `PYTHONPATH=src python3 -m unittest discover -s tests`.
- e2e 7종 개별 rc **0**: `indexer_e2e`(3문서·증분 0) · `search_api_e2e`(p95 2.30ms) ·
  `tokenizer_e2e` · `pagination_ui_e2e` · `noindex_e2e` · `quality_eval`(한 20/20 · 영 19/20)
  · `perf_search`(p95 **8.97ms**, 예산 300ms 의 3.0%).
- **린터·타입체커 없다**(`docs/project.md`) — 검증은 위 두 줄이 전부다.
- `data/crawl.db` sha256 `85c96744…5bda18` **무변경**. 스크래치패드 사본 삭제 완료.

## 집안일 (미결로 넘긴다)

`digest.md` **223줄**(상한 200) · `history_current.md` 상한 300 근접. 회전 전에
`index.md`·`plan_history_*.md` 참조 확인이 선행이다(`digest [6]`).

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마를 안 건드린다. 탐침·e2e 는 임시 디렉터리에서만.
- 기존 단언을 낮추지 않는다 — 특히 21 의 `NoCrawlDataError`·`StaleIndexError` 갈래.
- `except KeyboardInterrupt` 가 다른 예외를 같이 삼키면 RED(변이 M5 가 잰다).
- 색인 성능 10% 이상 회귀면 RED.
- 도메인당 요청 간격 1초 이상 · robots.txt 준수.
- 외부 네트워크 금지 · `docs/specs/` 읽기만 · `--no-verify` 금지 · `main` 직접 커밋 금지.
