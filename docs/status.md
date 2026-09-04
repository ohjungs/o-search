---
signal: DONE
phase: e2e
step: 5
attempt: 0
iteration: 302
updated: 2026-09-04
ctx: 38
night_iterations: 130
night_red: 2
night_retries: 0
plan: null
---

# 현재 상태

**계획 51 `hidden-passage` 완료.** e2e 통과 · 계획·설계 아카이브(`plan_history_037.md` ·
`design_history_037.md`) · `index.md` 51번 줄 **완료** · `plan: null`. 다음 계획 없음.
**새 파일은 e2e 1개**(`e2e/hidden_passage_e2e.py`) · 제품 `src/` **0줄**.

## 재본 것 — 프로세스 밖 사용자 자리

계획·설계가 잰 5/5 → 0/5 는 `indexer.passages()` 를 같은 프로세스에서 부른 값이다.
새 e2e 는 crawl 로 HTML 을 받아 색인하고 **README 그대로** 서버를 띄워 `GET /passages`
를 HTTP 로 때린다(11문서 · 12.5초). 그 형태에서도 **누출 0/5** · 정상 문단 **5/5 무변** ·
오탐 대조군 4종 **전부 살아 있다**. 숨김만 매치한 문서는 `/search` 결과에 **그대로
나온다** — 색인 경로가 안 움직인 증거. `extract_text` 무변은 논증이 아니라 **비교**로
닫았다(기점 `d5367fa` 의 `extract.py` 를 적재해 11개 입력에서 **차이 0건**).
`data/crawl.db` sha256 `85c96744…75bda18` 시작·끝 동일 — 읽기만 했다.

## 신호는 GREEN

단위 **593건 OK** rc 0(맨몸·단독 13.614초) · e2e **21종 rc 0**(20 + 새 1) ·
품질 5축 전부 통과·무변(ko 20/20 · en 19/20 · 근거 100.0% · `/passages` p95 1.49ms ·
`/search` p95 8.94ms · 수집 10.22/10.26 · 디자인 4축) · RED 0 · 재시도 0.
변이 **4종(좁힘 2 · 넓힘 2) 전부 사망** — 상세는 `docs/e2e/hidden-passage/result.md`.
러너 호출 **31회 · 명령 잇기 0 · 출력 조작 0**.

## 배운 것

**변이 하나가 fixture 항목 하나에만 닿게 자른다** — 오탐 대조군 3종을 한 문서에 몰아
뒀더니 하나가 죽어도 남은 둘이 대신 뽑혀 자가 안 섰다(M3 생존 → 문서당 문단 1개로 분리).
**`PASSAGE_LIMIT`(10)이 fixture 의 상한이다** — 넘기니 밀려난 문서가 「잘렸다」와 구별이
안 돼 거짓 빨강을 한 번 봤다. 모듈 최상단 `assert` 로 못 박았다(`metrics.md` 다섯째 축).

## 문서

`metrics.md`(반복 302 · e2e 28 · 계획 36/0/0) · `index.md`(51번 줄 완료) ·
`history_current.md`(308줄이 되어 회전 — 테스트 3을 `history_053.md` 로 밀어 **229줄**) ·
`digest.md`(**200줄 유지** · 명부에 `history_053.md`) · `docs/e2e/hidden-passage/result.md`
신규 · `README.md`·`project.md` 는 e2e 등재분만. `docs/specs/` **무변**.

## 원격 — 푸시 뒤에 다시 읽은 값이다

- **`loop/hidden-passage` = `2fde651`**(e2e 커밋 · `82cc84e` → `2fde651`, fast-forward).
  `git ls-remote origin loop/hidden-passage` 의 `2fde6518…3b010b0a` 와 로컬 `HEAD` 가 같다.
  `--no-verify`·`--force` 0회 · 훅 우회 0.
- 기점은 `d5367fa`(**`main` 아님**) — `origin/main`(`687a159`)에는 계획 48·49·50 이 없어
  `README.md` 의 건수 단언이 거기서는 RED 다.
- **PR #7**(`loop/merge-48-50` → `main`, 계획 48·49·50) **OPEN·미병합.** 병합은
  **사용자가 처리한다** — 이 반복은 PR 을 열지도 닫지도, 그 브랜치를 건드리지도 않았다.
  이번 브랜치의 PR 도 만들지 않았다(아래 「승인 대기」 5).

## 승인 대기

1. **`--line` 이 SC 1.4.11 대상인가**(라이트 1.34:1 · 다크 1.27:1).
2. **`--focus` 가 `--bg-button` 위에서 1.45:1**(다크 1.66:1) — `outline-offset` 0 일 때만.
3. **반응형 360px 미검증** — 브라우저가 없어 저장소의 누구도 그 화면을 못 그린다.
4. **회전 규약·러너 규율의 저장소 밖 절반**과 **사양이 남긴 둘**(`specs/concept.md` 의
   `## 사람이 정할 것`).
5. **PR #7 병합** · 이번 브랜치 `loop/hidden-passage` 의 PR 생성 여부.
