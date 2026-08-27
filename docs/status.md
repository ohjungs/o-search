---
signal: GREEN
mode: night
plan: -
phase: 계획
step: 0/0
attempt: 0
iteration: 101
night_iterations: 12
night_red: 0
night_retries: 0
updated: 2026-08-27 (반복 101 · 계획 015 DONE)
ctx: 68% / 200k
rules: 1411a37
---

# 현재 상태

**계획 015 `pagination-ui` 를 닫았다.** 다음 계획을 열 차례다.

## 직전 계획 (015 `pagination-ui`) — DONE

**서버는 진작부터 2페이지를 줄 수 있었다.** `?q=X&page=2` 를 손으로 치면 나왔다 —
없던 것은 **화면에 그려진 길**이었다. JSON 경로가 이미 쓰던 탐침 한 줄
(`limit=PAGE_SIZE + 1`)을 `_page_hits`·`_has_next` **한 벌**로 뽑아 두 경로가 나눠 쓴다.
COUNT 를 안 더하므로 p95 에 얹히는 것이 없고(9.22ms), 총 건수를 모르니 **번호 목록도
안 그린다**. 단위 **311건** · e2e 4/4 · `design_check` 0(JS 0B 유지).
기록은 `docs/e2e/pagination-ui/result.md` · `plan_history_013.md` · `index.md` 15번.

**남긴 교훈 둘:**
- **`if __name__ == "__main__"` 뒤에 클래스를 붙이면 그 테스트는 존재하지 않는다.**
  직접 실행 55건 · `discover` 70건 — **양쪽 다 초록**이라 사라진 신호가 없었다.
  백지 리뷰가 아니었으면 못 봤다 (digest `[7]`)
- **측정 불능(2)과 빨강(1)을 안 가르면 회귀가 "못 쟀다" 로 보고된다.** e2e 첫 판은
  링크 개수를 가드에 넣어 **기능 삭제와 문서 부족이 같은 코드 2**로 나왔다. 갈 곳이
  있는지는 화면이 아니라 **독립된 계측기**(JSON API)로 먼저 묻는다

## 다음 계획 (후보)

1. `digest.md ## 판단 필요` 의 `[5]` — **재시도 간격이 스킴별 robots 만 본다.**
   `Frontier.interval(domain)` 공개 읽기를 내고 `_fetch_one` 이 둘의 `max` 를 쓴다.
   실측: `http` 만 `Crawl-delay: 5` 일 때 URL 사이는 5.000초인데 `https` 재시도는 1.000초.
   작고(계획 014 가 파일 목록 밖이라 미뤘다), **컨셉 1순위(크롤 윤리)** 축이다
2. `docs/index.md` 사양 분할의 남은 항목 — 색인 규모는 운영 측정 대기

## 열지 않는 것

recrawl(`store.has` 상태 불문 스킵 · indexer 증분) · `X-Robots-Tag` · `loop/*` 병합.
