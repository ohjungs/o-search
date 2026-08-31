---
signal: DONE
phase: e2e
step: 1
attempt: 0
iteration: 187
updated: 2026-08-31
ctx: 62
night_iterations: 59
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 37 `indexer-interrupt` DONE.** 계획서는 `docs/plan_history_023.md` 로 아카이브했고
e2e 결과는 `docs/e2e/indexer-interrupt/result.md` 에 있다. 브랜치 `loop/indexer-interrupt`
(`loop/signal-budget-cover` `a8ad633` 에서 팠다) — **`main` 병합은 사람이 정한다.**
계획 36 까지 전부 DONE·아카이브 완료. **열린 계획 0.**

## 이번 계획이 한 일

**색인 도중 Ctrl-C 가 색인을 지웠다.** `index_pages()` 는 스키마가 드리프트하면
`DROP TABLE docs` → `CREATE` → 전건 `INSERT` → `commit` 으로 재구축하는데,
**Python 3.9.6 `sqlite3` 은 DDL 을 암묵 트랜잭션에 안 넣는다** — DROP/CREATE 는 그 자리에서
커밋되고 INSERT 만 롤백된다. 착수 탐침 B 는 **`docs` 6000행이 0행으로** 끝나는 것을 실측했고,
그때부터 검색은 전부 `결과 없음` 이라 크롤 데이터가 없는 것과 **구별되지 않았다**
(21·26·29 가 세 번 닫은 실패 모양). 곁들여 `indexer.main` 만 중단 계약이 없었다.

**제품 diff 는 `src/websearch/indexer.py` 한 파일 10줄이다** — `DROP` 앞의
`db.execute("BEGIN")` 한 줄과 `except KeyboardInterrupt` 한 갈래(rc **130** + 한 줄 안내).
리뷰·e2e 두 phase 는 제품 코드를 **0줄** 고쳤다.

## e2e phase 가 한 일 (2026-08-31)

- **`e2e/indexer_interrupt_e2e.py` 신규 — 19종째.** 문서 2,000개(각 약 4KB)를 임시 DB 에
  깔고 **진짜 SIGINT 를 진짜 CLI 프로세스**에 보낸다. 시나리오 6 + 측정 불능 가드, **6.8초**.
  재구축 중단(옛 2,000행·옛 정의 생존) · 증분 중단(색인·원본 무변경) · 재실행 복구 ·
  중단 뒤 질의(`결과 없음` 으로 침묵하지 않는다) · 대조군 · `--control`(rc 2).
- **신호 시점을 sleep 으로 안 잡는다.** 색인이 **쓰기 락을 잡은 것을 보고** 보낸다 —
  재구축은 `DROP TABLE docs`, 평소 갈래는 첫 `INSERT` 에서 락을 쥐므로 그때가 **되돌릴
  것이 있는 지점**이다. 창을 놓치면 초록이 아니라 측정 불능 2.
- **첫 판은 아무것도 안 재고 초록이었을 수 있다** — 문서가 작아 색인 창이 **0.1초**였다.
  본문을 실제 크롤 페이지 크기로 키워 창을 1초대로 만든 뒤에야 변이 표가 의미를 가졌다.
  **e2e 를 짜고 나서 창의 크기를 재보지 않으면 그 e2e 는 자기가 무엇을 재는지 모른다.**
- **변이 7종 중 6종이 여기서 죽는다.** M1(`BEGIN` 삭제)이 **옛 색인 0행**을, M7(행마다
  `commit`)이 **361행**을 실물로 재현한다 — 계획 3절 탐침 B 와 같은 숫자다. M2·M3(rc) ·
  M4(문구)도 죽는다. **M5(`except BaseException`)만 통과하고 같은 사본의 단위가 2건으로
  잡는다** — 계획 12-3 이 예고한 그대로다. 덮개는 e2e 단독이 아니라 **단위와 짝**이다.
- README 의 `e2e 시나리오` 숫자를 18 → **19** 로 같이 고쳤다. `tests/test_readme.py` 가
  `e2e/*.py` 개수를 직접 세므로 안 고치면 단위가 즉시 빨개진다(그 검사가 존재하는 이유).

## 검증 (전부 이번 반복에 직접 돌렸다)

- 단위 **456건 OK**(3.72초, rc 0) — `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m
  unittest discover tests`. e2e 앞의 전체 검증 선통과.
- **새 e2e** `PYTHONPATH=src python3 e2e/indexer_interrupt_e2e.py` rc **0**(6.8초) ·
  `--control` rc **2**(`바닥 색인이 0행이다(필요 2000)`).
- 계획 6절이 지정한 넷 전부 rc **0**: `indexer_e2e` 2.7s · `search_api_e2e` 15.0s ·
  `tokenizer_e2e` 5.8s · `pagination_ui_e2e` 11.8s.
- **린터·타입체커 없다**(`docs/project.md`) · CI 없다 — 검증은 위 줄들이 전부다.
- `data/crawl.db` sha256 `85c96744…5bda18` **무변경**(e2e 전후). e2e 는 전부 임시
  디렉터리에서 `cwd=<임시 디렉터리>` 로 돌렸다. 스크래치패드 사본은 `.git` 없이 만들었다.

## 남은 것 (다음 반복이 읽을 것)

- **보류 2건은 그대로 열려 있다**(계획서 12-2) — ① `commit()` 뒤 도착한 중단은 안내
  "색인은 바뀌지 않았다" 를 거짓으로 만든다 ② `--query` 도중 중단도 같은 색인 안내를 낸다.
  둘 다 사용자 표면이 바뀌어 자기 RED 가 필요하다. e2e 는 그 창을 안 만든다.
- **후보 1건** — `sqlite3.connect` timeout 불일치(`indexer.py:78·136·181` 5초 대
  `store.py:22` 30초). 이 diff 밖의 줄이고 악화도 아니라 후보로만 남긴다.
- **`digest.md` 232줄(상한 200) — 아직 미결.** 회전 전에 `index.md`·`plan_history_*.md`
  참조 확인이 선행이다(`digest [6]`). 이번 반복도 못 했다 — **두 반복째 밀린다.**

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마를 안 건드린다. 탐침·e2e 는 임시 디렉터리에서만.
- 기존 단언을 낮추지 않는다 — 특히 21 의 `NoCrawlDataError`·`StaleIndexError` 갈래.
- `except KeyboardInterrupt` 가 다른 예외를 같이 삼키면 RED(변이 M5 가 잰다).
- 색인 성능 10% 이상 회귀면 RED.
- 도메인당 요청 간격 1초 이상 · robots.txt 준수.
- 외부 네트워크 금지 · `docs/specs/` 읽기만 · `--no-verify` 금지 · `main` 직접 커밋 금지.
