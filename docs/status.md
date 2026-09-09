---
signal: DONE
phase: 계획
step: 2/2
attempt: 0
iteration: 490
updated: 2026-09-09
ctx: 46
night_iterations: 1
night_red: 0
night_retries: 0
plan: backoff-429
---

## 아침 할 일 — 어제와 같은 둘. 탐색은 **두 밤 연속 막혀 있다**

1. **패치 적용 판단** — `docs/patches/userinfo-leak-refuse-credentials.patch`
   (382줄 · 구현 + 단위 + e2e · `git apply --check` 통과). 야간이 적용하지 않은
   이유는 「보안 관련 — 줄 수 무관 항상 보류」다. 적용하면 `urls.normalize` 가
   netloc 에 `@` 를 든 URL 에 `None` 을 준다(018 의 「보존」을 뒤집는다).
   되돌리려면 `normalize` 안의 조건 한 줄을 지운다.
2. **다음 계획을 사람이 하나 열어 주는 것.** 막힌 자리는 아래에 이름으로 있다.

## 반복 494 — 짧은 경로 `archive-backlog` (브랜치 `loop/archive-backlog`, `main` 미병합)

`docs.md` 4절(계획 완료 시 계획서를 `plan_history_<NNN>.md` 로)을 **재는 자가
0개였고 두 번 미끄러져 있었다.** 치우고(`design_recrawl.md`→066 ·
`plan_ethics-floor.md`→067) `archive_gap` 을 얹었다. 단위 709 → **715 OK**(rc 0).
자세한 것은 `index.md` 끝 줄과 `history_current.md` 반복 494.

**반복 번호를 486 → 494 로 고쳤다** — `3e19f28` 병합이 status·metrics 를
seed-tier1 쪽(486)에서 가져와 history 쪽(493)과 갈렸고, `IterationSyncTest` 는
**둘이 나란히 틀린 것은 못 잡는다.** digest `## 반복 실패` 에 등재했다.

## 탐색 결과(반복 494, 8순위 전수) — 어제와 같은 0

① 실패 테스트 0(**715 OK** rc=0) ② 린트·타입 도구 없음 ③ 코드 `TODO` 0
④ `candidates.md` 없음 ⑤ 보류는 `userinfo-leak` 패치 하나(보안·사람 판단)
⑥ **5점 이상 세 건을 직접 다시 열었고 셋 다 그대로 닫혀 있다** — `[7]` 갱신 경로
`DELETE` 선형(여는 조건 「코퍼스 만 단위」 · 오늘 118문서) · `[high]` 옛 열쇠 행
통합(**마이그레이션이라 야간 금지**) · `[7]` OFFSET 페이지네이션(공개 API
`?page=N` 을 커서로 바꾸는 건이라 사람이 정할 갈림길) ⑦ 반복 실패 — 둘 등재
⑧ `gh issue list` 0건.

**사양 축도 훑었다(1~8순위 밖 · 계획 43·77 전례).** 재는 자가 없는 컨셉 판정은
**성능 3(수집→검색 10분)** 과 **경량 2(RSS 2GB)** 둘인데, 전자는 구조적으로 이미
만족하고(`store.py:76` WAL + `upsert` 마다 커밋 · 증분 재실행 계획 78 실측 10만
환산 29.5초) **남은 것은 문서 공백이지 코드 공백이 아니다.** 후자는 100만 문서가
있어야 잰다. 둘 다 밤에 열 계획이 아니다.

## 한도

`digest.md` **213줄**(상한 200). 무인은 이 파일을 회전하지 않는다(계획 76 이 그은 선).
