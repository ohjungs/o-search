---
signal: GREEN
phase: e2e
step: 1
attempt: 0
iteration: 161
updated: 2026-08-30
ctx: 48
night_iterations: 41
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 33 `clock-injection` 리뷰 phase 통과. 1건 — 자동 수정, 테스트 전용.**
단위 **433건 전부 OK** (3.36초, `PYTHONPATH=src python3 -m unittest discover -s tests` — 전체).
이 스텝의 `src` diff **0줄**. 열린 계획 **1** · 보류 패치 0 · RED 0.
`main` 은 `f888518` 그대로 — 병합은 사람 판단 항목이다.

## 리뷰 결과 (`review.md` 5절 형식)

```
리뷰: 1건 (informational 1)

[자동 수정]
- tests/test_crawl.py:1379 계약 클래스가 "기본값으로 새는" 누수를 못 본다
  (mock.patch 는 모듈 속성만 바꾸고 기본값은 def 시점 바인딩)
  → 벽시계 단언 assertLess(elapsed, 0.5) 추가. 변이 M4 가 4.04초로 죽는다

[승인 필요]
- 없음
```

**패스 A(백지)에서 나왔다** — 계획·설계를 열기 전에 diff 만 보고. 배경을 아는 작성자가
"두 대기 자리를 다 지난다" 까지 확인하고 넘어간 자리다(digest `[101]` 이 적어 둔 값).

## 무엇이 문제였나 — 변이 M4

`mock.patch("time.sleep")` 은 `time` **모듈의 속성**을 갈아끼운다. 그런데 기본값
`sleep=time.sleep` 은 **def 시점에 진짜 함수 객체를 붙들고** 있어 그 패치가 안 닿는다.
그래서 주입이 **기본값으로 새면 `call_count` 가 0 그대로**다.

M4 = `crawl.py:171` `pool.submit` 에서 `sleep` 인자만 뺀다(`_fetch_one` 이 기본값 사용).

| 무엇으로 재나 | M4 | 소요 |
|---|---|---|
| `TestSleepIsInjected` — 계약을 자처한 클래스 | **OK, 안 죽는다** | 0.003초 → **4.02초** |
| 전 스위트 | FAILED 7건 | 3초 → **130초** |

**계약이 안 지켜진 게 아니라, 자처한 자리가 아니라 옛 간격 테스트들이 지키고 있었다.**
개발 phase 의 M1·M2·M3 는 전부 **줄을 고치는** 변이라 **인자를 빼는** 갈래가 비어 있었다 —
digest `[7]` 이 "기본값이 있는 인자는 특히 위험하다(0 이 아니다)" 로 미리 적어 둔 자리다.

**고친 것**: 벽시계 단언 한 줄. mock 이 못 보는 것을 시간이 본다. 여유는 양쪽으로
166배(정상 0.003초)·8배(M4 4.04초)다. 판정은 digest `[103]` 대로 2단계 — ① `grep` 으로
변이가 실제로 심겼는지 먼저 확인 ② 새 단언이 죽이는지.

## 크롤 윤리 — `sleep=lambda s: None` 으로 예절을 무력화할 수 있나

**반쪽만 된다.** 실측:

| 자리 | 정상 | `sleep=no-op` | 무엇이 강제하나 |
|---|---|---|---|
| 워커 — 재시도 사이 (`crawl.py:74`) | `[1.005, 1.005]` | **`[0.0, 0.0]`** | `sleep` 이 **유일한** 강제. 뚫린다 |
| 메인 — URL 사이 (`crawl.py:179`) | `[1.001]` | `[1.0]` **지켜짐** | `frontier.next()` 가 `now()` 로 재검사 |

메인 쪽은 뚫리지 않는 대신 **91만 회 공회전**이 된다(벽시계 1.00초에 CPU 1.00초 — 정상은 0.00초).
잠을 없애도 요청이 일찍 나가지는 않고 CPU 만 태운다.

**대조 — 표면은 오히려 좁아졌다.** `now=` 는 **이번 변경 이전부터** 두 자리를 다 뚫는다
(`now` 를 가속하면 간격이 **0.001초**). `sleep=` 이 여는 것은 그 부분집합이다.
**둘 다 CLI 에서 도달 불가**다: `main()` 은 `crawl(args, max_pages, workers=, deadline=)`
만 넘기고, 모르는 `-` 인자는 `unknown` 가드가 rc=2 로 막는다.
`DOMAIN_INTERVAL` 하한(`crawl.py:61`)도 자리·값 그대로다(설계 계약 5).
→ **공개 API 표면이 아니라 인프로세스 이음매다. 신뢰 경계는 안 움직였다.**

## 나머지 렌즈 — 통과

- **렌즈 1 (계획·설계와 대조)** — 설계 계약 6개 전부 지켜졌다. 특히 **5**(`DOMAIN_INTERVAL`
  하한을 자리도 값도 안 건드린다)와 **6**(간격 기대값 `[1.0]`·`[5.0]`·`[1.0, 1.0]` 무변경)은
  `git diff` 에 아예 안 나온다 = 안 건드렸다. 계약 1(뒤에 붙이기)·2(둘이 같은 하나를 쓴다)도 맞다.
- **렌즈 4 (범위)** — `src` diff 는 시그니처 2줄·호출 2줄·독스트링 1줄이 전부다.
  직교 편집 0. `grep -rn 'time\.sleep' src/websearch/*.py` = **기본값 2곳뿐, 호출 0곳**.
- **직전 스텝이 리뷰에 넘긴 물음** — `e2e/` 의 `crawl.crawl()` 호출 **5곳**(4파일:
  `domain_key_e2e`·`retry_interval_e2e`·`url_normalize_e2e`·`crawl_politeness_e2e`×2)이
  `sleep=` 을 안 넘기는 것이 의도인가 → **의도다.** e2e 는 실시계로 예절을 재는 자리라
  진짜로 자야 한다. 실제로 `crawl_politeness_e2e` 는 벽시계 간격을 단언한다.
- **QA — 열거형 완전성** — 새 열거값·상태 문자열이 없다(인자 하나 추가). 해당 없음.
- **릴리스/SRE** — 되돌리기는 그대로 성립한다: 아무도 `sleep=` 을 안 넘기면 기본값이
  진짜 `time.sleep` 이라 오늘과 동일하게 돈다(`test_default_sleep_is_the_real_one` 이 고정).
  제품과 테스트를 따로 무를 수 있다. 배포 표면 변화 0 — CLI 인자·출력·rc 모두 무변경.

## 남은 갭 (8 미만 — `digest.md` 로)

- **[6] `_fetch_one` 의 위치 인자 순서를 지키는 단언이 없다.** `crawl.py:171` 은 `sleep`
  을 5번째 **위치**로 넘기는데(`pool.submit`) 테스트 7곳은 키워드로 부른다. 순서를
  뒤집으면 `sleep(remaining)` 이 float 호출이 돼 요란하게 죽으므로 조용한 회귀는 아니다.
  다만 **`floor` 와 `sleep` 사이에 인자가 하나 끼면** 조용해진다 — 이번 M4 와 같은 부류다.
- **[5] `sleep=no-op` 일 때 메인 루프가 91만 회 공회전한다.** 예절은 지켜지므로 버그가
  아니고, CLI 에서 도달 불가라 실물에 안 나온다. 중단 신호 계획이 `Event.wait` 로
  이 자리를 바꿀 때 같이 사라진다 — 그때 다시 본다.

## 다음에 할 것 — e2e phase (이 스텝에서는 안 넘어갔다)

**e2e 는 "달라진 게 없다" 를 증명하는 자리다.** 겉보기 동작이 안 바뀌는 계획이라
e2e 가 유일한 실제 증거다. 17종 전수로 판정한다 — `PYTHONPATH=src python3 e2e/<이름>.py`.
직접 표적 3종은 앞선 스텝들에서 이미 rc=0 을 봤다(`crawl_delay_e2e`·`deadline_e2e`·`perf_crawl`).

## (아카이브) 테스트 phase 관문 — 상세는 `history_current.md` 04:2x

관문 1(낮춘 단언) **없다** — `git diff de28dfb -- tests/test_crawl.py | grep -cE '^-.*assert'`
= `0`, 431→433 은 삭제 0 · 신규 2. 관문 2(빠뜨린 것) 갭 1건(중요도 8, 메인 쪽 대기
커버리지)을 그 자리에서 닫았다.

<details><summary>당시 근거 전문</summary>

### 관문 1 — 단언을 낮춰 통과시킨 곳이 있나 (`test.md` 6절) → **없다**

`git diff de28dfb..HEAD -- tests/test_crawl.py` 를 한 줄씩 봤다(+77/-32).
**기계로도 셌다 — `git diff de28dfb -- tests/test_crawl.py | grep -cE '^-.*assert'`
가 `0` 이다.** 지워진 단언 줄이 한 줄도 없다는 뜻이고, `+` 쪽 `assert` 3줄은
전부 새 `TestSleepIsInjected` 안에 있다. 바뀐 것은 기존 8개 헬퍼에서
아래 두 줄짜리 치환이 반복된 것뿐이다.

```diff
-             mock.patch("websearch.crawl.time.sleep") as ms, \
-            ms.side_effect = lambda s: clock.__setitem__("t", clock["t"] + s)
+            ms = mock.Mock(side_effect=lambda s: clock.__setitem__("t", clock["t"] + s))
-                        now=lambda: clock["t"], workers=8)
+                        now=lambda: clock["t"], workers=8, sleep=ms)
```

계획이 "고치면 멈춘다" 고 못 박은 기대값 셋이 diff 에 **없다**(= 안 건드렸다):
`[1.0]`(`test_retries_are_spaced_by_the_domain_interval`) ·
`[5.0]`(`Crawl-delay` 계열) · `[1.0, 1.0]`(재시도 2회).
`assertGreaterEqual(sent[1] - sent[0], 1.0)`·`assertGreaterEqual(gap, 5.0)`·
`assertEqual(self._elapsed(ms), 3.0/8.0)` 도 전부 원문 그대로다.

건수도 낮춘 게 아니다 — 431→433 의 +2 는 **삭제 0 · 신규 2**(`TestSleepIsInjected`)다.
`ms` 를 평범한 함수가 아니라 `mock.Mock` 으로 둔 것은 단언을 **살리기 위해서**다:
`TestDeadline._elapsed` 가 `ms.call_args_list` 로 흐른 시간을 재기 때문이다(`:1228`).

`src` 쪽도 확인했다 — `crawl.py` diff 는 시그니처 2줄·호출 2줄·독스트링 1줄이 전부고
`grep -rn 'time\.sleep' src/websearch/*.py` 는 **기본값 2곳뿐, 호출 0곳**이다.

### 관문 2 — 빠뜨린 것 (`test.md` 3절) → 카테고리 ⑤ 에서 1건, 중요도 8, 닫았다

**갭**: `test_injected_sleep_is_the_only_one_used` 가 **워커 쪽 대기(`crawl.py:74`)만**
지났다. 자기 독스트링이 "시드 하나·링크 없음이라 메인 쪽 대기는 지나지 않는다" 고
스스로 적어 두고 있었다. 즉 계획 33 의 핵심 계약("전역 `time.sleep` 0회")이 **두 대기
자리 중 한 곳에서만 단언되고 있었다.**

메인 쪽(`crawl.py:179`)이 전역으로 되돌아가면 가짜 시계가 안 흘러 **행**으로 잡히긴
한다(변이 M2, rc=124). 하지만 그것은 *시계에 의존하는* 대기일 때뿐이다.
누가 메인 루프에 **고정 대기**(`time.sleep(0.1)` 같은 백오프)를 새로 심으면 행도
안 나고 빨개지지도 않는다 — 스위트 전체에 진짜 대기가 조용히 돌아온다.
계획 33 이 존재하는 이유가 바로 그것이라 **8** 로 매겼다.

**고친 것**: 새 테스트를 만들지 않고 그 테스트의 시나리오만 두 줄 넓혔다 —
시드를 같은 도메인의 URL 둘로 바꾸니 첫 URL 뒤 쿨다운에서 `frontier.next()` 가
None 을 돌려주고(`frontier.py:82`) 메인 루프가 `:179` 로 들어간다. 단언은 그대로다.

**커버리지를 실측으로 증명했다** — `:179` 바로 뒤에 `time.sleep(0)` 을 심고(행이 안
나는 전역 호출) 두 판본을 같은 변이 위에서 돌렸다:

| 테스트 판본 | 변이 심은 뒤 | 뜻 |
|---|---|---|
| 옛 판본(시드 1개) | **OK** (rc=0) | 갭이 실재했다 — 못 잡는다 |
| 새 판본(같은 도메인 2개) | **FAILED** (rc=1, `전역 time.sleep 이 1번 불렸다`) | 갭이 닫혔다 |

변이 회수 후 `grep -c MUT src/websearch/crawl.py` **0** · `git status` 로 `src` 가
깨끗함을 확인했다. 그 스텝의 `src` diff 는 **0줄**, `tests` diff 는 **+8/-4**.

</details>

## 아직 남은 후보 (반복 152 분류 그대로)

**(a) 사람 승인 대기 — 무인 모드가 손대지 않는다**
`[8]` indexer 증분이 갱신을 반영 안 함(**스키마 변경**) · `[high]` `store.has` 상태
불문 스킵 재크롤 정책(**사람 판단**) · URL userinfo 가 `pages.url` PK 로 렌더됨
(**보안 경계**) · `[5]` `X-Robots-Tag` http-equiv(**스키마**) · `loop/*` 병합 여부.

**(b) 도달 불가 — 고치면 오히려 정상값을 거절한다**
`[4]` `int_max_str_digits`(3.9.6) · `[4]` `quality_eval` `limit=100`(실물 최대 28건) ·
`[4]` `fixture_defects` 의 `ja`(코퍼스 동결).

**(c) 정식 계획 크기** — ~~`[6]` 가짜 시계 이음매 9곳~~ = **계획 33 이 지금 닫는 중** ·
`[4]` pop 시각 간격 · `[7]` OFFSET 드리프트.

## 한도 (안 넘는다)

`data/crawl.db` 실물 · URL 은 `pages.url` PK · CI 90초 · `docs/specs/` 의 4축.
