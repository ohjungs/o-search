# e2e — `project-md-diet` (계획 97)

## 무엇을 재는가

이 계획의 산출물은 코드가 아니라 **문서**다. 그래서 e2e 도 「기능이 도나」가 아니라
**「다이어트한 `project.md` 만 읽고도 이 저장소를 돌릴 수 있나」** 다.
사람이 읽어서 판단하면 「내가 이미 아는 것」이 채워 넣으므로, **문서에서 이름을
기계로 뽑아** 그대로 실행했다. 문서가 틀리면 실행이 깨진다.

## 시나리오 1 — 문서가 스스로 실행된다

`docs/project.md` 의 `**e2e 13종**` 항목에서 백틱 토큰을 정규식으로 뽑아
`PYTHONPATH=src python3 e2e/<이름>.py` 를 조립해 돌렸다(2026-09-13):

```
문서에서 뽑은 이름 13개
crawl_e2e rc=0 · indexer_e2e rc=0 · noindex_e2e rc=0 · search_api_e2e rc=0
crawl_delay_e2e rc=0 · non_ascii_e2e rc=0 · hidden_passage_e2e rc=0 · design_check rc=0
tokenizer_e2e rc=0 · domain_key_e2e rc=0 · deadline_e2e rc=0 · interrupt_e2e rc=0
indexer_interrupt_e2e rc=0
→ 13종 전부 rc=0
```

**접힌 표기가 손실이 아님을 이것이 증명한다.** 옛 문서는 같은 13개를 13줄로 적었고
지금은 3줄이다 — 이름·경로·접두사가 하나도 안 틀렸다.

## 시나리오 2 — 접두사가 장식이 아니다

`PYTHONPATH=src` 가 실제로 필요한지 확인했다: **13 중 7 이 자체 `sys.path.insert` 가
없다.** 나머지 6 에는 무해하다. 문서가 접두사를 붙여 적은 것이 옳다.

## 시나리오 3 — 옮긴 것이 안 없어졌다

```bash
git show 3bfdb35:docs/project.md | sort -u > /tmp/before.txt
cat docs/project.md docs/baselines.md | sort -u > /tmp/after.txt
comm -23 /tmp/before.txt /tmp/after.txt
```

사라진 줄 **14** 이고 전부 의도한 것이다 — 거짓이 된 초기화 주석 2(「코드가 0줄이라
명령이 없다」) · 낡은 포인터 2(재작성) · `project.md` 와 통째 중복이던 10(맨몸 규율·
테스트·린트). **중복 10줄의 «사실»은 `project.md` 에 그대로 있다**(맨몸 규율 문단 ·
`-b` 설명 · 「린트·타입체크는 없다」).

## 리뷰가 잡은 것 — 이 e2e 로는 안 잡혔다

백지 패스가 **`project.md:44`** 의 사실 오류를 물었다: 「종료 코드는 다섯이 같은
관용구다(0/1/2)」가 **5중 3만** 참이다. `e2e/perf_search.py` 는 `return 0` 하나뿐이고
`e2e/crawl_delay_e2e.py` 는 `sys.exit` 가 **0건**이라 둘 다 **2 를 낼 길이 없다**.
rc=0 만 보는 이 e2e 는 **성공 경로만 밟으므로 이 오류를 못 본다** — 실패 경로의
종료 코드는 정적으로 확인했다(`grep -c 'exit(2)\|return 2'` → 3/7/1/**0**/**0**).

## 판정

**통과.** 전수 763 OK · e2e 13/13 rc=0 · `project.md` **60줄**(`rules/docs.md` 1절 예산과 동일).
