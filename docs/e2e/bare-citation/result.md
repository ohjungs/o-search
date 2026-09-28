# e2e 결과 — bare-citation (계획 110, e2e phase)

- 2026-09-28 · 반복 662 · **새로 만든 e2e 파일 0개** (계획 109 와 같은 자리 — 소비자가 루프
  자신이라 e2e 도구가 전수 러너다)
- 선통과: 전수 `PYTHONPATH=src scripts/verdict.sh python3 -m unittest discover -b -s tests`
  → **844 OK rc=0** (맨몸·포그라운드). 린터·타입체커 **없다**(`docs/project.md ## 명령`).
  **CI 없다** — `.github` 가 없고 `project.md` 에 확인 명령이 없다
- 제품 **동작 0줄** — `git diff main...HEAD -- src` 는 21줄이고 **전부 주석·독스트링 산문**이다
  (`#` 로 시작하지 않는 32줄을 하나씩 대조: 16쌍 전부 `docs/design_*.md` 이름 치환). 그래서
  컨셉의 성능·경량 축은 이 계획이 건드린 파일에 걸 것이 없다 — 돌리지 않았고 **「통과」라고
  적지 않는다**(`rules/e2e.md` 1절 3항)
- UI 없음 → 4절 8단계 해당 없음. `data/crawl.db` 는 **손대지 않았다**(mtime 09-15 그대로)
- 사본: `git archive HEAD` 를 `/tmp/bc110_e2e` 에 풀어 **저장소 워킹트리는 무변경**으로 뒀다
  (실측 `git status --short` → 0줄)

## 시나리오 — 계획 6절 그대로 셋

### ① 대조군 — 손대지 않은 사본이 초록

```
/tmp/bc110_e2e $ … scripts/verdict.sh python3 -m unittest discover -b -s tests
  → ── Ran 844 tests in 25.370s OK rc=0
```

### ② 사건 재연 — **백틱 없이** 가리키고 아카이브하면 RED

사본에서 둘을 했다. ⓐ 사람이 흔히 쓰는 꼴로 주석 한 줄을 심고(백틱 없음)
ⓑ `rules/docs.md` 4절의 마감을 그대로 밟았다.

```
src/websearch/serve.py:2  # 이 자리의 경위는 docs/plan_bare-citation.md 에 있다.
mv docs/plan_bare-citation.md docs/plan_history_085.md
  → ── Ran 844 tests in 33.324s FAILED (failures=1) rc=1
```

**실패는 정확히 하나**고 자리를 그대로 댄다:

```
FAIL: test_code_cites_documents_that_exist (test_docs.CitationAliveTest)
  src/websearch/serve.py:2 — `plan_bare-citation.md`
```

계획 109 의 자였다면 **이 편집은 조용했다** — 백틱이 없기 때문이다. 그것이 ③ 이다.
다른 문서 가드는 하나도 안 울었다: 계획서 파일이 사라지고 `index.md` 의 「진행」 행이
그대로인데도 전수가 조용하다.

### ③ 음성 대조 — 축만 되돌리면? **조용하지 않았다 — 세 겹으로 죽는다**

②의 편집을 그대로 두고 축만 계획 109 꼴(백틱 필수)로 되돌렸다. 계획서가 예상한 것은
「조용하다」였는데 **실측은 달랐고, 더 좋은 쪽으로 달랐다.**

```
/tmp/bc110_e2e $ … python3 -m unittest -b tests.test_docs.CitationAliveTest
  → AssertionError: 52 not greater than or equal to 100
     — 인용을 52 회밖에 못 셌다
```

판정을 분리해서 재니 셋이 갈린다:

| | 되돌린 축에서 | 읽는 법 |
|---|---|---|
| 심은 bare 인용 | **안 잡힌다** (판정 목록에 `serve.py:2` 없음) | **계획 110 이 잡는 것이 정확히 이것**이라는 증거 |
| 하한 100 | 실물 108 → **52** 로 떨어져 문다 | 축 제거 변이가 여기서 또 죽는다 |
| 오탐 축 | `` `plan_x.mdx` `` 두 자리가 결손으로 잡힌다 | 되돌린 축은 **뒤 낱말 경계도 같이 잃는다** — 리뷰 [R110-1] 이 고친 구멍이 되살아난다 |

시나리오를 낮추지 않고 그대로 돌린 결과를 적는다 — **「조용하다」는 성립하지 않았다.**
성립한 것은 그보다 강한 것이다: 축을 되돌리는 변이는 **판정·하한·오탐 세 자리에서** 죽고,
그중 셋째는 이 반복의 리뷰가 만들어 준 자리다.

## 판정

**통과** — 시나리오 3종 전부 실행했고 ①② 는 예상대로, ③ 은 예상보다 강하게 나왔다.
새 e2e 파일 0개 · 계획 밖 파일 수정 0개 · 저장소 워킹트리 무변경.
