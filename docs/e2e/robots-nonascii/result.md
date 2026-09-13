# e2e 결과 — 계획 100 `robots-nonascii` (2026-09-13 · 반복 585)

계획서 `docs/plan_robots-nonascii.md` 의 `## e2e 시나리오` 둘을 그대로 돌렸다.

## 앞 관문

| 관문 | 결과 |
|---|---|
| 전수 | `Ran 784 tests in 18.792s · OK` |
| 크롤 간격(품질 기준 · 이 계획이 건드린 축) | `e2e/crawl_delay_e2e.py` **rc=0** — 6페이지 4.5s · `Crawl-delay:2` 최소 2.01s · 하한 도메인 최소 1.00s |
| 비ASCII 축 기존 시나리오 | `e2e/non_ascii_e2e.py` **rc=0**(수정 전 판) |
| CI | 없음(`project.md`) |

다른 축(검색 품질·근거 문단·검색 지연·디자인)은 **이 계획이 건드린 파일과 무관**하다 —
`e2e.md` 1절 「이 계획이 건드린 파일에만 건다」. 돌리지 않았고 **통과라고 적지 않는다.**

## 수단 — 파일을 새로 안 만들었다

시나리오를 **`e2e/non_ascii_e2e.py` 의 넷째 축**으로 넣었다. 이 파일이 이미 「비ASCII URL」
축의 시나리오고, 새 파일을 만들면 명부(`project.md` **e2e 18종**)와 README 의 **22종**이
함께 낡는다 — 재는 것은 같은데 문서 두 곳을 흔드는 쪽을 고를 이유가 없다(ponytail 2번).

**자식 프로세스에 외부 조회 그물을 깔았다.** 한글 호스트 시드는 「죽은 호스트」 역할인데
그 판정이 이 기계의 DNS 로 나가면 `project.md` 한도(외부 네트워크 금지) 위반이다 —
`socket.getaddrinfo` 를 숫자 주소(로컬 서버)만 통과시키게 막았다.

## 시나리오 1 — 크롤 한 판에 비ASCII 씨앗을 섞는다 · **통과**

```
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 e2e/non_ascii_e2e.py
e2e 통과 — 수집 3행(한글 경로 %EA%B0%80.html), 한글 페이지 요청 1건,
서로게이트 시드 1개 건너뜀, 한글 호스트 시드 0행·크롤 생존 · 관문 직접 호출은 차단(네트워크 0회)
rc=0
```

**(a) 오늘 경로** — 씨앗 `http://한글.invalid/페이지` 는 `urls.normalize` 가
`http://xn--bj0bj06e.invalid/%ED%8E%98%EC%9D%B4%EC%A7%80` 로 바꾼 뒤에야 프런티어에 든다
(반복 585 실측). 관문에는 ASCII 만 닿으므로 **오늘은 이 경로로 못 죽는다** — 계약 2 가
계획서에 적어 둔 「도달 불가」의 실물 확인이다. 죽은 호스트라 **행 0개**, 종료 **0**,
로컬 3행과 서버 요청 집합은 **그대로**다(수정 전과 같다 — 회귀 0).

**(b) 정규화를 우회한 직접 호출** — 계획 100 이 고친 자리다. `RobotsCache().allowed(...)`
가 **예외 없이 `False`**, `delay(...)` 가 `None`.

**그물을 `AssertionError` 로 놓은 것이 이 시나리오의 핵심 한 줄이다.** `gaierror` 로 놓으면
관문이 그것을 **599 로 접어** 「네트워크를 탔는데도 `False`」가 조용히 통과한다 — 재려던
것(소켓을 열기 **전에** 끝난다)이 사라진 채 초록이 된다.

## 시나리오 2 — 음성 대조 · **통과**

`except (urllib.error.URLError, OSError, UnicodeError)` 에서 `UnicodeError` 를 도로 뺐다.

| 무엇 | 변이 아래 |
|---|---|
| `e2e/non_ascii_e2e.py` | **rc=1** — 4-b 에서 `UnicodeEncodeError: 'latin-1' codec can't encode characters in position 0-1`. 자리는 `http/client.py:1230 putheader` 로, **소켓을 열기 전**이다 |
| 전수 | `Ran 784 · FAILED (errors=2)` — `TestNonAsciiHost.test_a_non_ascii_host_is_blocked_not_raised` · `…_has_no_declared_delay` |

**죽는 자리가 둘로 갈린다 — 그것이 이 대조의 값이다.** 단위 둘은 **원인**(관문이 예외를
흘린다)을, e2e 는 **증상이 사용자 경로까지 나온다**는 것을 말한다. 단위만 있으면 「관문
함수 하나가 까다롭다」로 읽히고, e2e 만 있으면 어디를 고칠지 모른다.

**전수가 2건만 죽는다는 것도 측정이다** — 비ASCII 호스트를 관문에 직접 넣는 갈래가 이
저장소에 **그 둘뿐**이라는 뜻이고, 크롤 경로 갈래가 하나도 안 죽는 것이 계약 2(도달
불가)와 같은 값을 가리킨다.

원복 후 재실행 **rc=0**(위 출력 그대로) · `git checkout` 으로 되돌린 자리는
`src/websearch/robots.py:158` 한 줄.

## 만든·고친 파일 (계획서 밖 — `e2e.md` 3절 예외)

- `e2e/non_ascii_e2e.py` — 넷째 축 추가(+28줄). 기존 셋의 단언은 **한 줄도 안 고쳤다**
- `docs/e2e/robots-nonascii/result.md` — 이 문서

## 이슈

없다. 7개 카테고리 중 이 계획이 닿는 것은 **기능**(관문이 입력 하나에 죽는다) 하나고,
그 자리는 닫혔다.
