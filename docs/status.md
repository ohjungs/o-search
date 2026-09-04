---
signal: GREEN
phase: 개발
step: 4
attempt: 0
iteration: 299
updated: 2026-09-04
ctx: 31
night_iterations: 128
night_red: 2
night_retries: 0
plan: hidden-passage
---

# 현재 상태

**개발 4 — 리뷰 3 의 반려 `[R51-5]` 를 TDD 로 닫았다.** 제품 `src/websearch/extract.py`
**한 파일 +17/-2**(한도 20 안 · 계획 「건드릴 파일」 안) · `tests/test_extract.py` +38 ·
`README.md` 숫자 한 줄. 새 파일 0 · 새 의존성 0 · 커밋된 변이 0.

**신호는 GREEN** — 단위 **593건 OK** rc 0(맨몸·단독 13.233초) · **e2e 20종 전수 rc 0** ·
RED 0 · 재시도 0. 브랜치 `loop/hidden-passage`, 기점 `d5367fa`(**`main` 아님** — 아래 「원격」).

## 무엇을 고쳤나 — `_IMPLIED_END` 의 키를 열여섯으로 채웠다

`src/websearch/extract.py`. 집합 주석이 스스로 적은 멤버십 규칙(「**종료 태그 생략이
허용된** 요소」)에 키가 여덟뿐이라, 나머지 여덟(`thead`·`tbody`·`tfoot`·`caption`·
`colgroup`·`optgroup`·`rt`·`rp`)에 숨김이 붙으면 형제가 와도 안 걷혀 **보이는 문단이
통째로 사라졌다.** 이제 키는 명세 「optional tags」 **열여섯 전부**다.

**표 쪽은 `_TABLE_PARTS` 하나에서 빼기로 적었다.** 삽입 모드 넷(in cell · in row ·
in table body · in caption)이 **같은 목록**을 쓰기 때문이고, 빼는 것이 «형제가 아니라
자식» 이다 — `<td>` 는 `<tr>` 을 안 닫고, `<tr>` 은 `<tbody>` 를 안 닫고, `<col>` 은
`<colgroup>` 안이다. 그 뺄셈 세 줄이 과잉 닫기(누출)를 막는 자리다.

**리뷰의 제안은 절반이었다 — 값 축도 함께 넓혀야 했다.** 리뷰는 「키 여덟」만 적었는데
암묵적 닫기는 **스택 꼭대기만** 본다. `<tbody hidden><tr><td>숨은<tfoot>` 에서 `tfoot`
이 `td`·`tr` 을 못 걷으면 루프가 셀에서 멈춰 `tbody` 에 못 닿는다. 그래서 `tr`·`td`·`th`
의 **값**에 구획 태그를 더했다. 「어느 축의 전수인가」를 적으라는 규칙이 **처방에도 같이
걸린다.**

## RED → GREEN 판정 줄

`PYTHONPATH=src python3 -m unittest -v tests.test_extract.TestExtractBlocks.
test_every_element_with_an_optional_end_tag_is_closed_by_its_sibling`

- **RED**: `Ran 1 test in 0.001s` / **`FAILED (failures=6)`** — thead·tbody·caption·
  colgroup·optgroup 다섯이 `[] != ['보이는 …']`, rt 가 `['漢'] != […]`. 리뷰가 실측한
  여섯 모양 그대로다.
- **GREEN**: 전체 스위트 `Ran 593 tests in 13.233s` / **`OK`** rc 0(맨몸·단독).

**`rt` 만 기대값을 고쳤다.** 리뷰 표의 「브라우저」 칸(`漢 보이는`)을 그대로 베꼈는데
`rt` 는 `_INLINE_TAGS` 라 경계에 공백이 안 들어간다(`Kim<b>chi</b>` → `Kimchi` 규칙).
`extract_text` 도 `漢보이는` 인 것을 실측하고 `["漢보이는"]` 로 정정했다 — **재는 것은
띄어쓰기가 아니라 `보이는` 이 나오느냐다.**

## 관문 — 75,076 전수를 다시 돌렸다 (누출 0)

리뷰가 「단언보다 세다」고 지정한 그것이다. 태그 **139** × **139** × 숨김 4모양 =
**77,284 조합**을 HEAD 의 `extract.py` 를 임시 모듈로 띄워 **나란히** 돌렸다.

| | HEAD | 지금 |
|---|---|---|
| 누출(숨은 텍스트가 블록으로 나옴) | 7,784 | **7,784** |
| 미달(보이는 형제가 사라짐) | 69,528 | **69,280** |

- **새 누출 0 · 새로 사라진 것 0 · 수리된 것 248.**
- 누출 7,784 는 `14 void × 139 × 4` 로 **딱 떨어진다** — 누출 집합이 여전히
  `_VOID_TAGS` 뿐이고 그것은 설계가 고른 정답이다(void 는 자식을 못 가져 브라우저에서도
  보인다).
- 수리된 바깥 태그 열하나: `caption`·`colgroup`·`optgroup`·`rp`·`rt`·`tbody`·`td`·
  `tfoot`·`th`·`thead`·`tr`.

## 완료 기준 대조 (계획 51 5절)

1. **숨은 텍스트 0/5** — 계획 51 이 심은 임시 DB 탐침 행이 단위 스위트 안에 있고 초록이다.
2. 숨은 블록만 질의어를 담은 문서는 **문단 0개** — 같은 행이 붙든다.
3. **회귀 0** — 회귀 표본 **134개**(`data/crawl.db` · `e2e/quality/corpus.json` ·
   `tests/test_extract.py` HTML 리터럴)를 HEAD 모듈과 대조: **`extract_text` 차이 0** ·
   `extract_blocks` 차이는 **이번 fixture 1건뿐**. `_IMPLIED_END` 를 읽는 곳은
   `_BlockParser.handle_starttag` **하나**(grep 실측)라 색인 경로는 구조적으로 안 지나간다.
4. 정상 HTML 블록 목록 무변 — `passage_eval` 블록 **253 무변**과 단위 593건이 함께 붙든다.
5. **단위 593건 OK** rc 0 — `Ran 593 tests in 13.233s / OK`.
6. **e2e 20종 전수 rc 0** — `passage_eval` 블록 **253** · 정확도 **100.0%**(398/398) ·
   채택률 99.5% · p95 **1.50ms** · `quality_eval` ko **20/20** · en **19/20** · 1위 **39** ·
   매치 평균 14.0 · `perf_search` p95 **8.71ms** · `search_api` p95 **2.08ms** ·
   `perf_crawl` 통과 · `design_check` 4축 통과.
7. `data/crawl.db` sha256 `85c96744…75bda18` 무변 · `data/`·`e2e/`·`docs/specs/` 무변.
8·9. 변이는 **테스트 4 의 몫**이다 — 이 스텝은 심은 변이 0.

## README 숫자가 즉시 울었다

테스트 +1 에 `test_readme.test_verification_counts_match_reality` 가
`(592, 20) != (593, 20)` 으로 FAILED. 손으로 적는 숫자를 **한 반복 안에** 잡은 가드다
(반복 168 이 「하루 안에 값을 증명했다」고 적은 그 검사다).

## 러너 규율

판정 실행은 **맨몸·단독**이다 — `PYTHONPATH=src python3 -m unittest discover -b -s tests`
와 e2e 20종 각각 `PYTHONPATH=src python3 e2e/<이름>.py`. **이번 반복은 파이프·리다이렉션
0회**다(직전 반복이 e2e 20종에 리다이렉션 20회를 적은 자리 — 이번엔 `for` 루프에
리다이렉션을 안 붙이고 출력을 그대로 읽었다). 출력 조작 0회. 전수 스캔·회귀 대조 스크립트는
러너가 아니라 **저장소 밖 스크래치패드**에 있고 안 커밋한다.

## 문서

`status.md`(이 파일 · 반복 **299**) · `metrics.md`(반복 **299** · 개발 **72** · 「전수의
축」 교훈에 개발 4 의 닫는 문장을 이어 붙였다) · `index.md`(51번 줄에 개발 4) ·
`history_current.md`(개발 4 항목 · **항목을 붙인 뒤 세니 311줄이라 그 자리에서 회전했다** —
테스트 2(294) 한 항목 48줄을 `docs/history_051.md` 로 밀어 **263줄**. 서른한 회전 연속
지각 0. 직전 회전이 남긴 넷 중 **[R51-5] 를 닫아 사유가 소진된 하나**만 밀었다) ·
`digest.md`(**200줄 유지** — 「아카이브 명부」에 `history_051.md` 를 더하고 회전 서술을
같은 줄에 이어 붙였으므로 **새 색인 구멍 0**) · `README.md`(단위 592 → **593**, e2e 20 그대로).

## 다음 — 테스트 4

변이로 **새 키와 새 값을 각각** 재고, 특히 `_TABLE_PARTS` 의 **뺄셈 세 줄**이 단언에
걸려 있는지 본다 — 빼기를 지우는 변이가 초록이면 「자식 방향」 가드가 비어 있다는 뜻이고,
그 방향이 곧 누출이다. 개발 3 이 남긴 살아남은 변이 둘(⑨caption 삭제 · ⑩search 삭제)은
이제 `_TABLE_PARTS`·`p` 목록 위에서 다시 판정된다.

## 원격 — `origin/main` 은 계획 47 까지다

- **커밋·푸시 뒤에 `git ls-remote origin` 을 다시 읽었다**(digest 의 「원격을 바꾸는 동작을
  «명령을 보냈다» 로 기록하지 않는다」 항목). 아래 SHA 는 이 반복이 실제로 읽은 값이다.
- **`loop/hidden-passage` = `918b925`** (개발 4 커밋 · `2b9a6a6` → `918b925`, fast-forward).
  `git ls-remote origin loop/hidden-passage` 의 `918b9255…7a02d` 와 로컬 `HEAD` 가 같다.
  `main` = `687a159` 무변. `--no-verify`·`--force` 0회 · 훅 우회 0.
- **PR #7** — `loop/merge-48-50` → `main`, 계획 48·49·50. **OPEN·미병합.** 병합은
  **사용자가 처리한다** — 이 반복은 PR 을 열지도 닫지도 않았고 그 브랜치를 건드리지도,
  `main` 으로 리베이스하지도 않았다.
- **계획 51 의 기점은 `main` 이 아니다** — `origin/main`(`687a159`)에는 계획 48·49·50 이
  없어 `README.md` 의 건수 단언이 거기서는 RED 다. `d5367fa` 에서 브랜치를 땄다.
- 앞선 병합: PR #6 = 계획 44~47(`687a159`). 충돌 0.

## 사람이 정할 것 — 다섯 (PR #7 이 붙었다)

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1, 입력창의 유일한 경계).
2. **`--focus` 는 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 이 0 일
   때만 이웃이 되고, 검사기가 매 실행 offset > 0 을 확인한다(실측 2px).
3. **반응형 360px 미검증** — 브라우저가 없어 이 저장소의 누구도 그 화면을 못 그린다.
4. **회전 규약·러너 규율의 저장소 밖 절반**과 **사양이 남긴 둘**(`docs/specs/concept.md` 의
   `## 사람이 정할 것` — 속도 제한 시점, 사양 숫자 90%·500ms·60회/분이 초안이라는 것).
5. **PR #7 병합** — 위 「원격」 절.
