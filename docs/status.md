---
signal: DONE
phase: e2e
step: 1/1
attempt: 0
iteration: 349
updated: 2026-09-05
ctx: 50
night_iterations: 166
night_red: 2
night_retries: 1
plan: endtag-cut-cover 계획 59 (e2e 완료 · 완료 기준 6/6 충족)
---

# 현재 상태

**계획 59 를 닫는다 — e2e 21종 전수 `rc 0` · 기준선 회귀 0 · 완료 기준 6/6 을 오늘 다시
재서 충족했다.** 이 phase 가 한 일은 셋이다: **면제 판정**(새 e2e 를 안 만든다), 21종 전수,
변이 셋(무변이 대조군 · M-a · `li` 줄 삭제)을 **메모리에서** 다시 재기. 증거는
`docs/e2e/endtag-cut-cover/result.md` 에 있다.

## 면제 — 새 e2e 를 안 만든다 (`rules/e2e.md` 3절)

계획이 바꾼 것은 `tests/test_extract.py` 의 단언 +12줄과 주석뿐이고 제품 `src/` 는 0줄이다.
파서 동작이 한 글자도 안 바뀌었으니 **프로세스 밖에서 달라지는 동작이 0** 이다. 새 단언이
지키는 실물 계약(숨김이 문서 끝까지 고정돼 뒤 문단이 사라지는 것)은
`e2e/hidden_passage_e2e.py` 가 이미 crawl→색인→HTTP 로 재고 있고 오늘도 **0/5 · 본문 5/5**
로 통과했다. 만든 e2e 파일 0 · 고친 e2e 파일 0.

## e2e 21종 — 전부 `rc 0` · 기준선 회귀 **0**

정확도 **100.0%**(=) · `/passages` p95 **1.51ms**(1.52) · `perf_search` p95 **8.80ms**(8.81 ·
기록 9.11) · 품질 ko **20/20**(=) · en **19/20**(=) · 매치 14.0/11/28(=) · 크롤
**10.24/s**([차단] 10.24 · 반복 344 는 10.21) · 숨은 텍스트 **0/5** · 디자인 4축 통과
(JS 0 B · 최저 대비 4.87:1). **움직인 기준선이 없어 `docs/project.md` 의 수치는 한 줄도
안 갱신했다** — 제품 0줄인 계획이라 기대한 결과 그대로다.

## 완료 기준 6/6 — 오늘 실측

1. 전수 `Ran 605 tests in 13.789s` · `OK` · rc 0 (건수 무변)
2. 변이 M-a(`del self._els[i:i+1]`) → `failures=2`, 늘어난 칸이 **`shape='안 닫힌 span'`**
   (착수 탐침은 1)
3. 무변이 대조군 `605 failures=0` — 새 subTest 도 `반대 방향` 줄도 초록(오탐 0)
4. `_IMPLIED_END` 에서 `li` 줄을 지우는 변이 → 죽는 것은 **다른 테스트 둘뿐**이고
   (`test_an_optional_end_tag_does_not_hide_the_next_sibling` 의 `li`·`li 안의 안 닫힌 p`)
   `안 닫힌 span` 은 초록이다 — **표와 다른 축**이라는 계획의 주장이 그대로 재졌다
5. 고친 파일 `tests/test_extract.py` 하나(`7396117` +12줄 · `97c3057` 주석만) · `src/` 0줄 ·
   `git status --short` 빈손 · `README.md`·`docs/specs/` 무접촉 · `data/crawl.db` sha256 무변
6. 위 21종 전수

## 다음

**계획 59 DONE.** 다음 반복은 계획 phase — 계획 59 마감(계획서·있으면 설계서 아카이브 회전 ·
`digest.md` 의 후보 `[5]` 「닫는 태그가 자손을 잘라내는 자리를 붙드는 단언이 하나뿐이다」에
취소선 · `## 완료` 절에 계획 59 줄)과 새 후보 탐색을 함께 돈다. 계획 59 의 테스트 phase 가
등재한 새 갭 1건(4점, 8점 미만)도 `digest` 의 후보 목록에 있다.

## 한도

- 병합은 사람 몫이다 — 계획 57·58·59 의 커밋이 `loop/passage-cost-band` 에 쌓여 있고
  `origin/main` 무접촉 · PR 0(만들지도 조회하지도 않았다).
- 러너에 리다이렉션·파이프를 안 붙인다 — 오늘도 위반 0회(누적 37 유지).
- 변이는 계속 **메모리에서**(`mock.patch.object`) 걸고 `PYTHONPYCACHEPREFIX=$(mktemp -d)` 를
  함께 준다 — 저장소 파일과 `data/crawl.db` 는 안 건드린다.
