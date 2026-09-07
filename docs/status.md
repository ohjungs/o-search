---
signal: GREEN
phase: 테스트
step: 1/1
attempt: 0
iteration: 410
updated: 2026-09-07
ctx: 72
night_iterations: 2
night_red: 0
night_retries: 0
plan: index-e2e-verdict
---

## 현재 상태

**계획 71 스텝 1/1 개발 완료 — 색인표 다섯째 칸을 재는 자가 섰고 오늘의 위반 1건을 고쳤다.**
전수 **647 OK**(639 + 새 검사 8). 다음 반복은 **테스트 phase** — 계획서 4절의 M3~M6.

## 이번 phase 가 산 것

**빨간 것을 먼저 눈으로 봤다** (`rules/dev.md` 0절). 검사만 심은 상태에서 전수를 돌리니
`VerdictSyncTest` 가 **실물 `docs/index.md` 에서 슬러그를 이름으로 대고** 실패했다:

```
FAIL: test_done_rows_carry_a_verdict (test_docs.VerdictSyncTest)
e2e 칸에 판정이 아니라 날짜가 있다 — index.md `plan_noindex-entity-prefilter` 의
다섯째 칸이 `2026-09-07` 다. 판정은 docs/e2e/<슬러그>/result.md 에 있다
```

**M1(구멍)·M2(처방)·M0(대조군)을 이 반복에서 직접 밟았다.** M4(오탐 축)도 같이 샀다 —
`없음(…)`·`**새 e2e 0개**(…)` 여섯 행이 그대로 있는데 성한 트리가 조용하다. 어휘를
요구하지 않는다는 것이 실물로 증명된 자리다.

**심은 것 넷** (`tests/test_docs.py`, 기존 `step_gap`·`iter_gap`·`strike_gap` 관용구 그대로):

- 상수 `VERDICT_ROW`(다섯째 칸) · `VERDICT_ROW_HEAD`(행 머리) · `VERDICT_DATE` · 하한 못 `VERDICT_ROW_FLOOR = 45`
- 순수 함수 `verdict_gap(index_text)` — 완료 행만 보고, 어긋난 자리를 한 줄로 돌려준다
- `VerdictSyncTest` — 실물 위에서 `None` 인가 + 추출기 하한 못
- `VerdictGapTest` — 합성 표로 갈래 6개(진탐 · 판정 정상 · **오탐 축 4꼴** · 판정 안의 날짜 ·
  진행 행 · 열 모양 붕괴 신고)

**계획서에 없던 판정 하나** — 「칸 전체가 날짜뿐」만 무는 것으로는 **열이 하나 사라진 행을
정규식이 조용히 건너뛴다**. 계획서 8절이 그 위험에 「침묵 말고 신고」라고 답을 적어 뒀길래
`VERDICT_ROW_HEAD` 로 행 머리를 따로 세어 개수가 다르면 신고하게 했다(3줄).

## 검증 (맨몸 · 리다이렉션 0)

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=$(mktemp -d) PYTHONPATH=src python3 -m unittest discover -b -s tests
Ran 647 tests in 15.996s · OK · rc 0
```

`src/`·`e2e/` **0줄** · `docs/specs/` 무접촉 · `data/crawl.db` **무개봉** · 새 의존성·스키마·
마이그레이션·재색인 **0** · 바깥 네트워크 0 · `main` 직접 커밋 0 · PR #7 무접촉.

**계획서가 안 적은 파일 하나를 고쳤다 — `README.md` 한 줄(`단위 639건`→`647건`).**
계획 범위를 넓힌 것이 아니라 **테스트를 더하면 반드시 따라오는 부기**다: `test_readme.py` 가
README 의 건수를 실제 수집 결과와 대조하므로, 갱신 없이는 전수가 초록이 될 수 없다.
계획서 4절이 이미 「건수가 639 + 새 검사 수여야 한다」로 예견했고, 선례도 일치한다 —
계획 68·69·70 세 커밋 모두 같은 한 줄을 동반 갱신했다(`27e5e20`·`1653d8c`·`72c8bbb`).

## 다음

**테스트 phase** (`rules/test.md`) — 계획서 4절의 남은 넷을 저장소 밖 사본에서 변이로 판다:

- **M3 재발** — 다른 완료 행의 e2e 칸을 `2026-09-01` 로 바꾸면 다시 우는가
- **M5 판정 무력화** — `verdict_gap` 몸통을 `return None` 으로 하면 `VerdictGapTest` 가 죽는가
- **M6 추출기 무력화** — 행 정규식이 아무 행도 안 물면 하한 못이 죽이는가
- 그리고 **범위를 넓히는 쪽** — 계획 70 테스트 phase 가 「넓어지는 변이 둘이 살아 있다」를
  실측한 자리라 같은 축을 여기서도 판다(완료 아닌 행까지 물게 하면 죽는가)

**사람 몫으로 남긴 것 하나** — `digest.md` 는 **214줄로 상한 200 을 넘는다**. 지울 수 있는
완료 항목이 여덟 줄뿐이라 산술이 안 되고, **무인 모드는 파일·데이터를 삭제하지 않는다**.
무엇을 버릴지는 아침에 사람이 정한다 — 야간 보고서에 올린다.
