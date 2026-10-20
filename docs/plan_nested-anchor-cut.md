# 계획 121 `nested-anchor-cut` — 중첩 `<a>` 가 내비·TOC 를 한 블록으로 둔다

- **근거**: 탐색 **6순위** — 후보 **`[6]`**(`digest.md` 후보 `[6]`「중첩 `<a>`」)이 **계획 120 으로 열렸다.**
  등재문의 여는 조건은 「이 모양이 «근거로 나가 본문을 이긴다» 는 **소비** 측정이 나오는 날」
  이었고, `e2e/passage_consume.py` 가 그 수를 냈다 — **상한 44.4%**(분자 12 / 분모 27 ·
  모양 블록 49 · 3문서) · `rc=1` · **0 이 아니다.** 나가는 근거가 TOC 한 줄이다:
  질의 `software Cflow cflow` → position 4 `Cflow (http://www.gnu.org/software/cflow)`.
- **공급은 작다** — 계획 119 census 가 20,000문서에서 **6문서·53블록**(블록 698만의
  **0.0008%**). 그래서 이 계획은 끊김을 **넓히는** 것이 아니라 **브라우저 답에 맞추는** 것이다.

## 문제 · 목표 · 기대 결과

`src/websearch/extract.py` 의 `_BlockParser` 는 중첩 `<a>` 에서 바깥 링크를 안 닫는다
(`html.parser` 가 안 닫고 `_IMPLIED_END`(`extract.py:62`)에 `a` 항목이 없다). 실물 TOC 꼴
`<li><a name=toc_Health href=#Health>Health (<a href=…>…</a>)</a>` 에서 둘이 따라온다:

1. `handle_endtag`(`extract.py:395`)의 `_after_link` 가 **안 선다** → 인접 링크 경계
   (`extract.py:341`)가 그 자리에서 안 선다
2. 안쪽 `</a>` 뒤 글자가 `_els` 꼭대기 셋째 칸(「링크 안인가」)이 **참인 채라 산문으로
   안 잡힌다**(`_prose` 가 안 선다 — 후보 `[4]`(`digest.md` 후보 `[4]`「천장 ⓐ 와 미닫힘」)가 같은 성질의
   반대 방향을 쟀다)

**브라우저는 중첩 링크를 금지해 안쪽 `<a>` 시작에서 바깥 것을 암묵적으로 닫는다.**
기준 모델이 저장소에 이미 있다 — `e2e/passage_shapes.py:151` 의 `_NestedRef`
(`_BlockParser` 하위 클래스 · 계획 119 census 가 쓴 자).

**목표**: `_BlockParser` 가 이 모양에서 `_NestedRef` 와 같은 블록을 낸다.
**기대 결과**: 소비 분자 **12 → 0**(`passage_consume.py` `rc=1` → `rc=0`) · 공급의
「덜 끊음」 53 → 0 · **「더 끊음」은 0 유지**(계획 119 가 20,000문서에서 0 으로 쟀다 ·
95% 상한 약 0.015% — 새로 끊는 자리가 생기면 그 수가 깨진다).

## 가정 (명시 · 스텝 1 이 실측한다)

**색인 경로는 안 바뀐다.** `_IMPLIED_END` 를 읽는 곳은 `extract.py:353` 한 곳뿐이고
(`grep -n _IMPLIED_END` 2건) 그 자리는 `_BlockParser.handle_starttag` 안이다.
틀리면 **재색인 계획**이므로 YELLOW 다.

## 설계 — **필요하다** (`design.md` 1절 「대안이 2개 이상 갈림」)

후보 등재문이 갈림을 적었다: **바깥 `a` 를 닫는 쪽**(`_BlockParser` 전용 술어 · 계획
51·115 선례) 대 **고르는 규칙에 내비 벌점을 주는 쪽**(`indexer.passages` 의 `score`).
계획 단계에서 저울질하지 않는다(`plan.md` 6-1절). 설계가 답할 것 셋:

1. `_NestedRef` 의 답에서 위 TOC 꼴 경계가 **어디에** 서는가 — 바깥 `a` 가 닫히면
   끝의 `)` 가 링크 밖 글자라 `_prose` 가 서고, 그러면 계획 118 의 규칙대로 **안 끊길**
   수도 있다. census 의 「덜 끊음 53」이 어느 전제에서 나온 수인지부터 읽는다
2. 경계 쪽이면 `_IMPLIED_END` 에 `"a": {"a"}` 한 줄로 닫히는가, 아니면 `_after_link`·
   `_prose` 둘을 따로 손대야 하는가
3. 벌점 쪽을 버리는 근거 — `docs/specs/concept.md` 4축 중 어느 것이 갈랐는가

## 스텝

**둘이다** — 제품 변경이 경계 판정 한 자리고 나머지는 실물 수를 다시 적는 일이다
(`plan.md` 3절: 3개 미만이면 사유를 적는다).

### 스텝 1 — 중첩 `<a>` 에서 바깥 링크를 닫는다 (TDD)

- **의존**: 없음 (설계 결론을 입력으로 받는다)
- **건드릴 파일**: `src/websearch/extract.py` · `tests/test_extract.py`
- **완료 기준** (전부 실행해서 확인):
  1. **실패하는 테스트를 먼저** — 양성 1건(실물 TOC 꼴이 `_NestedRef` 와 같은 블록) ·
     **음성 대조 2건**: ⓐ 산문 속 중첩 링크
     `<p><a>가</a><a>나<a>다</a> 에서 김치찌개를 본다</p>` 는 **안 끊긴다**(천장 ⓐ 계약 ·
     계획 118) ⓑ 숨김 안의 중첩 링크는 경계를 안 세운다(리뷰 115 [R115-2] 의 자리)
  2. 전수 `PYTHONPATH=src scripts/verdict.sh python3 -m unittest discover -b tests` 가
     **OK rc=0** · 건수 939 + 새 건수
  3. **색인 경로 무변경 실측** — 같은 문서에서 `extract_text` 출력이 변경 전후 동일
  4. e2e 18종 `rc=0` (명부는 `docs/project.md`)

### 스텝 2 — 실물 수를 다시 재서 `baselines.md` 에 적는다

- **의존**: 스텝 1 (그 산출물인 파서로 재야 수가 나온다)
- **건드릴 파일**: `docs/baselines.md`
- **완료 기준**:
  1. `PYTHONPATH=src python3 e2e/passage_consume.py` **`rc=0`**(분자 0 · 5.2초)
  2. `PYTHONPATH=src python3 e2e/passage_shapes.py` 의 「덜 끊음」 **0** · 「더 끊음」 **0 유지**
  3. 회귀 둘 — `e2e/passage_eval.py` **100% · p95 500ms 이하** ·
     `e2e/quality_eval.py` **ko·en 둘 다 80% 이상**
  4. `docs/baselines.md` 에 네 수를 변경 전/후로 나란히 적는다

## 하지 않을 것

- **천장 ⓑ(구분자가 낀 연접 · `<a>가</a> | <a>나</a>` · `<br>` · `<img>`)** —
  `extract.py:291` 이 **사람 몫**으로 못박은 축이고 소비 측정도 없다(후보 `[5]`
  `digest.md` 후보 `[5]`「소비 축이 모양 하나만」). 등재문의 「한 계획으로 묶으면 싸다」를 **따르지 않는 이유가 이것**이다
- **`indexer.passages` 의 `score`** — 설계가 벌점 쪽을 고르지 않는 한 안 건드린다
- **`pre` 블록**(후보 `[4]` `digest.md` 후보 `[4]`「`pre` 블록」) — 모양이 다르고 모집단이 따로다
- **`e2e/passage_consume.py` 입구 가드 테스트**(후보 `[6]` `digest.md` 후보 `[6]`「입구 가드 셋」) —
  여는 조건(「CI·예약 작업에 올라 사람이 출력을 안 보는 길」)이 **안 섰다**
- **리팩터링·이름 변경** — `_els` 셋째 칸 계산을 읽기 좋게 고치는 일 포함

## e2e 시나리오 (계획 시점에 확정)

1. 실물 `gnu.org/bulletins/gnustatus-2011-10.html` 를 `software Cflow cflow` 로 물으면
   근거 문단이 TOC 한 줄(`Cflow (http://www.gnu.org/software/cflow)`)이 **아니다**
2. `PYTHONPATH=src python3 e2e/passage_consume.py` 가 `rc=1`(분자 12) → **`rc=0`(분자 0)**
3. 회귀 0 — `passage_eval` 100% · `quality_eval` ko·en 80% 이상 · 「더 끊음」 0
4. 음성 대조가 산다 — 산문 속 중첩 링크는 끊기지 않는다

## 브랜치

`loop/nested-anchor-cut`
