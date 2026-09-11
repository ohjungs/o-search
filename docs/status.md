---
signal: GREEN
phase: 계획
step: 0/0
attempt: 0
plan: null
iteration: 551
updated: 2026-09-12
mode: night
night_iterations: 3
night_red: 0
night_retries: 0
night_self_amendments: 0
ctx: 미상 (.context-state.json 오래됨 — statusLine 꺼짐, 반복 상한에만 의존)
note: e2e 통과 — 실물 A/B 결과 바이트 동일 · 17초 대 187초. 합성 눈금이 11.5배 낙관이었다
---

# 현재 상태

계획 **96 `docs-delete-rowid`** **완료**. 갱신 경로의 세 `DELETE FROM docs` 가
`WHERE url = ?`(FTS5 전수 스캔)에서 `WHERE rowid = ?` 로 바뀌었고, 스텝 1(단위·변이)·
스텝 2(합성 규모)·e2e(실물 A/B)가 전부 초록이다.

## e2e phase (2026-09-12 · 반복 551)

실물 `data/crawl.db` **사본 두 벌**에 새 팔(HEAD)과 옛 팔(`main:src/websearch` 통째,
`/tmp/oldsrc`)을 **순차로** 돌렸다. 원본은 안 건드렸다.

**워터마크를 되돌려야 갱신 경로가 보였다** — 실물의 `recheck_watermark` 가
`max(pages.fetched_at)` 과 같아(크롤 직후 색인이 돌았다) 갱신 루프가 볼 쌍이 **1건**이었다.
양쪽 사본에 똑같이 `2026-09-11 14:53:00` 으로 되돌려 **1,225쌍**을 만들었다(코퍼스 4만 그대로).

| | 새 `rowid` | 옛 `url` |
|---|---|---|
| `docs` 행 | 40,317 | 40,317 |
| 404 된 URL 잔존 · 중복 URL | 0 · 0 | 0 · 0 |
| 새 본문 히트 | 200 | 200 |
| `GET /search` 16응답 | **바이트 동일** | |
| 벽시계 | **16.79s** | 187.05s |

**1판만으론 부족했다** — 워터마크만 되돌린 실행은 같은 HTML 을 다시 처리하는 것이라
「새 본문이 나온다 · 404 가 사라진다」를 안 건드린다. 2판에서 양쪽에 똑같이 200건 본문
교체 · 30건 `status=404` 를 심어 그 둘을 실제로 밟았다.

**합성 표의 눈금이 11.5배 낙관이었다** — 4만 행 삭제 1건이 11.95ms(합성) 대 **137ms**(실물).
원인은 평균 본문 **960자 대 16,210자**(16.9배)다. 스텝 2 의 3절이 「절대값은 이 입력에서의
눈금」이라 적어 둔 천장이 수치로 맞았다 — **모양(상수 대 선형)은 맞았고 눈금만 낙관**이었다.

전부 `docs/e2e/docs-delete-rowid/result.md` 5절.

## 다음 행동

**아카이브 완료** — 계획서는 `plan_history_071.md` · `index.md` 에 한 줄. 다음은 **새 계획
탐색**(`discover.md`)이다. 병합은 **손으로 조립하지 않는다** — `scripts/merge-to-main.sh`
(전수가 초록일 때만 민다).

## 규모 축 (2026-09-12)

`pages` **52,172** · `docs` **40,347** · 2.48GB · 전수 **763 OK**.

## 사람 결정 대기

- **동시 색인이 만드는 중복 `docs` 행** — 반복 550 리뷰 보류 건. 고치는 자리는 `index_pages`
  의 트랜잭션 경계(`BEGIN IMMEDIATE`)이고 재구축 갈래의 `BEGIN`(`indexer.py:217`)과
  중첩을 함께 풀어야 한다. **자기 계획 크기**이고 레이스 컨디션이라 야간이 안 연다.
  (이번 e2e 는 중복 0인 코퍼스에서만 쟀다 — 그 갈림을 재지 않았다.)
- **`docs/patches/userinfo-leak-refuse-credentials.patch`** — URL 자격증명이 크롤·저장·렌더로
  새는 건. 구현·테스트까지 초록 확인 후 패치로 뽑아 뒀다. **보안 경계**라 적용 보류.
- **`~/.claude/settings.json`** 미커밋 — 내 변경이 아니고(`model: opus → opus[1m]` + `allow`
  자리 정렬 · 권한 상향 아님을 diff 로 확인) 코어층 가드가 막았다. 승인하면 `--no-verify`.
- **`~/.claude/hooks/ojeong-guard.cjs`** — `RUNNER` 가 `^python3` 로 앞머리를 고정해 **환경변수로
  시작하는 이 저장소의 정식 테스트 명령을 검증으로 한 번도 안 센다.** 고칠 내용은
  `~/.claude/hooks/guard.test.js` 가 명세한다. 분류기가 그 파일 쓰기를 막아 내가 못 고친다 —
  나를 제약하는 가드를 내가 푸는 것은 권한 상향이라 우회하지 않는다.
- **`docs/digest.md` 210줄** — 상한 200 초과. 줄이려면 완료 항목을 **지워야** 하는데
  2026-09-07 의 삭제 위임은 그 건 한 번이었다. 야간이 안 연다.
