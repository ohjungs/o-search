---
signal: GREEN
phase: 테스트
step: 1
attempt: 0
iteration: 184
updated: 2026-08-31
ctx: 69
night_iterations: 57
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 37 `indexer-interrupt` 개발 끝(스텝 1·2 완료)** — 계획서 `docs/plan_indexer-interrupt.md`,
브랜치 `loop/indexer-interrupt`(`loop/signal-budget-cover` `a8ad633` 에서 팠다).
설계 생략(계획서 8절). **재구축이 한 트랜잭션이 됐고**(`indexer.py:92` `DROP` 앞
`db.execute("BEGIN")`) **`main` 이 중단을 관용구로 받는다**(`indexer.py:255` `except
KeyboardInterrupt` → `중단 — 색인은 바뀌지 않았다` · rc **130**). 탐침 재실측: A 는
`pages 6000 / docs 0 / integrity ok`, B 는 `docs` **6000행·옛 정의 유지**(고치기 전 6000→0),
**둘 다 rc 130 · Traceback 0회 · stderr 한 줄**. 완료 기준 7개 전부 대조 통과.
**다음은 테스트 phase.** 계획 36 까지 전부 DONE. **`main` 병합은 사람이 정한다.**

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

## 다음 스텝 (계획서 5절 — 개발 두 스텝 다 끝났다)

1. ~~재구축을 한 트랜잭션으로~~ **완료**(`indexer.py:92`). 단언
   `TestSchemaDrift.test_interrupted_rebuild_leaves_the_old_index_intact`.
2. ~~`main` 이 중단을 관용구로~~ **완료**(`indexer.py:255`). 단언 둘 —
   `TestCli.test_interrupt_is_a_one_line_message_and_rc_130` 과 대조군
   `test_interrupt_branch_does_not_swallow_other_base_exceptions`(M5 를 잰다).

→ **다음은 테스트 phase.** 개발이 남긴 것은 단위 단언 3건뿐이고 중단 e2e 는 아직
`crawl` 쪽 둘뿐이다 — `indexer` 중단을 실제 CLI+SIGINT 로 지나는 e2e 가 있는지가 다음 판정이다.

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
