---
signal: GREEN
phase: e2e
step: 1
attempt: 0
iteration: 207
updated: 2026-09-01
ctx: 55
night_iterations: 70
night_red: 0
night_retries: 0
---

# 현재 상태

**계획 41 `crawl-db-guard` 리뷰 1/1 완료 — 판정 머지 가능. 제품 수정 0줄.**
설계서 `docs/design_crawl-db-guard.md` · 계획서 `docs/plan_crawl-db-guard.md`
세 커밋(`ccb5932` 설계 · `1b7b9c4` 개발 · `b490d7c` 테스트)을 백지 → 대조 두 패스로 읽었다.
다음은 e2e 1스텝. 통과하면 계획 41 DONE.

## 방금 것 (2026-09-01 · 리뷰 1/1 · 반복 207)

### ① 패스 A(백지) — 막는 지적 0건

제품 실질 8줄을 diff 만 보고 읽었다. 확인한 것 넷:
`except (sqlite3.Error, OSError)` 는 **`Store(db_path)` 한 줄만** 덮고 `sqlite3.Error` 는
`OSError` 의 하위가 아니라 겹침이 없다 · 둘 다 `Exception` 하위라 `KeyboardInterrupt`
(=`BaseException`)를 **안 삼킨다**(rc 130 계약 무사) · `StoreOpenError` 가
`NoUsableSeedsError`(=`ValueError`)와 **상속이 안 겹쳐** `main` 의 except 순서에 안 걸린다 ·
`finally` 의 시그널 복구가 새 갈래도 지난다. `Store(` 호출은 `src` 전수 **한 곳**
(`crawl.py:176`)이라 열거 누락 없다.

**rc 는 한 값도 안 바뀌었다** — 전에도 안 잡힌 예외를 파이썬이 1 로 끝냈다.
바뀐 것은 stderr 의 **모양뿐**이다(14~16줄 → 1줄). 되돌리기는 커밋 하나 revert.

### ② 버린 지적 1건 (80점 미만) — 락 갈래의 문구

`indexer` 는 락을 갈라 다른 문장을 낸다(`indexer.py:262` *"DB 가 잠겨 있다"*).
`crawl` 은 안 가르므로 **락일 때만 두 CLI 의 화면이 갈린다.** 다만 코드 주석이 약속한
것은 `indexer.py:264` **그 줄과 같다** 이고 그건 항상 참이다. 설계 물음 3 이 이미
근거(검사 하나가 30.6초)와 **여는 조건**(`Store` 의 timeout 을 손대는 계획)까지 적어 뒀다 —
기보류 중복이라 버렸다. `digest` 항목을 안 열었다(열린 항목 50 유지).

### ③ 앞 스텝이 넘긴 둘은 이미 기록돼 있었다

변이 절차 결함("되돌리지 않은 변이가 다음 변이를 살려 놨다")은 `digest.md:155` 의
`[8]` 이 **2회**로 흡수했고(심겼는가 ↔ 되돌려졌는가), 파이프는 `## 반복 실패` **7회**
⑦로 들어가 있다. 리뷰가 더할 것이 없었다 — **테스트 phase 가 자기 결함을 자기 손으로
적은 첫 사례**다.

### ④ 숫자 대조 — 어긋난 것 0

`README` 건수 줄 466 은 `test_readme.py::test_verification_counts_match_reality` 가
`discover` 로 **직접 세어** 초록이다(손으로 적은 숫자가 아니다). `index.md` 41 행 `1/1` =
개발 커밋 1개 · `metrics.md` 반복 206 = `status.md` 206 — `## 반복 실패` 가 4회 적은
어긋남이 이번엔 없다. `history_017.md` 169줄 ↔ `digest.md:66` 의 016·017 회전 줄 대응 OK.

**검증**: 단위 **466건 OK 11.887초**(맨몸 실행, 파이프 0) · `data/crawl.db` sha256
**무변경**(`85c96744…5bda18`) · `digest.md` 50항목 200줄 · `history_current.md` 164줄.

## 다음 스텝 (e2e 1)

설계가 **새 e2e 0개**로 확정했다 — 재는 것이 `main(argv)` 의 반환값과 stderr 이고 다섯
상황이 전부 `tempfile` 로 선다. 그러니 e2e 스텝은 **회귀 전수**다: `e2e/*.py` 19종이
rc 0 인가, 그중 `crawl()` 을 직접 부르는 12개 시나리오가 새 예외로 안 깨지는가.
통과하면 계획 41 DONE — `index.md` 41 행 완료 · `digest` `[6]` 닫아 **49** · `metrics` 마감.

## 한도 (넘으면 RED)

- `data/crawl.db` 실물·스키마 무변경 (sha256 `85c96744…5bda18` — 반복 207 에서 대조함).
- **e2e 는 임시 디렉터리에서만, `cwd` 도 거기다** — `crawl` 은 `cwd` 밑에 `data/` 를 만든다.
- 단위 **466건**이 기준선(11.9초). 466 미만이면 RED · e2e **19종**이 줄면 RED.
- `docs/digest.md` 열린 항목 **50**(`grep -c '^- \['`) — DONE 때만 `[6]` 을 닫아 49.
  **200줄 상한**이다. 항목을 더하려면 먼저 압축한다.
- 제품 diff 는 **0줄**이다. e2e 가 제품을 고쳐야 하면 그건 RED 이지 e2e 스텝이 아니다.
- **러너를 파이프로 감싸지 않는다**(`## 반복 실패` **7회**. 방아쇠가 매번 다르다:
  망각 → 재확인 → "사본이라 가벼운 실행". 백그라운드 태스크도 같은 변종이다).
- 의존성 추가 금지(stdlib 만) · `docs/specs/` 읽기만 · `--no-verify` 금지 ·
  `main` 직접 커밋 금지 · 외부 네트워크 금지 · 도메인당 요청 간격 1초 이상 · robots 준수.
