# e2e — `e2e-roster` (계획 98)

## 무엇을 재는가

산출물이 코드가 아니라 **명부와 명부를 무는 자**다. 그래서 재는 것은 「기능이 도나」가
아니라 **「명부가 사실인가」**와 **「자에게 이빨이 있나」** 둘이다. 사람이 읽어서 판단하면
「내가 이미 아는 것」이 채워 넣으므로 **문서에서 이름을 기계로 뽑아 그대로 실행했다**
(계획 97 의 방식을 그대로 썼다 — 새 수단을 짓지 않았다).

**선행 관문**: 전수 `PYTHONPATH=src python3 -m unittest discover -b tests` → **770 OK**(18.8s) ·
린터·타입체커 **없음**(`project.md`) · CI 확인 명령 **없음**.
**품질 기준 4축은 이 계획이 안 건드렸다** — 제품 `src/` 0줄이라 걸 자리가 없다.
다만 시나리오 1 이 `design_check`·`crawl_delay_e2e` 를 포함해 돌리므로 아래 표에 값이 있다.

## 시나리오 1 — 명부가 스스로 실행된다 → **18/18 rc=0**

`docs/project.md` 의 `**e2e 18종**` 항목 본문에서 백틱 토큰을 정규식으로 뽑아
`PYTHONPATH=src python3 e2e/<이름>.py` 를 조립해 돌렸다(2026-09-13):

```
문서가 말하는 종수 18 · 뽑은 이름 18
crawl_e2e             rc=0 14.7s    indexer_e2e           rc=0  2.9s
noindex_e2e           rc=0  5.9s    search_api_e2e        rc=0 15.1s
crawl_delay_e2e       rc=0  4.6s    non_ascii_e2e         rc=0  2.6s
hidden_passage_e2e    rc=0 10.8s    design_check          rc=0  0.1s
tokenizer_e2e         rc=0  5.8s    domain_key_e2e        rc=0  7.1s
deadline_e2e          rc=0 19.9s    interrupt_e2e         rc=0 18.3s
indexer_interrupt_e2e rc=0  6.9s    crawl_politeness_e2e  rc=0  5.1s
pagination_ui_e2e     rc=0 11.9s    recrawl_e2e           rc=0  6.8s
retry_interval_e2e    rc=0 15.7s    url_normalize_e2e     rc=0  5.1s
→ 18/18 rc=0 (합 약 3분)
```

**570 이 다섯을 처음 돌려 잰 값이 재현됐다** — `crawl_politeness_e2e` 5.1s ·
`recrawl_e2e` 6.8s · `retry_interval_e2e` 15.7s · `url_normalize_e2e` 5.1s ·
`pagination_ui_e2e` 11.9s. 등재가 사실 기록이었다는 것이 두 번째 실행으로 확인됐다.

## 시나리오 1 이 **첫 판에 실패했다** — 그리고 그것이 이 phase 의 수확이다

첫 실행은 **이름을 19개** 뽑았고 열아홉째가 `E2eRosterTest` 였다:

```
E2eRosterTest  rc=2   can't open file '…/e2e/E2eRosterTest.py'
→ 19종 중 rc=0 이 18
```

**내가 571 에서 그 줄에 넣은 포인터다** — 「명부가 낡으면 `E2eRosterTest` 가 문다」.
사람에게는 유익한 한 마디지만, **그 줄은 기계가 읽는 줄**이라 유령 이름을 하나 만들었다.
문서가 스스로 말하는 종수(18)와 뽑히는 이름 수(19)가 갈렸다.

**고친 것은 시나리오가 아니라 문서다**(`e2e.md` 7절 — 통과시키려고 시나리오를 낮추지
않는다). 포인터를 클래스 대신 **파일**로 바꿨다: `` `E2eRosterTest` `` → `` `test_docs.py` ``.
점이 든 토큰은 「맨 식별자」 정규식에 안 잡히므로 이름 줄이 다시 순수해진다.
추출기를 「이름 나열까지만 읽게」 좁히는 길도 있었지만 그것은 **자를 통과시키려고 자를
깎는 것**이라 안 했다.

**이 줄에 계약이 하나 생겼다 — 그리고 그 계약을 재는 자는 아직 없다**:
「`**e2e N종**` 항목 안의 맨 식별자 백틱 토큰은 정확히 명부다.」
`e2e_roster_gap` 은 **자리를 안 재므로**(이름이 문서 어디에 있든 등재로 친다) 이것을 못 문다.
`digest.md` 의 `[6]`(「18종」 라벨이 명부 길이와 안 묶였다)과 **같은 자리**라 그쪽에 합쳤다.

## 시나리오 2 — 음성 대조: 자에게 이빨이 있다

명부에서 이름 하나(`recrawl_e2e`)를 지운 트리에서 전수를 돌렸다:

```
FAIL: test_project_names_every_e2e (test_docs.E2eRosterTest)
AssertionError: 'project.md 가 `e2e/` 의 1개를 이름으로 안 부른다 — `recrawl_e2e`.
                 명부에 없는 e2e 는 아무도 안 돌린다(루프는 이 파일을 읽어 무엇을 칠지 정한다)'
Ran 770 tests — FAILED (failures=1)
```

되돌리니 **770 OK**. **실패 한 건뿐이라는 것이 값이다** — 자가 무는 자리가 하나로
모여 있고, 명부를 고치는 사람이 어느 이름인지 메시지에서 바로 읽는다.

함수 단위의 이빨은 테스트 phase 가 **변이 10판**으로 이미 쟀다(8 사망 · 산 둘을 닫았다 ·
하한 못 1→0 만 생존하고 그 이유는 `status.md` 에 있다). 여기서는 **디스크 위에서** 다시 쟀다.

## 만든 파일

- `docs/e2e/e2e-roster/result.md` (이 문서)
- 새 e2e 시나리오 파일 **없음** — 계획대로 기존 수단(정규식 추출 + 전수)만 썼다.
  새 `e2e/*.py` 를 만들었다면 그것부터 명부에 올려야 했다(자기 자신이 무는 자리다).

## 판정

**통과.** 시나리오 둘 다 만족했고, 첫 판의 실패는 **문서를 고쳐** 닫았다(시나리오 무변).
