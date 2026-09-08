---
signal: GREEN
phase: 테스트
step: 3/3
attempt: 0
iteration: 473
updated: 2026-09-08
ctx: 34
night_iterations: 5
night_red: 0
night_retries: 0
plan: recrawl
---

## 현재 상태

**계획 80 개발 3/3 완료 — 재방문·갱신·삭제 셋이 다 선다.** 전수 **702 OK**.
다음 반복은 **테스트 phase** — 새로 쓰는 곳이 아니라 **빠뜨린 것을 찾고 전체를 돌리는** 곳이다.

## 스텝 셋이 놓은 것

| | 자리 | 계약 |
|---|---|---|
| 재방문 | `store.is_fresh()` + `crawl.py` 팝 지점 | 2xx 30일 · 그 밖 15일, 시계는 SQLite |
| 갱신 | 워터마크 루프 | `DELETE`+`INSERT`. 마크가 있을 때만 |
| 삭제 | 워터마크 루프 | 404·410 → `docs` 만. `pages` 는 묘비 |

## 테스트 phase 가 볼 곳

- **e2e 스크립트 둘이 CLI 문구를 문자열로 문다** — `e2e/noindex_e2e.py`(`"1 문서 색인
  제외"`)·`e2e/tokenizer_e2e.py`(`"색인 제외" not in`). 부분 문자열이라 넓힌 문구에도
  맞을 텐데 **실제로 돌려서 확인한다**(카파시 4번).
- **`store.has` 의 남은 호출자**(`crawl.py` 리다이렉트 도착지)가 이 계획에서 안 바뀐 것을
  다시 확인한다 — 뜻이 다른 두 술어가 갈라선 채로 남았는지.
- **갱신·삭제가 `search`·`/passages` 경로와 만나는 자리** — 갱신이 `docs` 행을 갈아
  끼우므로 근거 문단(`indexer.passages`)이 옛 본문을 들고 있지 않은지.

## 알아 둘 것 둘

1. **statusLine 이 꺼져 있다** — `.context-state.json` 이 32분 낡아 컨텍스트·한도 축을
   못 읽는다. 정지 판단은 **반복 상한**에만 기댄다.
2. **`git checkout <파일>` 로 변이를 되돌리지 않는다** — 미커밋 구현이 한 번 날아갔다.
   되돌리기는 `cp` 백업, 변이 실행에는 `PYTHONDONTWRITEBYTECODE=1` 을 함께 건다.

전문: `docs/design_recrawl.md` · 스텝: `docs/plan_recrawl.md` 4절
