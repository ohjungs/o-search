---
signal: GREEN
mode: night
plan: quality-eval
phase: 개발
step: 1/4
attempt: 0
iteration: 48
night_iterations: 17
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-25 (반복 48)
ctx: 82% / 200k
rules: rules/design.md
---

# 현재 상태

**`quality-eval` 설계 완료 → 개발 phase 1/4.**
`docs/design_quality-eval.md` 작성. 브랜치 `loop/quality-eval`.
**컨텍스트 82% 로 이번 야간은 여기서 정지한다** (스텝 경계에서 끊었다).

## 설계가 정한 것 — 개발이 그대로 따른다

세 갈림길의 답은 `docs/design_quality-eval.md` `## 세 갈림길의 답` 절에 있다.
개발 전에 **`## 계약` 절만 다시 읽으면 충분하다.** 요지:

- **코퍼스**: 손으로 쓴 토픽 클러스터. 언어당 2토픽 × 16문서 = 32문서, 총 **64문서**.
  한국어 토픽 `김치찌개`·`제주도 여행`, 영어 `sourdough baking`·`python for beginners`.
  한 토픽의 16문서는 토픽 어휘를 **전부 공유**한다. 정답 문서도 같은 토픽 다른 질의의 방해 문서다
- **질의**: 토픽당 10개 → 40개. **1어절 원칙** (탐침에서 다어절이 AND 라 0건이 나왔다)
- **정답은 질의당 1건.** 분모 = 언어별 20, 분자 = 상위 10에 그 URL 이 든 질의 수
- **파일**: `e2e/quality/corpus.json` · `e2e/quality/queries.json` (HTML 아님, 러너가 감싼다)
- **가드 3종은 종료 코드 2** — 품질 미달(1)과 구분한다. 핵심은 G2 **매치 수 ≤ 10 이면 측정 불능**

## 다음 스텝 — 개발 1/4 (코퍼스 fixture)

`e2e/quality/corpus.json` 64문서를 쓴다. 완료 기준은 계획서 스텝 1 그대로
(`index_pages()` 반환 수 == 64, `is_noindex` 로 조용히 빠지는 문서 0건).

문서를 쓸 때 **일부러 넣어야 하는 것** — 탐침이 확인한 실패 원인이고, 이게 없으면
100% 가 나와도 토크나이저가 좋아서가 아니라 코퍼스가 쉬워서다:
조사가 붙은 어형(`김치찌개를`) · 복합어(`돼지김치찌개`) · 띄어쓰기 변형(`김치 찌개`) ·
영어 복수/활용형(`breads`, `baking`).

- 이미 한 것: 설계 문서, 계획서 스텝 3 완료 기준에 가드 추가, 계획서 `SCHEMA` 열 이름
  오기 수정(`text` → `body`). **코드는 여전히 0줄.**

## 보류 (사람 승인 대기 — 무인 모드에서 착수 금지)

- `recrawl`(`concept.md:31` 30일 재방문) · `X-Robots-Tag` 헤더 — 둘 다 **스키마 변경**이다
- `robots.py:_fetch_robots` 의 `resp.read()` 무상한 — 자원 관련이라 무인 금지 (`digest.md`)
