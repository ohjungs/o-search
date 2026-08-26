---
signal: GREEN
mode: night
plan: quality-eval
phase: 개발
step: 4/4
attempt: 0
iteration: 51
night_iterations: 20
night_red: 0
night_retries: 0
night_self_amendments: 0
updated: 2026-08-26 (반복 51)
ctx: 57% / 200k
rules: rules/dev.md
---

# 현재 상태

**`quality-eval` 개발 3/4 완료 → 다음은 4/4 (실측·기록).**
`e2e/quality_eval.py` 146줄 + `tests/test_quality_eval.py` 8건. 164/164 통과.

## 실측이 나왔다 — 기능 2 는 **합격**이다

```
$ PYTHONPATH=src python3 e2e/quality_eval.py
64문서 색인 / 질의 40개
한국어 17/20 (85%)
영어 18/20 (90%)
[ko] 보관법 → http://q.test/ko/kimchi/07 (매치 12건, 순위 밖)
[ko] 올레길 → http://q.test/ko/jeju/05  (매치 12건, 순위 밖)
[ko] 일출봉 → http://q.test/ko/jeju/07  (매치 11건, 순위 밖)
[en] loaf   → http://q.test/en/sourdough/05 (매치 12건, 순위 밖)
[en] tuples → http://q.test/en/python/03    (매치 13건, 순위 밖)
합격선 80% — 통과   (종료 코드 0)
```

`concept.md:22-23` 이 요구한 숫자를 **처음 쟀다.** 미포함 5건은 전부 설계
`## 착수 전 탐침` 이 예고한 토크나이저 실패다 — 복합어 뒷부분(`보관법`·`일출봉`),
띄어쓰기 변형(`올레길`), 불규칙 복수(`loaf`), 접두 매치의 방향(`tuples`).
**앞 세션이 status 에 적어 둔 ko 18/20 은 낡은 탐침값이었다.** 실측은 ko 17/20 이고
커밋 `d014408` 의 메시지가 이미 그 값을 적고 있었다. 여기 것을 실측으로 맞췄다.

## 스텝 4 가 답해야 하는 것 — 100% 가 아니어서 오히려 쉬워졌다

설계 `## 가정` 은 **"100% 가 나오면 합격이 아니라 의심 신호"** 라고 했다.
실측은 85/90% 라 그 함정은 피했지만, **35건이 순위 1위**라는 사실은 남는다.
e2e 시나리오 3(방해 문서 제거 시 포함률이 오르는가)으로 여전히 갈라야 한다.

- `docs/project.md` 품질 기준에 명령과 이 숫자를 등록한다 (기준선이지 절대 품질이 아니다)
- `docs/e2e/quality-eval/result.md` 에 시나리오 결과를 남긴다
- 미포함 5건의 원인(토크나이저)은 이 계획의 `## 하지 않을 것` 이라 **`digest.md` 후보**로만 남긴다

## 40줄 한도를 넘겨 적용한 근거 (`rules/dev.md` 6절)

러너 하나가 146줄이라 무인 40줄을 넘는다. 세 물음이 전부 통과라 패치가 아니라 적용했다:
계획 `스텝 3` 의 예상 파일 그대로(`e2e/quality_eval.py`) · **같은 스텝에 덮는 테스트 8건** ·
1인 저장소 · `src/` 0줄 · 보안 무관. 변이 7종을 심어 테스트가 전부 잡는 것까지 확인했다.

## 보류 (사람 승인 대기 — 무인 모드에서 착수 금지)

- `recrawl`(`concept.md:31` 30일 재방문) · `X-Robots-Tag` 헤더 — 둘 다 **스키마 변경**이다
- `robots.py:_fetch_robots` 의 `resp.read()` 무상한 — 자원 관련이라 무인 금지 (`digest.md`)
