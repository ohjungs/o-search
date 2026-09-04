---
signal: DONE
phase: e2e
step: 1/1
attempt: 0
iteration: 326
updated: 2026-09-05
ctx: 58
night_iterations: 148
night_red: 2
night_retries: 0
plan: db-state-invariant # 계획 55 — e2e 1/1 통과 · 완료 기준 9/9 · 새 e2e 0개 · DONE
---

# 현재 상태

**계획 55 `db-state-invariant` 가 끝났다.** 결과는 `docs/e2e/db-state-invariant/result.md`,
설계서는 `docs/design_db-state-invariant.md`, 계획서는 `docs/plan_db-state-invariant.md`,
브랜치는 `loop/db-state-invariant`.

## e2e 가 잰 것 — **앞 반복의 숫자를 하나도 그대로 안 받았다**

`status.md` 가 「rc 0 확인됨」으로 적어 둔 것까지 전부 다시 돌렸고, 앞 phase 들이 단위
실패 건수로만 재고 넘긴 완료 기준 3·4·5·6 도 **저장소 밖 전체 사본에서 다시 심어 다시
쟀다**(`rsync` · `.git` 없는 트리 · `git checkout` 0회).

**① 자의 눈금이 스키마를 따라 저절로 큰다** — `store.SCHEMA` 에 `title TEXT` 한 줄을 더한
사본에서 자가 도는 눈금이 `url·html·status·fetched_at` **4칸 → 5칸**이 됐다. **테스트
파일은 한 글자도 안 고쳤다.** 눈금을 0칸으로 눈멀게 하면 조용한 초록이 아니라
`0 not greater than or equal to 4` 로 죽는다(기준 4).

**② 변이 둘 다 RED — 그런데 폭이 다르다(새로 안 것).**

| 변이 | rc | 죽은 subTest |
|---|---|---|
| ① 탐침에서 `url,` 삭제 | 1 | `missing='url'` **1건** |
| ② 탐침을 `hits` 루프 **안**으로 | 1 | `missing='url'` · `missing='html'` **2건** |

계획 54 e2e 는 이 둘을 «HTTP 표면에서 동치» 로 적었는데 그 측정은 `html` **한 축**만 봤기
때문이다. 열 축 전체를 도는 자로 재니 ②는 **계획 54 가 닫은 자리까지 함께 되돌린다**.
자리를 하나 더 넓히는 안이었다면 그 회귀를 아무도 못 봤다 — **자를 세운 값이 여기 있다.**

**③ 실서버 두 대 · `url` 열 없는 DB**

| DB 상태 | `/passages` 세 질의 | `/search` 세 질의 | 화면 |
|---|---|---|---|
| 정상 (대조군) | 200 · 200 · 200 | 200 · 200 · 200 | 200 |
| **`url` 열 없음** | **500 · 500 · 500** (착수 500/200/200) | **200 · 200 · 200** | **200** |

**정상 대조군 7칸 무변**이라 계획서 8절의 최대 위험(가드 오탐)은 **0**. `/search` 가 200 인
것은 정상이다 — FTS `docs` 는 `content=` 없는 독립 표라 `pages` 를 안 읽는다.
**CSO 통과** — 500 본문에 `sqlite`·`OperationalError`·`no column`·DB 경로 **0건**, 원인은
서버 stderr 에만(`/passages 실패: OperationalError('no such column: url')`).

## 완료 기준 — **9/9 통과** (뒤집힌 행 0개)

## 전수

**단위 605 OK**(13.526초 · 맨몸·단독 · rc 0) · **e2e 21종 전수 rc 0 · 새 e2e 파일 0개**(근거
넷은 result.md 4절 — 결정적인 것은 «손으로 적는 e2e 는 스키마를 따라 안 커서, 이 계획이
없애러 온 취약성을 e2e 디렉터리에 새로 만든다») · 21종 합계 약 171초, 오래 걸리는 넷은
전부 실시계를 일부러 기다리는 것들이다(`perf_crawl` 28s · `deadline` 19s · `interrupt` 18s ·
`retry_interval` 15s) · `passage_eval` 정확도 **100.0%**(398/398) · 채택률 99.5% ·
p95 1.65ms(예산의 0.3%) · `quality_eval` ko 20/20 · en 19/20 · `perf_search` p95 8.81ms ·
`perf_crawl` 10.24/s · `design_check` 4축 — **기준선 전 축 무변**.

## 한도

`src/` **0줄**(e2e phase) · 제품 diff 는 계획 전체로도 `indexer.py` 한 파일 ·
`data/crawl.db` sha256 `85c96744…5bda18` 무변(열지도 않았다) · `docs/specs/` 무변 ·
새 의존성 0 · 스키마·마이그레이션·재색인 0 · `pgrep -f websearch.serve` **0건** ·
`--no-verify`·`--force` 0 · `main` 직접 커밋 0 · **PR 무접촉(조회 0회)** · 러너 규율 위반 0.

**푸시 대조** — 아래 「푸시」 절에 실측을 적는다.

## 사람 결정 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 아무도 안 그려 본다.
4. **브랜치 병합** — 원격 `main` 은 `c0be72f`, 계획 54(PR #9)까지 들어 있다.
   `loop/db-state-invariant` 병합은 사람 몫이고 `main` 직접 커밋은 않는다.

## 정지 사유

없음 — 계획 55 DONE. 다음 반복은 **계획 탐색**이다(아카이브·회전은 이 반복이 안 했다).
