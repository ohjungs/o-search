---
signal: GREEN
phase: 개발
step: 1
attempt: 0
iteration: 183
updated: 2026-08-31
ctx: 66
night_iterations: 56
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 37 `indexer-interrupt` 개발 스텝 1 완료** — 계획서 `docs/plan_indexer-interrupt.md`,
브랜치 `loop/indexer-interrupt`(`loop/signal-budget-cover` `a8ad633` 에서 팠다).
설계 생략(계획서 8절). **재구축이 한 트랜잭션이 됐다** — `indexer.py:88` `DROP` 앞
`db.execute("BEGIN")` 한 줄. 탐침 B 재실측: 재구축 중 SIGINT 에 `docs` **6000행 유지**·
옛 정의 유지(고치기 전 6000→0). **다음은 개발 스텝 2**(`main` 의 `except KeyboardInterrupt`
→ rc 130). 계획 36 까지 전부 DONE. **`main` 병합은 사람이 정한다.**

## 이번 계획이 여는 것

**색인 도중 Ctrl-C 가 색인을 지운다.** `index_pages()` 는 스키마가 드리프트하면
`DROP TABLE docs` → `CREATE` → 전건 `INSERT` → `commit` 으로 재구축하는데,
**Python 3.9.6 `sqlite3` 은 DDL 을 암묵 트랜잭션에 안 넣는다** — DROP/CREATE 는 그 자리에서
커밋되고 INSERT 만 롤백된다. 그래서 재구축 중 SIGINT 는 **옛 6000행을 지우고 0행을 남긴다.**
그때부터 검색은 전부 `결과 없음` 이고, 이는 크롤 데이터가 없는 것과 **구별되지 않는다**
(21·26·29 가 세 번 닫은 실패 모양).

곁들여 **`indexer.main` 만 중단 계약이 없다** — `crawl` 은 rc 130(34·35·36), `serve` 는
rc 0, `indexer` 만 트레이스백 + rc -2 다. `digest ## 반복 실패` 의 "CLI 가 트레이스백을
낸다"(2회)의 **세 번째 자리**이고, 계획 21 이 이 함수에 세운 관용구를 중단 경로만 안 따른다.

## 착수 탐침 실측 (2026-08-31 · 전부 임시 디렉터리)

- **A 정상 색인 중 SIGINT**: rc **-2** · stdout 빈 문자열 · `KeyboardInterrupt` 트레이스백
  (`extract.py:60` 프레임까지) · DB `pages 6000 / docs 0 / integrity ok`(색인 무변경).
- **B 재구축 중 SIGINT**: rc **-2** · `docs` **6000행 → 0행** · 새 정의는 커밋된 채로 남는다.
- **뿌리**: 맨 `sqlite3`(3.9.6)에서 `DROP`+`CREATE` 뒤 commit 없이 close → **안 되돌아간다.**
- 전건 색인 기준선 **6000문서 4.58초**(성능 회귀 판정용).

## 오늘의 검증이 이 변화를 재는가 — 못 잰다

단위 452건 중 `indexer` 중단 단언 **0건** · e2e 18종에도 없다(중단 e2e 둘은 `crawl` 쪽) ·
스키마 재구축 단언은 있으나 **중단된 재구축**은 없다.

## 다음 스텝 (계획서 5절)

1. **재구축을 한 트랜잭션으로** — `indexer.py:88-90` 의 `DROP` 앞에 `db.execute("BEGIN")`.
   RED 는 `extract.extract_text` 가 `KeyboardInterrupt` 를 던지게 만든다.
2. **`main` 이 중단을 관용구로** — `indexer.py:236-249` 옆에 `except KeyboardInterrupt`,
   rc **130** + 안내 한 줄. 스텝 1 뒤라야 "색인은 바뀌지 않았다" 가 참이다.

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
