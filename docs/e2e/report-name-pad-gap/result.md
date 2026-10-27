# e2e 결과 — 계획 125 `report-name-pad-gap`

**날짜**: 2026-10-28 (반복 771) · **브랜치** `loop/report-name-pad-gap` (`a9a7a28`) · **무인(night)**
**종합**: 🟢 **통과** — 시나리오 **4/4** · 반사실을 **깨끗한 사본에 실제로 심어** 돌렸다(픽스처가 아니다).

## 0. e2e 앞의 두 관문

| 관문 | 결과 |
|---|---|
| 전수(전체) | `PYTHONPATH=src scripts/verdict.sh python3 -m unittest discover -b tests` → **998 OK rc=0** |
| 린트·타입체크 | **없다**(`project.md` — 「검증되지 않았다」로 적는다, 통과라고 쓰지 않는다) |
| CI | 확인 명령 없음(혼자 쓰는 저장소 · `project.md` 브랜치 절) |
| 품질 축(품질·성능·디자인) | **안 돌렸다 — 제품 `src/` 0줄**이다(`git diff main...HEAD -- src/` **빈 출력**). 계획서 「측정하지 않는 것」 그대로 |
| e2e 18종 | **전부 rc=0** (명부는 `project.md` · 로그는 아래 4절) |

## 1. 사본이 먼저다 — 계획 122 가 죽은 자리를 센다

이 계획의 **살아 있는 축**은 `docs/reports/` 를 읽는다. 그 디렉터리는 `.gitignore:2` 에 있고
`git ls-files -- docs/reports` 가 **0건**이다 — 계획 122 가 e2e 에서 보류된 바로 그 구조고
(게이트 ⑱) 사람이 2026-10-26 에 **㉢**(기계 로컬 가드 + `skipTest`)로 닫았다.

| 센 것 | 수 |
|---|---|
| `git ls-files -- docs/reports` | **0** |
| `git ls-files -- docs/index.md` · `docs/status.md` | **1** · **1** |
| `git archive HEAD` 사본 전수 | **998 OK (skipped=2)** |
| 건너뛴 2건 | `NightReportSignalTest.test_the_latest_report_carries_a_signal_row` · `ReportNameTest.test_every_live_report_name_carries_a_date` — **둘 다 사유가 `docs/reports/ 없음 — 기계 로컬 가드`** |

**새 차단이 아니다.** 122 는 사본에서 **거짓 RED** 였고(건너뛰는 길이 없었다), 이쪽은 사람이
고른 ㉢ 의 꼴을 그대로 써서 **건너뛴다**. 그래서 병합을 막는 것이 없다 — 다만 이 가드의
실물 축은 **이 기계 전용**이라는 사실을 여기 적어 둔다(백지 패스도 같은 결론을 냈다).

## 2. 반사실 넷 — 사본의 `docs/reports/` 를 실제로 만들어 심었다

스크립트: `/tmp/e2e-rnpg-scenarios2.sh`(일회용 · 커밋하지 않는다) · 사본 `/tmp/e2e-rnpg.zJ8P`

**1판은 버렸고 그 이유를 적는다** — 심은 보고서를 **전부 ⚪** 로 만들었더니 그중 최신이
핀(`8e56457` · 2026-10-24)보다 미래라 `pin_rot_gap` 이 **옳게** 빨개져 이름 축의 신호와
섞였다. 2판은 마지막 하나를 **🟢**(핀과 같은 날)로 심어 핀 축을 조용하게 만든 뒤 이름 축만 읽는다.

| # | 심은 것 | 기대 | 실측 |
|---|---|---|---|
| ⓐ | `night_2026-10-05.md`(⚪) + **`night_2026-10-5.md`**(⚪) + `night_2026-10-24.md`(🟢) | 빨강 | **`ReportNameTest` 빨강 + `NightReportSignalTest` 빨강** — 패딩 빠진 이름이 사전순 **마지막**이라(`…10-5` > `…10-24`) 둘이 중복 신고한다 |
| ⓑ | **`night_2026-10-055.md`**(⚪) + `night_2026-10-24.md`(🟢) | 빨강 | **`ReportNameTest` 만 빨강** — 흘러넘친 이름이 사전순 **중간**이라(`…10-055` < `…10-24`) 최신-하나 축은 조용하다. **리뷰 [R125-2] 가 찾은 자리고, 고치기 전에는 이 이름이 세 자 전부에서 `2026-10-05` 로 읽혔다** |
| ⓒ | `night_2026-09-09.md` + **`night_2026-09-09_iter-third-witness.md`**(실물 접미사 꼴) + `night_2026-10-24.md` | **조용** | **OK** — 접미사 허용이 지켜진다(오탐 축) |
| ⓓ | **`night_2026-10-5.md`**(⚪) + `night_2026-11-01.md`(🟢) | 한쪽만 빨강 | 최신-하나 축(계획 122) **OK** · 새 축(계획 125) **빨강**. **두 자의 차이를 실물로 보인 것이 이 계획의 근거다** |

ⓐ 와 ⓓ 의 차이가 요점이다 — **같은 패딩 결손이 사전순 위치에 따라 잡히기도, 안 잡히기도 한다.**
계획 122 의 축은 「최신 하나」라 그 위치에 걸려 있고, 새 축은 **전수를 본다.**

## 3. 오늘 트리

| 센 것 | 값 |
|---|---|
| 전수 | **998 OK rc=0** (990 → 997(개발) → 998(리뷰 [R125-2] 의 못 하나)) |
| 제품 `src/` | **0줄** (`git diff main...HEAD -- src/` 빈 출력) |
| 고친 파일 | `tests/test_docs.py` · `README.md`(단위 수 가드가 **기계적으로 강제** · 990 → 998) |
| 실물 보고서 | **45건 · 이름 결손 0건** — 그래서 살아 있는 축은 오늘 초록이고, 이 계획이 닫은 것은 **열린 구멍**이다 |
| 변이 | **누적 8판 중 7 죽음 · 1 등가**(`match`→`search` 는 `^` 앵커가 있어 진짜 등가) |

## 4. e2e 18종

`PYTHONPATH=src python3 e2e/<이름>.py` — **18/18 rc=0**
(`crawl_e2e` `indexer_e2e` `noindex_e2e` `search_api_e2e` `crawl_delay_e2e` `non_ascii_e2e`
`hidden_passage_e2e` `design_check` `tokenizer_e2e` `domain_key_e2e` `deadline_e2e`
`interrupt_e2e` `indexer_interrupt_e2e` `crawl_politeness_e2e` `pagination_ui_e2e`
`recrawl_e2e` `retry_interval_e2e` `url_normalize_e2e`)

## 5. 천장 — 이 자가 못 보는 것

1. **실물 축은 이 기계 전용이다.** 다른 체크아웃에선 `skipTest` 로 빠지고 합성 픽스처 7건만
   남는다. 사람이 ㉢ 으로 고른 결과이지 이 계획의 선택이 아니다.
2. **「입구에서 막는다」가 아니라 「병행 신고」다.** 호출자가 제 테스트뿐이라 `PinRotTest` 만
   따로 돌리면 거짓 초록이 유지된다 — 전수가 관문이라는 전제에 기대 있다(리뷰 [R125-1]).
3. **날짜의 「값」은 안 본다.** `night_2026-13-45.md` 는 꼴이 맞아 통과한다(실물 0건).
4. **`\d` 가 유니코드다.** 전각 숫자 이름은 통과하고 `pin_rot_gap` 이 **거짓 RED** 를 낸다 —
   `digest.md` 후보 `[3]` 으로 등재했다(시끄럽게 틀리므로 조용한 초록이 아니다).
