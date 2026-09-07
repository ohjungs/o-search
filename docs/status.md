---
signal: YELLOW
phase: 계획
step: 0/0
attempt: 0
iteration: 414
updated: 2026-09-07
ctx: 72
night_iterations: 6
night_red: 0
night_retries: 0
plan: null
---

## 현재 상태

**계획 71 `index-e2e-verdict` 는 DONE 으로 닫혔고(반복 413), 다음 계획 탐색이 근거 0 이다.**
`rules/discover.md` 2절 — **근거를 못 찾으면 계획을 만들지 않는다.** 무인 모드라 질문하지
않고 **보류로 두고 정지**한다. 밤에 만들어도 되는 셋(깨진 것 · 코드의 TODO · 근거 있는
후보) 어디에도 오늘 열 수 있는 것이 없다.

## 탐색 결과 — 8개 출처 전부 확인 (`rules/discover.md` 1절)

| 순위 | 출처 | 실측 | 결과 |
|---|---|---|---|
| 1 | 실패하는 테스트 | 전수 `Ran 647` `OK` rc 0 · e2e 21/21 rc 0 | **0건** |
| 2 | 타입·린트 에러 | `project.md` — 수단 **없음**(stdlib 소규모) | 해당 없음 |
| 3 | 코드의 `TODO`/`FIXME`/`HACK` | `src/`·`e2e/`·`tests/` grep → 1건이지만 **fixture 문자열**(`tests/test_indexer.py:779` 의 HTML 입력) | **0건** |
| 4 | `docs/candidates.md` 큐 | 파일 **부재**(이 저장소는 014 자율발전 미적용) | 해당 없음 |
| 5 | `digest.md` 보류(승인 대기) | 항목 **0**(주석 예시뿐) | **0건** |
| 6 | `digest.md` 다음 계획 후보 | 열린 항목은 있으나 **전부 여는 조건 미도래**(아래) | **0건** |
| 7 | `digest.md` 반복 실패 | 남은 1건은 **룰 문장으로 닫힌 절차 항목**(리뷰 예산 — 정적 판독으로 닫는다) | **0건** |
| 8 | 이슈 | `gh issue list` → **빈손** | **0건** |

**6순위를 안 여는 이유는 후보가 없어서가 아니라 후보마다 조건이 적혀 있어서다.** 표본:

- `[9]` `/passages` 총 p95 는 `/search` 몫 — 여는 조건 «실물 분포가 먼저»(실물 1.39ms)
- `[7]` `robots.allowed()` 비ASCII 예외 — **지금은 도달 불가**, 여는 조건 «`robots.py` 직접 호출처가 생기는 날»
- `[7]` 페이지네이션 커서 — 게이트는 열렸지만 **공개 API 를 바꾸는 갈림길이라 사람 몫**
- `[6]` `index.md` 헤더 다섯째 이름([R71-3]) — 여는 조건 «표에 열을 실제로 더하는 날»
- `[5]` `_IMPLIED_END` 잔존 변이 101 — 여는 조건 «표를 손으로 고치는 계획이 열릴 때»
- `[5]` 예산 `500` 리터럴 둘 — 여는 조건 «사양 성능 4·5 의 숫자가 처음 움직이는 날»
- `[8]` 숨은 텍스트가 근거 문단으로 — **이미 닫혔다**(계획 51 `hidden-passage`)

여는 조건이 안 찬 후보를 여는 것은 **오늘 없는 사고를 위해 자를 세우는 것**이고,
`rules/discover.md` 3절이 밤에 금지한 「근거가 측정값이 아닌 개선」과 같은 자리다.

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
Ran 647 tests in 16.017s · OK · rc 0
```

`src/`·`e2e/` **0줄** · `docs/specs/` 무접촉 · `data/crawl.db` **무개봉** · 바깥 네트워크 0 ·
`main` 직접 커밋 0 · 브랜치 `loop/index-e2e-verdict`(병합 안 함 — `rules/git.md` 1절).

## 사람이 정할 것 (야간 보고서 `docs/reports/night_2026-09-07.md` 에 올렸다)

1. **`digest.md` 216줄 — 상한 200 초과.** 지울 수 있는 완료 항목이 여덟 줄뿐이라 산술이
   안 맞고, **무인 모드는 파일·데이터를 삭제하지 않는다**. 무엇을 버릴지가 사람 몫이다.
2. **다음 계획의 방향.** 후보 풀이 「조건이 안 찬 것」으로만 남았다 — 방향을 주려면
   `docs/specs/concept.md` 에 적거나 `digest.md` 「다음 계획 후보」에 한 줄 넣으면 된다.
3. **`loop/index-e2e-verdict` 병합 여부** — 계획 71 은 DONE 이고 병합은 사람 몫이다.
