---
signal: GREEN
phase: 리뷰
step: 3/3
attempt: 0
iteration: 474
updated: 2026-09-08
ctx: 34
night_iterations: 6
night_red: 0
night_retries: 0
plan: recrawl
---

## 현재 상태

**계획 80 테스트 완료 — 지목한 셋을 실행으로 확인하고 갭 둘을 닫았다.** 전수 **704 OK**.
다음 반복은 **리뷰 phase** — 스텝 셋의 diff 를 그대로 머지해도 되는지 본다.

## 테스트가 확인한 것

| 확인 | 방법 | 결과 |
|---|---|---|
| e2e 둘의 CLI 문구 단언 | 실제로 돌렸다 | 둘 다 통과 — 넓힌 문구가 부분 문자열에 맞는다 |
| `store.has` 남은 호출자 | 탐침 3회 | 무변. 리다이렉트 **출발지**는 `pages` 에 안 남아 매번 나간다 (`has` 시절과 같다) |
| 갱신 × 근거 문단 | 새 테스트 | `passages` 가 새 문단만 낸다 |
| 갱신 도중 중단 | 새 테스트 | `DELETE`+`INSERT` 가 함께 되돌아가 문서를 안 잃는다 |

## 리뷰 phase 가 볼 곳

- **`mark` 를 세 번 묻는다** — 삭제 갈래(`mark and status in _GONE`)와 갱신 갈래(`elif mark`)와
  `sql` 조립. 셋의 이유가 각각 다른데(전수일 때 삭제하면 옛 DB 가 통째로 흔들린다 / 전수
  재추출은 39.7분 / 집합 정의) **한 이름이 세 뜻을 진다**. 합칠 것인지 이름을 가를 것인지 본다.
- **`removed = before + indexed - after` 가 이제 세 원인을 한 숫자로 낸다** — noindex·404·
  (갱신은 상쇄). 설계 계약 5 가 반환 계약을 안 바꾼다고 못박았으니 **문구가 그 부담을 진다**.
- **`FRESH_DAYS`/`RETRY_DAYS` 가 CLI 로 안 열린다** — 계획이 정한 것이지만, 되돌리기가
  「상수를 크게」인 설계 근거와 실제 조작 수단이 맞는지 본다.

## 알아 둘 것 둘

1. **statusLine 이 꺼져 있다** — `.context-state.json` 이 낡아 컨텍스트·한도 축을
   못 읽는다. 정지 판단은 **반복 상한**에만 기댄다.
2. **`git checkout <파일>` 로 변이를 되돌리지 않는다** — 미커밋 구현이 한 번 날아갔다.
   되돌리기는 `cp` 백업, 변이 실행에는 `PYTHONDONTWRITEBYTECODE=1` 을 함께 건다.

전문: `docs/design_recrawl.md` · 스텝: `docs/plan_recrawl.md` 4절
