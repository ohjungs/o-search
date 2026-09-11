---
signal: GREEN
phase: 테스트
step: 2/2
attempt: 0
plan: docs-delete-rowid
iteration: 548
updated: 2026-09-11
mode: night
night_iterations: 3
night_red: 0
night_retries: 0
night_self_amendments: 0
ctx: 85
note: 컨텍스트 85% 로 정상 종료 — 이어받으면 테스트 phase 부터
---

# 현재 상태

계획 **96 `docs-delete-rowid`** 개발 **2/2 완료** — 갱신 경로의 세 `DELETE FROM docs` 가
`WHERE url = ?`(FTS5 전수 스캔)에서 `WHERE rowid = ?` 로 바뀌었고, 그 값을 1천·1만·4만
문서에서 **두 열쇠 모두** 쟀다(`docs/e2e/docs-delete-rowid/result.md`).

| N | 옛 `url` | 새 `rowid` | 배수 |
|---|---|---|---|
| 1,000 | 0.164ms/건 | **0.012** | 14배 |
| 10,000 | 2.693 | **0.012** | 220배 |
| 40,000 | 11.950 | **0.014** | 881배 |

판정 ① 새 열쇠 4만/1천 **1.17배**(무관) · ② 옛 열쇠 **72.9배**(선형 재현). 둘 다 참.

**크롤이 아직 백그라운드에서 돌 수 있다**(`--max 30000` · 끝나면 색인까지 자동으로
이어지고 **그 색인이 이 코드를 쓴다**). 이어받기 전에 먼저 본다:

```bash
pgrep -f websearch.crawl   # 비었으면 끝난 것
python3 -c "import sqlite3;c=sqlite3.connect('file:data/crawl.db?mode=ro',uri=True);\
print(c.execute('select count(*) from pages').fetchone()[0])"
```

## 다음 행동

**테스트 phase** — 스텝이 둘 다 닫혔으니 새로 쓰는 곳이 아니라 **빠뜨린 것을 찾는**
곳이다(`test.md`). 이어서 리뷰(백지) → e2e. e2e 시나리오는 계획서에 적혀 있다:
실물 `data/crawl.db` **사본**에서 색인을 한 번 돌려 `docs` 행 수와 `GET /search` 응답이
변경 전과 같은지 본다 — **바꾼 것은 값이지 결과가 아니다**를 실물에서 확인한다.

## 설계

**생략** — 기존 함수의 질의 한 줄에 `d.rowid` 를 얹고 `WHERE` 열쇠를 바꿨다. 새 파일·공개
인터페이스·스키마 변경 없음 (`design.md` 1절 트리거 해당 없음).

## 규모 축 (2026-09-11)

색인 **10,461** · pages **37,704** · 1.37GB · 전수 **763 OK**. **병합은 손으로 조립하지
않는다** — `scripts/merge-to-main.sh` (전수가 초록일 때만 민다).

## 사람 결정 대기

- **`docs/patches/userinfo-leak-refuse-credentials.patch`** — URL 자격증명이 크롤·저장·렌더로
  새는 건. 구현·테스트까지 초록 확인 후 패치로 뽑아 뒀다. **보안 경계**라 적용 보류.
- **`~/.claude/settings.json`** 미커밋 — 내 변경이 아니고(`model: opus → opus[1m]` + `allow`
  자리 정렬 · 권한 상향 아님을 diff 로 확인) 코어층 가드가 막았다. 승인하면 `--no-verify`.
- **`~/.claude/hooks/ojeong-guard.cjs`** — `RUNNER` 가 `^python3` 로 앞머리를 고정해 **환경변수로
  시작하는 이 저장소의 정식 테스트 명령을 검증으로 한 번도 안 센다.** 고칠 내용은
  `~/.claude/hooks/guard.test.js` 가 명세한다. 분류기가 그 파일 쓰기를 막아 내가 못 고친다 —
  나를 제약하는 가드를 내가 푸는 것은 권한 상향이라 우회하지 않는다.

## 정지 사유

**컨텍스트 85% 이상** (`.context-state.json` 실측 85 · 경계값은 정지 쪽). 실패가 아니다 —
스텝 경계에서 끊었고 기록·보고서를 남겼다. 이어서 하려면 같은 명령을 다시 부른다.
(`docs/digest.md` 208줄 — 상한 200 초과. 다음 짧은 경로 후보다)
