# 계획 100 — 비ASCII 호스트가 robots 관문을 예외로 뚫는다

- 슬러그: `robots-nonascii` · 브랜치 `loop/robots-nonascii`(기점 `064fe56`)
- 근거: `digest.md` 6순위 `[7]` — 「`robots.allowed()`·`delay()` 도 비ASCII 호스트에서
  예외를 흘린다」(2026-08-26 non-ascii-url 리뷰). **오늘 다시 쟀다**(반복 581):

```
$ PYTHONPATH=src python3 -c "RobotsCache().allowed('http://한글.invalid/페이지')"
UnicodeEncodeError: 'latin-1' codec can't encode characters in position 0-1
$ ... .delay('http://한글.invalid/페이지')   → 같은 예외
$ ... 퓨니코드('http://xn--bj0bj06e.invalid/p') → allowed False · delay None (정상)
```

## 계약 — 세우기 전에 재 둔 것

1. **`UnicodeEncodeError` 는 `ValueError` 의 자손이지 `OSError` 가 아니다.**
   `_fetch_robots` 의 `except (urllib.error.URLError, OSError)` 가 못 잡는다 —
   `allowed()` 안의 `except ValueError` 는 `can_fetch` 만 감싸서 **한 칸 옆이다.**
2. **오늘 크롤 경로에서는 도달 불가다**(실측). 씨앗은 `crawl.py:195`, 링크는
   `links.py:34` 에서 `urls.normalize` 를 거쳐 **퓨니코드로 바뀐 뒤** 프런티어에 들어간다.
   그래서 이것은 「지금 죽는 버그」가 아니라 **관문 자체가 입력 하나에 죽는다**는 문제다 —
   `RobotsCache` 는 e2e 와 테스트가 직접 부르는 공개 표면이기도 하다.
3. **처방의 방향이 이 저장소의 기존 판단과 같다.** 바로 위 `except ValueError` 가
   「못 읽는 URL 은 **안 간다** — 예외를 올리면 크롤 전체가 죽는다」를 이미 적어 뒀다.
   같은 값(차단)으로 닫는다. **더 후해지는 쪽으로는 안 고친다**(크롤 윤리 1순위).
4. 자리는 **공유 함수 한 곳**이다 — `_fetch_robots` 의 `except` 한 줄. 호출부
   (`allowed`·`delay`·`known_delay`)마다 가드를 두면 다음 호출부가 또 샌다.
5. 테스트를 더하면 `README.md:104` 의 건수 가드가 문다(계획 99 에서 두 반복 연속 물었다) —
   `docs/project.md:13` 의 형제 숫자까지 **미리** 적어 둔다.

## 스텝

### 스텝 1/1 — 예외를 차단으로 바꾸고, 그 값이 「차단」인지까지 못박는다

- 건드릴 파일: `src/websearch/robots.py` · `tests/test_robots.py` ·
  `README.md`·`docs/project.md`(건수 줄 — 계약 5 로 강제된다)
- 할 일: ① 비ASCII 호스트에서 `allowed()` 가 **예외 없이 `False`**, `delay()` 가 `None`
  임을 재는 테스트를 먼저 쓰고 **RED 를 본다**. ② `_fetch_robots` 의 `except` 에
  `UnicodeError` 를 더한다. ③ GREEN. ④ 퓨니코드 호스트가 그대로인 것을 본다. ⑤ 전수.
- 완료 기준: 비ASCII RED 가 **`UnicodeEncodeError` 로 죽고**(예외가 새는 것을 눈으로 본다) ·
  고친 뒤 `allowed` 는 `False`, `delay` 는 `None` · 퓨니코드 갈래 무변화 · 전수 OK
- TDD 주기는 한 스텝 안에서 닫는다(계획 98·99 와 같은 이유 — 게이트 ⑨).

## 하지 않을 것

- **`urls.normalize` 개조** — 도달 불가를 만들고 있는 것이 그쪽이고, 오늘 그 값은 맞다.
  관문을 고치는 계획에서 관문 앞 정규화를 함께 건드리면 어느 쪽이 막았는지 못 잰다.
- **비ASCII 호스트를 퓨니코드로 **바꿔서** 통과시키는 것** — 그건 `robots` 가 아니라
  `urls` 의 일이고, 관문이 조용히 더 후해진다(계약 3).
- **`known_delay`·`allowed` 에 개별 가드** — 계약 4. 공유 함수 한 곳에서 닫는다.
- **`docs/patches/userinfo-leak-refuse-credentials.patch` 와의 병합** — 자격증명은 보안
  경계라 밤이 영구히 못 연다(게이트 ③).

## e2e 시나리오

1. **크롤 한 판에 비ASCII 씨앗을 섞는다** — 정규화가 퓨니코드로 바꿔 관문이 안 죽는
   오늘 경로를 그대로 보고, 정규화를 우회해 `RobotsCache` 에 직접 넣으면 **차단**으로
   끝나는 것을 본다(예외로 크롤이 죽지 않는다).
2. **음성 대조** — `except` 에서 `UnicodeError` 를 도로 빼면 같은 트리가 어디서 죽는지
   본다(이빨 측정 · 죽는 자리가 테스트 하나인지 전수 전체인지까지 적는다).
