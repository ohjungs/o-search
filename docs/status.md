---
signal: GREEN
mode: night
plan: docs-delete-rowid
phase: 개발
step: 1/2
attempt: 0
note: 스텝 2 — 규모에서 값 측정
iteration: 547
night_iterations: 2
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-09-11
ctx: 26
---

# 현재 상태

계획 **96 `docs-delete-rowid`** 착수 — 계획서 `docs/plan_docs-delete-rowid.md`.
갱신 경로의 `DELETE FROM docs WHERE url = ?`(`src/websearch/indexer.py:285·292·300`)가
FTS5 전수 스캔이라 코퍼스 크기에 선형이다. 워터마크 조인이 이미 그 행을 들고 있으므로
`d.rowid` 를 얹어 열쇠만 바꾼다. **근거는 digest 후보 `[7]` 이 스스로 적어 둔 여는 조건
「코퍼스가 만 단위로 올라가는 날」이 오늘 열린 것**이다 — `docs` **10,461행** 실측.

**크롤이 백그라운드에서 돌고 있다**(`--max 30000` · `--deadline 10800` · 끝나면 색인까지
자동으로 이어진다). **그 자동 색인이 내 코드를 쓴다** — 스텝 1 은 전수가 초록일 때만 남긴다.

```bash
python3 -c "import sqlite3;c=sqlite3.connect('file:data/crawl.db?mode=ro',uri=True);\
print(c.execute('select count(*) from pages').fetchone()[0])"
pgrep -f websearch.crawl   # 비었으면 끝난 것
```

## 다음 행동

**스텝 1 완료** — 세 `DELETE` 가 전부 `WHERE rowid = ?` 다(`git grep "DELETE FROM docs WHERE url"`
가 `src/` 에서 0건). 전수 **763 OK**(새 테스트 1건 · README 건수도 763 으로 맞췄다).
스텝 2 — 1천·1만·4만 문서 임시 DB 에서 갱신 1건당 `DELETE` 값을 옛/새 열쇠로 **둘 다** 재서
`docs/e2e/docs-delete-rowid/result.md` 에 남긴다(음성 대조가 없으면 「원래 빠른 기계」와 못 가른다).
측정 스크립트는 `/tmp` 에서 돌리고 커밋하지 않는다. 완료 기준 전문은 계획서 스텝 2.

## 설계

**생략** — 기존 함수의 질의 한 줄에 `d.rowid` 를 얹고 `WHERE` 열쇠를 바꾼다. 새 파일·공개
인터페이스·스키마 변경 없음, 처방과 값이 후보 `[7]` 과 `indexer.py:239` 주석에 이미 실측으로
박혀 있어 대안이 갈리지 않는다 (`design.md` 1절 트리거 해당 없음).

## 규모 축 (2026-09-11)

색인 **10,461** · pages **37,704** · 1.37GB · 전수 **762 OK**. 저장·색인 고정비·처리량·재개·
질의 다섯 축은 계획 77·78·82·83·85·88·91·92·95 가 전부 열었다 — **남은 것은 크롤 시간뿐이다.**
**병합은 손으로 조립하지 않는다** — `scripts/merge-to-main.sh` (전수가 초록일 때만 민다).

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

없음. (`docs/digest.md` 208줄 — 상한 200 초과. 다음 짧은 경로 후보다)
