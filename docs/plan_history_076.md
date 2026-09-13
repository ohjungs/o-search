# 계획 101 — e2e 진입점이 듣는 소켓과 파이프를 안 닫는다

- **슬러그**: `e2e-fd-leak`
- **브랜치**: `loop/e2e-fd-leak`
- **출처**: `discover.md` 6순위 — digest `[4]` 「`-b` 는 통과한 테스트가 낸 경고도 삼킨다 —
  초록 실행에서 `DeprecationWarning`·`ResourceWarning` 이 영영 안 보인다」
- **설계**: 있음 (`docs/design_history_076.md`) — 3개 이상 파일에 걸침 · 대안 둘이 갈림

## 문제

반복 586 이 그 digest 항목을 **단위 스위트에서** 처음 열어 `ResourceWarning` 12건을 0으로
만들었다. **e2e 쪽 절반은 아무도 안 쟀다** — 그리고 e2e 는 `-b` 를 안 쓰는데도 안 보인다.
`ResourceWarning` 은 파이썬이 **기본으로 무시**하기 때문이다(`-b` 와 무관한 두 번째 뚜껑).

오늘 처음 벗겨서 쟀다 — `PYTHONWARNINGS=always python3 -W always e2e/<이름>.py` · 18종:

| | 값 |
|---|---|
| 종료 코드 | **18/18 rc=0** (전부 초록이다 — 이것이 요점이다) |
| `ResourceWarning` | **30건 · 18종 중 16종**에서 |
| `DeprecationWarning` | **0건** |
| 새는 곳 | 전부 `e2e/` 하네스. **`src/` 제품 코드 0건** |

`tracemalloc` 으로 할당 지점을 받아 원인이 **둘**로 갈렸다:

1. **듣는 소켓** — `ThreadingHTTPServer` 를 `shutdown()` 만 하고 `server_close()` 를 안 한다.
   `shutdown()` 은 `serve_forever` 루프만 멈추고 **듣는 소켓은 안 닫는다.**
   `e2e/crawl_e2e.py:50` 할당 → `socketserver.py:448` (`self.socket = socket.socket(...)`)
2. **자식 파이프** — `subprocess.Popen(...)` 의 `stdout`/`stderr` `TextIOWrapper` 를 안 닫는다.
   `e2e/noindex_e2e.py:103` 할당 → `subprocess.py:943` (`self.stdout = io.TextIOWrapper(...)`)

## 왜 고치나 — 취향이 아니라 측정값이다

**이 저장소는 이미 셋에서 옳게 하고 있다** — `design_check.py:441-442` ·
`passage_eval.py:248-249` · `perf_search.py:109-110` 이 `shutdown()` **다음에**
`server_close()` 를 부른다. 나머지 17개는 그 한 줄이 없다. **일관성이 아니라 같은 계약을
어긴 것**이고, 옳은 쪽이 이미 저장소 안에 있으니 새로 설계할 것이 없다.

실질 피해: 듣는 소켓이 GC 까지 포트를 붙들고 fd 가 쌓인다. `deadline_e2e` 가 1초 하한에서
간헐로 갈리는 것(digest `[6]`)과 **같은 프로세스 안에서 fd 4~8개를 흘리는 것**이 무관하다고
말할 근거가 지금 없다 — 다만 **이 계획은 그 인과를 주장하지 않는다**(범위 밖 · 아래 참조).

## 범위 — 건드릴 파일

`server_close()` 빠진 곳 **17파일 · 18곳**(`crawl_politeness_e2e` 만 2곳):
`crawl_delay_e2e` `crawl_e2e` `crawl_politeness_e2e` `deadline_e2e` `domain_key_e2e`
`hidden_passage_e2e` `indexer_e2e` `interrupt_e2e` `noindex_e2e` `non_ascii_e2e`
`pagination_ui_e2e` `perf_crawl` `recrawl_e2e` `retry_interval_e2e` `search_api_e2e`
`tokenizer_e2e` `url_normalize_e2e`

`Popen` 파이프 **8곳**: `hidden_passage_e2e:121` `indexer_interrupt_e2e:159`
`interrupt_e2e:132` `noindex_e2e:103` `pagination_ui_e2e:161` `search_api_e2e:103,190`
`tokenizer_e2e:108`

## 하지 않을 것

- **`e2e/` 공용 도우미 모듈을 만들지 않는다.** 설계 2절에서 버린 대안이고, digest 가
  「e2e 도우미 0건(22/22 진입점)」으로 등재한 열리지 않은 문이다. 밤에 22개 진입점의
  구조를 바꾸는 것은 `discover.md` 3절 금지(아키텍처 변경)다
- **`docs/project.md` 의 테스트 명령에 `-W` 판을 더하지 않는다.** 게이트 ⑫ 로 등재된
  사용자 승인 대기 건이다. 이 계획은 **승인이 필요 없는 다른 레버**(소스를 읽는 가드)로 간다
- **`deadline_e2e` 간헐 실패를 고치지 않는다.** 인과가 확인 안 됐다. fd 누수를 0으로
  만든 뒤 그 간헐이 남는지는 e2e phase 에서 **재기만** 한다
- **`src/` 를 안 고친다.** 제품 코드 누수 0건이 오늘 측정됐다

## 스텝

### 스텝 1 — 회귀 가드를 세운다 (의존: 없음)

`tests/test_e2e_fd.py` — `e2e/*.py` 소스를 입력으로 읽어, `HTTPServer` 를 만드는 파일은
`server_close()` 도 부르는지 짝을 맞춘다. `Popen(...)` 에 `stdout=PIPE` 를 준 파일은
파이프를 닫거나 컨텍스트매니저로 감쌌는지 본다.

- **완료 기준**: 새 테스트가 **지금 빨갛다** — 17파일을 이름으로 지목해야 한다.
  전수는 784 + 신규 그대로 OK.

### 스텝 2 — `server_close()` 18곳 (의존: 1)

저장소가 이미 쓰는 패턴(`design_check.py:441-442`)을 그대로 따른다.

- **완료 기준**: 스텝 1 가드 초록 · 전수 OK · `-W always` 18종 재측정에서
  `unclosed <socket.socket` **0건**.

### 스텝 3 — `Popen` 파이프 8곳 (의존: 1)

- **완료 기준**: `-W always` 18종에서 `unclosed file` **0건** · 18/18 rc=0.

### 스텝 4 — 전수 재측정 (의존: 2, 3)

- **완료 기준**: 18종 `ResourceWarning` **0건** · `DeprecationWarning` **0건** ·
  18/18 rc=0 · 단위 전수 OK. 품질 4축 회귀 없음.

**스텝이 4개인 이유**: 가드(1)와 두 누수 계층(2·3)이 각각 되돌릴 수 있는 단위고, 4는
계획 전체의 완료 기준이라 스텝을 더 쪼갤 근거가 없다.
