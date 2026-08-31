---
signal: GREEN
phase: 리뷰
step: 1
attempt: 0
iteration: 186
updated: 2026-08-31
ctx: 85
night_iterations: 58
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 37 `indexer-interrupt` 리뷰 phase 끝** — 계획서 `docs/plan_indexer-interrupt.md`
(실측은 12절), 브랜치 `loop/indexer-interrupt`(`loop/signal-budget-cover` `a8ad633` 에서 팠다).
개발 스텝 1·2 · 테스트 1 완료. **리뷰 지적 4건 — 제품 동작 지적 0건**(자동 2 = 둘 다 문서 ·
보류 2 = 안내 문구, `severity.md` 3절이 트랜잭션 경계·사용자 표면을 승인 쪽으로 못박는다).
**제품 코드는 한 줄도 안 고쳤다.** 단위 **456건 OK** · e2e 7종 rc=0 ·
`data/crawl.db` sha256 무변경(`85c96744…`). **다음은 e2e phase.**
계획 36 까지 전부 DONE. **`main` 병합은 사람이 정한다.**

## 이번 계획이 여는 것

**색인 도중 Ctrl-C 가 색인을 지운다.** `index_pages()` 는 스키마가 드리프트하면
`DROP TABLE docs` → `CREATE` → 전건 `INSERT` → `commit` 으로 재구축하는데,
**Python 3.9.6 `sqlite3` 은 DDL 을 암묵 트랜잭션에 안 넣는다** — DROP/CREATE 는 그 자리에서
커밋되고 INSERT 만 롤백된다. 그래서 재구축 중 SIGINT 는 **옛 6000행을 지우고 0행을 남긴다.**
그때부터 검색은 전부 `결과 없음` 이고, 이는 크롤 데이터가 없는 것과 **구별되지 않는다**
(21·26·29 가 세 번 닫은 실패 모양). 곁들여 `indexer.main` 만 중단 계약이 없었다
(`crawl` rc 130 · `serve` rc 0 · `indexer` 트레이스백 + rc -2).

## 리뷰 phase 가 찾은 것 (2026-08-31) — 자세한 것은 계획서 12절

- **락은 실측으로 닫았다.** 읽어서 판정하지 않고 `serve` 가 쓰는 것과 같은
  `indexer.search()` 를 다른 프로세스에서 두드리며 색인을 돌렸다. DB 는 WAL 이라
  (`store.py:23`) 독자가 안 막힌다 — 평소 증분 갈래(3000행 + 3000행·5.00초) **59/59 성공**,
  p50 77.6ms 대 대조군 71.3ms(**+9%, 정지 구간 0**). 재구축 갈래 390회에서
  `database is locked` **0회**(나온 예외는 전부 `StaleIndexError` — 옛 정의 색인이 원래
  못 쓰이는 기존 계약이지 이 diff 와 무관하다).
- **쓰기 창은 이 diff 가 안 늘렸다.** `INSERT` 루프는 원래부터 한 트랜잭션이었다
  (`CREATE` 뒤 `in_transaction=False`, 첫 `INSERT` 뒤 `True`). `BEGIN` 이 창에 새로 넣은
  것은 `DROP`/`CREATE` 두 문장뿐이다.
- **중첩 트랜잭션은 불가능하다.** `index_pages` 가 매 호출 자기 연결을 열고, 호출자 41곳
  전부 경로 문자열만 넘긴다(연결 객체를 받는 호출자 0).
- **이득이 계획서보다 넓다.** `RuntimeError`·`sqlite3.OperationalError`·`MemoryError` 를
  재구축 중에 주입해도 셋 다 옛 색인이 산다 — `finally: db.close()` 가 롤백한다.
  SIGINT 만이 아니라 *모든* 예외에서 안전해졌다.
- **보류 2건은 둘 다 "데이터는 옳고 문구가 어긋난다".** ① `db.commit()` 이 끝난 **뒤**
  도착한 중단은 `색인은 바뀌지 않았다` 를 거짓으로 만든다(결정적으로 재현: rc 130 인데
  실제 `docs` 는 2행 새 정의). ② `--query` 도중 중단도 같은 색인 안내를 낸다.
  둘 다 재실행이 멱등이라 해가 제한적이고, 고치면 사용자 표면이 바뀌어 자기 RED 가 필요하다.

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

- 단위 **456건 OK**(3.87초, rc 0) — `PYTHONPATH=src python3 -m unittest discover -s tests`.
- e2e 7종 개별 rc **0**: `indexer_e2e`(3문서·증분 0) · `search_api_e2e`(p95 **2.28ms**) ·
  `tokenizer_e2e` · `pagination_ui_e2e` · `noindex_e2e` · `non_ascii_e2e` · `crawl_e2e`.
- **락 실측** — 위 "리뷰 phase 가 찾은 것" 첫 항목. 임시 DB 에서만 돌렸다.
- **성능(완료 기준 5)** — 6000문서 A/B: 평소 **0.69초** vs 재구축 **0.66초**.
  명시 `BEGIN` 은 안 느리다.
- **린터·타입체커 없다**(`docs/project.md`) — 검증은 위 줄들이 전부다.
- `data/crawl.db` sha256 `85c96744…5bda18` **무변경**(e2e 전후 두 번). 스크래치패드 삭제 완료.

## 집안일

- **`history_current.md` 회전 완료** — 336줄(상한 300 초과)이라 계획 35 여섯 반복을
  `history_014.md` 로 밀었다. **336 → 192줄.** 테스트 phase 가 "미결" 로 넘긴 것을
  리뷰가 주웠고, 그래서 `digest ## 반복 실패` 에 "회전이 또 한 반복 늦었다" 로 적었다.
- **`digest.md` 232줄(상한 200) — 아직 미결.** 이번 반복이 9줄을 더했다(회전 1줄 +
  반복 실패 3회째 8줄). 회전 전에 `index.md`·`plan_history_*.md` 참조 확인이
  선행이다(`digest [6]`) — 그 확인 자체가 한 반복이라 e2e 뒤로 미룬다.

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마를 안 건드린다. 탐침·e2e 는 임시 디렉터리에서만.
- 기존 단언을 낮추지 않는다 — 특히 21 의 `NoCrawlDataError`·`StaleIndexError` 갈래.
- `except KeyboardInterrupt` 가 다른 예외를 같이 삼키면 RED(변이 M5 가 잰다).
- 색인 성능 10% 이상 회귀면 RED.
- 도메인당 요청 간격 1초 이상 · robots.txt 준수.
- 외부 네트워크 금지 · `docs/specs/` 읽기만 · `--no-verify` 금지 · `main` 직접 커밋 금지.
