---
signal: YELLOW
phase: 계획
step: 0/0
attempt: 0
plan: null
iteration: 558
updated: 2026-09-13
mode: night
night_iterations: 1
night_red: 0
night_retries: 0
night_self_amendments: 0
ctx: 측정 불가 — 공유 파일의 87% 는 **내 세션 것이 아니다**(게이트 ⑦). 반복 상한에만
  의존했고, 탐색 0건이라 어느 쪽으로 읽어도 정지다
note: 일곱 번째 빈손. 잰 것 둘 — ①필수 읽기가 **721줄**로 제 상한 600 을 넘겨 있었다.
  status.md 의 history 중복을 접고(183→80) 밀린 회전을 돌려(307→119) **448줄**로 내렸다
  ②`.context-state.json` 세션 경합을 **다른 날 두 번째로** 재현. 승인 게이트 **7건**(⑥ digest 가 오늘 회전으로 한 줄 나빠졌다)
---

# 현재 상태

계획 **96 `docs-delete-rowid` 완료** — 아카이브·병합까지 끝났다(`plan_history_071.md` ·
`index.md` · `04161b3` · e2e 상세 `docs/e2e/docs-delete-rowid/result.md` 5절).

**탐색이 빈손이라 YELLOW 로 멈췄다 — 일곱 세션 연속 0건**이다(552~555 는 여덟 출처를 네 번 따로 전수, 556~558 은 아래 핀).

## 빈손 대조 핀 — 여덟 출처를 다시 안 재도 되는 조건

기준 트리는 **`1f37284`** (그때 잰 것: 763 OK · `TODO` 0 · `candidates.md` 없음 · 이슈 0 ·
패치는 `userinfo-leak` 하나 · 활성 `plan_*.md` 은 보류분 하나). 1~7순위는 **트리의 함수**라
트리가 같으면 결과가 같다. **8순위(이슈)만 트리 밖이라 둘째 줄을 «항상» 돌린다.**

```bash
git diff --stat 1f37284..HEAD -- src tests e2e scripts docs/digest.md docs/candidates.md docs/specs
gh issue list --state open --limit 20     # 트리 밖 — 항상 돌린다
```

둘 다 비면 전수를 다시 안 돌린다. **단, 핀은 «코드»의 함수지 «환경»의 함수가 아니다** —
파이썬·OS 가 움직이면 같은 트리가 다른 결과를 낸다. 558 이 그 구멍을 쟀다:
**763 OK**(18.6s · Python 3.9.6) — 싸니 밤마다 돌린다.

## 사람 결정 대기 — 하나를 열어야 이어진다

근거·재현·처방은 갖춰졌고 막는 것은 판단뿐이다. 밤에 새로 막힌 것은 **여기 먼저 적는다**
(야간 보고서가 이 절을 그대로 퍼 간다).

- **① 동시 색인이 만드는 중복 `docs` 행** — 반복 550 리뷰 보류. 고치는 자리는 `index_pages`
  의 트랜잭션 경계(`BEGIN IMMEDIATE`)이고 재구축 갈래의 `BEGIN`(`indexer.py:217`)과 중첩을
  함께 풀어야 한다. **자기 계획 크기**이고 레이스 컨디션이라 밤이 안 연다. 승인하면 바로 계획.
- **② `perf_crawl.py` 기준선 여유 0.5%**(digest 후보 8점) — ①재기준선 ②[열림] 대비 비율
  ③참고용 강등 **셋 중 택1**. 밤이 못 고르는 이유는 셋 다 「통과시키려고 시나리오를 낮추는
  것」과 겉모양이 같아서다.
- **③ `docs/patches/userinfo-leak-refuse-credentials.patch`** — URL 자격증명이 크롤·저장·렌더로
  새는 건. 적용 상태에서 초록 확인 후 뽑아 뒀다. **보안 경계**라 밤이 영구히 못 연다.
- **④ `~/.claude/settings.json` 미커밋** — 내 변경이 아니고(`model: opus → opus[1m]` + `allow`
  자리 정렬 · 권한 상향 아님을 diff 로 확인) 코어층 가드가 막았다. 승인하면 `--no-verify`.
- **⑤ `~/.claude/hooks/ojeong-guard.cjs`** — `RUNNER` 가 `^python3` 로 앞머리를 고정해 **환경변수로
  시작하는 이 저장소의 정식 테스트 명령을 검증으로 한 번도 안 센다.** 고칠 내용은
  `~/.claude/hooks/guard.test.js` 가 명세한다. 분류기가 그 파일 쓰기를 막아 내가 못 고친다 —
  나를 제약하는 가드를 내가 푸는 것은 권한 상향이라 우회하지 않는다.
- **⑥ `docs/digest.md` 211줄**(상한 200) — 558 회전이 한 줄 더했다. 줄이려면 완료 항목을
  **지워야** 하는데 2026-09-07 의 삭제 위임은 그 건 한 번이었다. 밤이 안 연다.
- **⑦ 정지 조건이 `session_id` 를 안 본다** (557 최초 실측 · **558 이 다른 날 재현**) —
  `~/.claude/.context-state.json` 은 **모든 세션이 공유하는 파일 하나**고 statusLine 이 매 렌더
  덮어쓴다. 신선도 검사는 `updated_unix` 만 보고 누가 썼는지를 안 본다. 09-13 10:17 에도 홈
  디렉터리 세션(`402da0af…`)이 22초 전에 쓴 87% 를 읽었고, 내 세션이 자라는 동안 그 값은
  **87→83 으로 내려갔다**. **오염은 정지 조건에만 있지 않다** — `metrics.jsonl` 최근 6줄 중
  5줄이 남의 값이다(09-12 네 줄은 `ctx_at` 까지 동일). **위험한 쪽은 반대 방향이다** — 내가
  90%인데 남이 20%로 덮으면 정지선을 안 밟는다. 처방 한 줄: 읽은 `session_id` 가 내 것이
  아니면 **statusLine 이 꺼진 경우와 똑같이** 취급(반복 상한에만 의존). 고칠 자리가 SKILL.md
  의 «나를 멈추는 룰»이라 밤이 안 연다 — ⑤ 와 같은 이유다.

병합은 손으로 조립하지 않는다 — `scripts/merge-to-main.sh` (전수가 초록일 때만 민다).

## 규모 축 (2026-09-13)

`pages` **52,172** · `docs` **40,347** · 2.48GB · 전수 **763 OK**.
필수 읽기 **448줄**/600 (`project.md` 249 + `status.md` 80 + `history_current.md` 119) —
회전분은 `history_083.md`(반복 532~551). `project.md` 는 제 예산 60 의 4배지만 「거의 안 바뀌는 사실」이라 안 건드렸다.
