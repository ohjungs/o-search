---
signal: GREEN
phase: 리뷰
step: 1
attempt: 0
iteration: 160
updated: 2026-08-30
ctx: 51
night_iterations: 40
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 33 `clock-injection` 테스트 phase 통과. 낮춘 단언은 없었다.**
단위 **433건 전부 OK** (2.93초, `PYTHONPATH=src python3 -m unittest discover -s tests` — 전체).
갭 하나(중요도 8)를 찾아 그 자리에서 닫았다. 열린 계획 **1** · 보류 패치 0 · RED 0.
`main` 은 `f888518` 그대로 — 병합은 사람 판단 항목이다.

## 관문 1 — 단언을 낮춰 통과시킨 곳이 있나 (`test.md` 6절) → **없다**

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

## 관문 2 — 빠뜨린 것 (`test.md` 3절) → 카테고리 ⑤ 에서 1건, 중요도 8, 닫았다

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
깨끗함을 확인했다. 이번 스텝의 `src` diff 는 **0줄**, `tests` diff 는 **+8/-4**.

## 남은 갭 (8 미만 — `digest.md` 로)

- **[6] `_fetch_one` 의 위치 인자 순서를 지키는 단언이 없다.** `crawl.py:170` 은 `sleep`
  을 5번째 위치로 넘기는데(`pool.submit`), 테스트 7곳은 키워드로 부른다. 다만 순서를
  뒤집으면 `sleep(remaining)` 이 float 호출이 돼 요란하게 죽으므로 조용한 회귀는 아니다.
- **[5] `test_default_sleep_is_the_real_one` 은 기본값만 본다.** "안 넘겼을 때 실제로
  전역을 부른다" 까지는 안 본다 — 부르면 진짜로 자야 해서 단위에서 잴 자리가 아니다.

## 다음에 할 것 — 리뷰 phase

리팩터링이라 볼 것이 좁다: `crawl()`·`_fetch_one()` 시그니처가 공개 인터페이스인데
`e2e/` 의 `crawl.crawl()` 호출 5곳(파일 4개: `domain_key_e2e`·`retry_interval_e2e`·
`url_normalize_e2e`·`crawl_politeness_e2e`×2)은 `sleep=` 을 안 넘긴다 — **그것이 맞다**(진짜로 자야 한다).
리뷰가 볼 것은 그 "안 넘김" 이 의도인지 누락인지 구분되게 적혀 있는가다.

**e2e 는 "달라진 게 없다" 를 증명하는 자리다.** 이번 스텝에 대표 3종을 미리 돌려
전부 rc=0 임은 봤다(`crawl_delay_e2e` · `deadline_e2e` · `perf_crawl`).
e2e phase 에서 17종 전수로 다시 판정한다.

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
