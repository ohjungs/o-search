---
signal: GREEN
mode: night
plan: quality-eval
phase: 개발
step: 3/4
attempt: 0
iteration: 50
night_iterations: 19
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-26 (반복 50)
ctx: 45% / 200k
rules: rules/dev.md
---

# 현재 상태

**`quality-eval` 개발 2/4 완료 → 다음은 3/4 (러너).**
`e2e/quality/corpus.json` 64문서 + `e2e/quality/queries.json` 40질의(ko 20 / en 20).
`tests/test_quality_corpus.py` 10건. 156/156 통과. 커밋 `d014408`.

> 기록 정정: 반복 50(개발 2/4)의 커밋은 들어갔으나 직전 세션이 API 502 로 죽어
> `status.md`·`history_current.md`·`metrics.md` 가 한 스텝 뒤처져 있었다.
> 커밋 로그와 파일 실측으로 대조해 여기서 맞췄다. 코드는 건드리지 않았다.

## 스텝 3 이 지켜야 할 계약 (`docs/design_quality-eval.md` `## 계약`)

```
e2e/quality_eval.py [--corpus PATH] [--queries PATH]
```

- 러너가 `<html><title>{title}</title><body><p>{body}</p></body></html>` 로 감싸 `pages` 에
  넣고 `indexer.index_pages()` 를 부른다 (`e2e/perf_search.py:52-63` 과 같은 경로, 네트워크 없음)
- 판정은 `indexer.search(db, q, limit=100)` **한 번**으로 낸다 — 앞 10건이 곧 `limit=10` 결과
- **가드 3종은 전부 종료 코드 2** (품질 미달 1 과 구분한다)
  - G1 `answer` 가 코퍼스에 없다 / G2 어떤 질의의 매치 수 ≤ 10 (측정 불능) / G3 언어별 질의 수 ≠ 20
- 종료 코드 `0` 두 언어 모두 ≥80% / `1` 미달 / `2` 코퍼스 결함·사용법
- 출력: `한국어 NN/20 (NN%)` · `영어 NN/20 (NN%)` · 미스마다 `[ko] 질의 → 기대 URL (매치 N건, 순위 M|밖)`

## 스텝 4 가 쓸 실측 예상값 (탐침, 커밋 없음)

40질의 매치 **11~28건** — G2 여유. 정답 순위는 35건이 1위.
미포함 5건은 **의도적으로 심은 토크나이저 실패**다(설계 `## 착수 전 탐침` 이 예고한 것):
`보관법`→`김치찌개보관법` · `일출봉`→`성산일출봉` (복합어 뒷부분) / `올레길`→`올레 길` (띄어쓰기) /
`loaf`→`loaves` (불규칙 복수) / `tuples`→`tuple` (접두 매치의 방향).

이대로면 ko 18/20 · en 18/20 = **각 90%** 로 합격 예상. 다만 나머지 35건이 전부 1위라
설계가 말한 **"100% 는 의심 신호"** 에 가깝다 — 스텝 4 에서 e2e 시나리오 3
(방해 문서 제거 시 포함률이 오르는가)으로 갈라야 한다.

## 보류 (사람 승인 대기 — 무인 모드에서 착수 금지)

- `recrawl`(`concept.md:31` 30일 재방문) · `X-Robots-Tag` 헤더 — 둘 다 **스키마 변경**이다
- `robots.py:_fetch_robots` 의 `resp.read()` 무상한 — 자원 관련이라 무인 금지 (`digest.md`)
