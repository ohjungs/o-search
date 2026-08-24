# 계획: noindex-respect — noindex 선언 문서를 색인하지 않는다

- **슬러그**: `noindex-respect`
- **브랜치**: `loop/noindex-respect`
- **근거**: `docs/digest.md` 보류 [85·높음] — 2026-08-25 indexer 리뷰가 실측으로 남김
  ("noindex 선언 페이지가 그대로 색인돼 검색 결과 1위"). 저장소 전체에
  `noindex`/`X-Robots-Tag` 문자열이 아직 한 번도 등장하지 않는다.
- **시작**: 2026-08-25 (야간 반복 20)

## 문제 재진술 <!-- 카파시 1번 -->

- **문제**: `src/websearch/indexer.py:22-30` 의 `index_pages()` 는 `pages.html` 이
  NULL 이 아닌 모든 행을 무조건 FTS5 `docs` 테이블에 넣는다. 문서가
  `<meta name="robots" content="noindex">` 로 색인 거부를 선언해도 색인된다.
  `docs/specs/concept.md` 의 갈림길 우선순위에서 **크롤 윤리가 1순위**이고,
  공개 검색엔진에서 noindex 무시는 robots.txt 무시와 같은 축이다.
- **목표**: noindex 를 선언한 문서는 색인에 들어가지 않고, 이미 색인된 것이
  있으면 다음 색인 실행에서 색인에서 빠진다.
- **기대 결과**: noindex 페이지를 크롤한 DB 에 `python3 -m websearch.indexer <db>`
  를 돌려도 그 URL 은 `--query` 결과에 절대 나오지 않는다. 기존 71건 회귀 없음.
- **명시하는 가정**: 판단 근거는 `pages.html` 안의 HTML 뿐이다. HTTP 응답 헤더
  (`X-Robots-Tag`)는 `src/websearch/fetcher.py:13-17` 의 `FetchResult` 가
  헤더를 버리고 `src/websearch/store.py:5-12` 의 `pages` 스키마에도 자리가 없어
  **지금은 판단 자체가 불가능하다**(아래 "하지 않을 것" 참조).

## 하지 않을 것 <!-- 범위 고정, 카파시 3번 -->

- **`X-Robots-Tag` HTTP 헤더** — `FetchResult` 필드 추가 + `pages` 스키마 변경이
  필요하다. 스키마 변경은 야간 무인 모드가 손대지 않는 항목이라 보류하고
  `digest.md` 후보로 남긴다. 이 계획은 HTML 안의 meta 만 본다.
- **`nofollow` / 링크 추적 중단** — 색인이 아니라 크롤 경로의 문제다.
  `crawl.py` 를 건드리게 되므로 별도 계획(`digest.md` 후보).
- **`googlebot` 등 봇 이름별 meta** — 이 프로젝트의 UA 는 자기 이름을 쓰므로
  `name="robots"` 만 본다.
- **증분이 갱신을 반영하지 않는 문제**([8], `digest.md` 판단 필요) — 별개 사안.
  단 "이미 색인된 noindex 문서를 빼는" 경로는 이 계획 안에서 닫는다.
- **robots.txt 처리** — 이미 `src/websearch/robots.py` 에서 동작한다. 안 건드린다.

## 설계 <!-- 6-1 판단 -->

- **필요** → `docs/design_noindex-respect.md`
  - 트리거 ①: **대안이 2개 이상 갈린다** — (A) 색인 시점에 `pages.html` 을 보고
    거르기 / (B) 수집 시점에 아예 저장하지 않기. 둘 다 동작하지만 결과가 다르다
    (B 는 스키마·크롤 경로를 건드리고 재판정이 불가능해진다).
  - 트리거 ②: **공개 인터페이스 추가** — `extract` 모듈에 판정 함수가 하나 는다.
  - 설계에서 결정할 것: 판정 함수의 시그니처와 위치, 이미 색인된 문서를 빼는
    방식(매 실행 전수 재판정 vs 값싼 사전 필터), 그 선택의 성능 천장.

## 스텝

### 1. noindex 판정 함수
- **완료 기준**: 새 테스트가 먼저 실패하는 것을 확인한 뒤 통과. 케이스 —
  ① `<meta name="robots" content="noindex">` → 참
  ② `content="none"` → 참
  ③ `content="NOINDEX, NOFOLLOW"`(대소문자·공백·쉼표) → 참
  ④ `content="index,follow"` / meta 없음 → 거짓
  ⑤ `name="googlebot"` 처럼 다른 이름 → 거짓
  ⑥ 본문 텍스트에 "noindex" 라는 낱말만 있는 문서 → 거짓(오탐 금지)
  ⑦ 깨진 HTML(닫히지 않은 태그) 에서도 예외 없음
- **건드릴 파일**: `src/websearch/extract.py`, `tests/test_extract.py`
- **의존**: 설계
- **상태**: 완료 (81/81)

### 2. 색인이 noindex 를 거른다
- **완료 기준**: 새 테스트가 먼저 실패하는 것을 확인한 뒤 통과. 케이스 —
  ① noindex 페이지 1건 + 일반 페이지 1건인 DB → `index_pages()` 가 1 을 반환하고
     noindex URL 은 `search()` 결과에 없다
  ② 이미 `docs` 에 들어가 있는 URL 이 noindex 면 다음 `index_pages()` 실행 후
     `search()` 결과에서 사라진다
  ③ 일반 문서는 재실행해도 중복 색인되지 않는다(기존 증분 동작 회귀 없음)
  ④ 전체 스위트 통과: `PYTHONPATH=src python3 -m unittest discover tests`
- **건드릴 파일**: `src/websearch/indexer.py`, `tests/test_indexer.py`
- **의존**: 1
- **상태**: 완료 (84/84)

### 3. e2e — 크롤부터 검색까지 왕복
- **완료 기준**: `docs/e2e/noindex-respect/result.md` 에 실행 출력 기록.
  기존 `e2e/crawl_e2e.py`·`e2e/indexer_e2e.py` 회귀 없음도 같이 확인.
- **건드릴 파일**: `e2e/noindex_e2e.py`(신설), `docs/project.md`(e2e 명령 한 줄)
- **의존**: 2
- **상태**: 대기

## e2e 시나리오 <!-- 사용자가 하는 그대로 -->

1. 로컬 테스트 서버에 페이지 3개를 띄운다: 일반 페이지, `<meta name="robots"
   content="noindex">` 페이지, `content="none"` 페이지. 세 페이지 모두 같은
   고유 단어(예: `pyeongsan`)를 본문에 담아 질의 하나로 갈린다.
2. `PYTHONPATH=src python3 -m websearch.crawl <시드> --max 5` — 3페이지 수집.
3. `PYTHONPATH=src python3 -m websearch.indexer <db>` — **1문서 색인**이라고 출력.
4. `PYTHONPATH=src python3 -m websearch.indexer <db> --query pyeongsan` —
   일반 페이지 URL 하나만 나온다. noindex/none URL 은 결과에 없다.
5. 이미 색인된 그 페이지가 뒤늦게 noindex 를 달았다고 가정하고 색인 명령을 다시
   돌린 뒤 같은 질의 → **결과 없음**. (이미 색인된 문서가 빠지는 경로 확인)
   - 주의: `src/websearch/crawl.py:23` 이 `store.has(url)` 이면 건너뛰므로 CLI 재크롤로는
     `pages.html` 이 갱신되지 않는다(`digest.md` [5] 재크롤 스킵, 별도 사안).
     e2e 는 `pages.html` 을 sqlite 로 직접 한 줄 갱신해 그 상황을 만들고,
     검증 대상인 **색인 명령은 사용자가 쓰는 그대로** 실행한다.

## 기록

<!-- 스텝 완료/보류/실패 시 한 줄씩. 상세는 history_current.md 에. -->
- 2026-08-25 계획 작성. 설계 phase 로 넘긴다.
- 2026-08-25 설계 완료 — `docs/design_noindex-respect.md`. A(색인 시점 판정) 채택,
  가정 4건 탐침으로 확인. 스텝 1 개발 착수 가능.
