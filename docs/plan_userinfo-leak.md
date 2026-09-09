# 계획 83 — URL 에 실린 자격증명을 크롤·저장·렌더 어디에도 들이지 않는다

- **슬러그**: `userinfo-leak` · **브랜치**: `loop/userinfo-leak` (기점 `main` = `6046747`)
- **야간 처분**: **패치만 남긴다.** `SKILL.md` 자동 적용 기준의 「보안 관련 — 줄 수 무관
  항상 보류」 · `severity.md` 3절(보안 전반 = 승인 필요). 구현·테스트를 다 하고 초록을
  확인한 뒤 `docs/patches/` 로 뽑고 작업 트리를 되돌린다.

## 1. 문제

크롤한 페이지에 `<a href="http://user:pw@evil.test/p">` 가 하나 있으면,
남의 자격증명이 **우리 요청 · 우리 DB · 우리 검색 화면** 셋 다에 들어온다.

실측 (2026-09-09 반복 485, `PYTHONPATH=src`):

```
normalize('http://user:pw@evil.test/p')   -> 'http://user:pw@evil.test/p'
normalize('http://google.com@evil.test/x') -> 'http://google.com@evil.test/x'
```

- `urls.normalize:174` 가 `userinfo + at` 을 **일부러 되붙인다.** 그 판단의 근거
  (「떼면 요청 내용이 바뀐다」)는 요청에 대해서는 옳다.
- 그 문자열이 그대로 `pages.url` PRIMARY KEY 가 되고(`crawl.py:345` → `store.upsert`),
  `docs.url` 로 색인되고, `serve.py:280·284` 가 **URL 줄(글자)과 `<a href>` 양쪽**으로
  내보낸다. `_safe_href` 는 스킴만 보므로 이것을 안 막는다.
- 두 번째 예시가 이 결함의 다른 얼굴이다 — `http://google.com@evil.test/x` 는
  사람 눈에 google.com 으로 읽히는 **피싱 모양**이고, 우리 화면이 그것을 그대로 싣는다.

**목표**: 자격증명을 든 URL 은 프런티어에 들어오지 않는다. 요청도 저장도 렌더도 없다.

**기대 결과**: 위 두 URL 이 `normalize` 에서 `None` 이 되어 `links.extract` 가 버리고,
시드로 주면 **왜 버렸는지 알리고** 건너뛴다.

## 2. 근거

- `digest.md ## 다음 계획 후보` `[high]` 「URL 에 실린 자격증명이 `pages.url` PK 로
  저장되고 검색 결과에 렌더된다」 (2026-08-27 반복 115 백지 리뷰).
- 탐색 1~5순위 0건이라 6순위로 내려왔다: 전수 **709 OK** · `src`·`e2e`·`scripts`
  `TODO` **0건** · `docs/candidates.md` 없음 · `docs/patches/` 없음 · `digest ## 보류` 비어 있음.
- `metrics.md ## 야간` 이 이 건을 「승인 대기」 셋 중 하나로 이미 세고 있다 —
  **승인 대기는 「손대지 마라」가 아니라 「적용하지 마라」다**(`SKILL.md` 패치 절).

## 3. 컨셉 축

`concept.md` 갈림길 우선순위 1순위가 **크롤 윤리**다. 남의 자격증명으로 남의 서버에
인증 요청을 보내는 것은 `robots`·간격과 같은 칸에 있는 문제이고, 이 축은
「기능 추가」·「디자인」보다 위다. 그래서 **요청을 안 보내는 쪽**으로 간다.

## 4. 스텝

**2개다.** 고치는 것이 술어 하나라 그보다 잘게 쪼개면 없는 일을 만드는 것이다
(`plan.md` 3절 — 3개 미만 사유).

| # | 산출물 | 의존 | 검증 |
|---|---|---|---|
| 1 | `urls.normalize` 가 userinfo 를 든 URL 에 `None` 을 준다 + 단위 | — | 전수 초록 · 변이 |
| 2 | 시드 스킵 사유를 「읽을 수 없다」와 가른다 | 1 | 전수 초록 · stderr 단언 |

- **스텝 1** — `urls.py`. `normalize` 는 이미 `netloc.rpartition("@")` 로 userinfo 를
  분해하고 있다. 되붙이는 대신 **거절**한다. `links.extract:35` 는 `None` 을 이미
  버리고 있어 링크 경로는 배선 0줄. `crawl.py:345` 는 `or url` 로 떨어지는데 그 `url`
  은 프런티어를 지난 것이라 이미 안전하다 — 리다이렉트 목적지가 자격증명을 들면
  **요청한 URL 로 저장**되는 것이 맞다.
- **스텝 2** — `crawl.py:188~197`. 시드 루프는 버릴 때 사유를 알리는 자리인데,
  스텝 1 뒤에는 자격증명 시드가 「URL 로 읽을 수 없는 시드」라는 **거짓 사유**로
  버려진다. `urls` 에 술어 하나를 내고 분기를 하나 더 단다.

## 5. 완료 기준 (전부 실행해서 확인한다)

1. `PYTHONPATH=src python3 -m unittest discover -b tests` 초록 · 건수 709 초과.
2. 새 단언: `normalize` 가 `user:pw@` · `user@` · `google.com@` 셋 다 `None`.
3. 새 단언: `@` 가 **경로·질의**에만 있는 URL(`http://a.test/x@y?m=n@o`)은 **통과**한다.
4. 새 단언: `links.extract` 가 자격증명 href 를 안 낸다.
5. 새 단언: 자격증명 시드가 **자기 사유**로 stderr 에 나오고 크롤이 안 나간다.
6. 변이 확인(사본 · `PYTHONPATH... PYTHONPYCACHEPREFIX=$(mktemp -d)`):
   가드를 지우면 2·4·5 가 빨개진다.
7. `docs/patches/userinfo-leak-*.patch` 가 존재하고 `git apply --check` 를 통과하며
   **테스트를 포함한다**(`SKILL.md` — 구현만 담긴 패치는 남기지 않는다).
8. 작업 트리가 원상복구돼 전수가 다시 709 OK(= 패치가 안 적용된 상태).

## 6. 하지 않을 것

- **`serve.py` 렌더 가리기.** 입구를 막으면 새 행은 안 생긴다. 실물
  `data/crawl.db` 400행에 자격증명 URL 은 **0건**(2026-09-09 실측)이라 오늘 가릴
  대상이 없다. 여는 조건: **옛 DB 에서 자격증명 행이 1건이라도 세어지는 날.**
- **기존 행 정리·재색인.** 데이터 형태 변경이라 야간 금지이고, `[high]` 「정규화는
  새 DB 에서만 목적을 달성한다」가 이미 사람 몫으로 잡아 둔 자리다.
- **시드에만 예외 주기**(운영자가 준 자격증명은 허용). 두 정책이 되면 규칙이 둘이고,
  허용해도 그 URL 이 `pages.url` 과 검색 결과에 그대로 실린다 — 문제가 안 닫힌다.
- **`to_ascii`·`domain_key` 손대기.** `domain_key` 는 이미 userinfo 를 뗀다.

## 7. 되돌리는 법

가드는 `normalize` 안의 조건 한 줄이다. 지우면 옛 동작 그대로다.
브랜치째 버려도 `main` 은 무변경 — 야간 처분이 패치라 애초에 적용되지 않는다.

## 8. 설계

**필요하다** — `design.md` 1절 「대안이 2개 이상 갈림」. 후보가 적어 둔 안이 둘이고
(저장 열쇠에서만 뗀다 / 렌더에서 가린다) 이 계획이 고른 것은 **셋째 안**이다.
`docs/design_userinfo-leak.md` 에 셋을 비교하고 왜 나머지를 버렸는지 적는다.
