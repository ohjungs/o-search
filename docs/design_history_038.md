# 설계 52 `focus-ring-combinator`

**결정: B안 — 괄호·대괄호 깊이를 세며 top-level 에서만 가른다.** 헬퍼 하나(`_top_level`)를
`e2e/design_check.py` 에 두고 조건 5 를 「쉼표 조각마다 **마지막 compound**」로 옮긴다.
제품 `src/` **0줄** · 새 파일 **0** · 파일 **2개**(`e2e/design_check.py` ·
`tests/test_design_check.py`) · `focus_rule` 시그니처와 rc 계약 무변.

## 1. 세 대안 — 출발점을 갈라서 냈다

| 안 | 출발점 | 무엇 |
|---|---|---|
| **A 최소** | 사다리 2번(있는 것으로 때운다) | `INDIRECT_RE.sub()` 를 **먼저** 돌려 `:not(…)`/`:has(…)` 를 지운 뒤 `re.split(r"[ >+~]", part)[-1]`. 새 코드 3줄 |
| **B 정공** | 정면으로 푼다 | 괄호 `()`·대괄호 `[]` 깊이를 세며 **depth 0 의 쉼표·결합자에서만** 가른다. 헬퍼 12줄 |
| **C 되돌리기 우선** | 5분에 무른다 | 정규식 한 줄 `re.split(r"[ >+~](?![^()]*\))", part)` — 괄호 밖 결합자만 |

## 2. 같은 표에 먹였다 (2026-09-04 · 반복 304 실측 · 25행)

`ok_today` 는 오늘의 조건 5, `순진` 은 후보 항목이 물려준 처방이다. O=통과 · X=거절.
**전문은 아래. 갈리는 행에 ★ 를 달았다.**

| 입력 | 옳은 판정 | 오늘 | 순진 | A | B | C |
|---|---|---|---|---|---|---|
| `.sb input:focus-visible,.sb button:focus-visible,a:focus-visible` (제품) | 통과 | O | O | O | O | O |
| `a:focus-visible .hint` / `>` / `+` / `~` (4행) | 거절 | **O 미탐** ×4 | X | X | X | X |
| `a:focus-visible > .hint` (공백 낀 결합자) | 거절 | **O 미탐** | X | X | X | X |
| `a:focus-visible,.x` (쉼표 목록) | 거절 | **O 미탐** | X | X | X | X |
| `:is(a:focus-visible) .hint` | 거절 | **O 미탐** | X | X | X | X |
| ` a:focus-visible .hint ` (앞뒤 공백) | 거절 | **O 미탐** | X | X | X | X |
| `.sb:focus-within` · `.card:has(a:focus-visible) .hint` | 거절 | X | X | X | X | X |
| `:is(a b):focus-visible` · `a:where(.hint):focus-visible` · `:not(.no-ring):focus-visible` · `a:FOCUS-VISIBLE` | 통과 | O | O | O | O | O |
| `a:focus-visible ` (꼬리 공백) · `.x:focus-visible , a:focus-visible` · 줄바꿈 낀 쉼표 (3행) | 통과 | O | O | O | O | O |
| ★ `a:focus-visible:not(.x + .y)` | 통과 | O | **X 오탐** | O | O | O |
| ★ `a:focus-visible:is(.x + .y)` | 통과 | O | **X 오탐** | **X 오탐** | O | O |
| ★ `a:is(.x, .y):focus-visible` | 통과 | O | **X 오탐** | **X 오탐** | O | **X 오탐** |
| ★ `a:focus-visible:not(.x, .y)` | 통과 | O | **X 오탐** | O | O | **X 오탐** |
| ★ `a:is(.x, .y > .z):focus-visible` | 통과 | O | **X 오탐** | **X 오탐** | O | **X 오탐** |
| ★ `a:focus-visible[class~=btn]` | 통과 | O | **X 오탐** | **X 오탐** | O | **X 오탐** |
| **틀린 행 / 25** | | **8** | **6** | **4** | **0** | **4** |

**갈리는 행이 무엇을 갈랐나** — 셋 다 결합자 4종과 쉼표 목록은 닫는다. 가른 것은
**괄호 안에 결합자·쉼표가 들어간 정상 셀렉터**다.
- `:is(…)`/`:where(…)` 는 **투명**이라 `INDIRECT_RE` 가 안 지운다(계획 49 오탐 표가
  붙들고 있는 성질이다). 그래서 A 의 「먼저 지우기」는 `:not`/`:has` 만 막고
  `:is(.x + .y)`·`:is(.x, .y)` 앞에서 그대로 넘어진다 — **처방을 한 칸 밀었을 뿐**이다.
- C 의 lookahead 는 결합자만 보고 **쉼표를 안 본다.** `:not(.x, .y)` 처럼 괄호 안
  쉼표가 있으면 조각이 둘로 갈려 앞 조각에 포커스가 없어진다.
- **대괄호는 셋 중 B 만 본다.** `[class~=btn]` 의 `~` 는 CSS 속성 연산자인데 결합자와
  같은 글자다. 이 행은 후보에도 계획서에도 없었고 설계가 표를 짜다 찾았다.

**A·C 의 오탐은 오늘 제품에서는 안 터진다** — 제품 CSS 에 괄호도 대괄호도 0곳이다.
그러나 오탐의 결과는 **rc 2 → e2e 전수 RED** 라, 누가 `:is()` 나 속성 셀렉터를 처음
쓰는 날 제품이 아니라 **재는 자 때문에** 빨개진다. 계획 44·49 가 지킨 「오탐 0」이
이 계획의 최대 위험이라고 계획서 5절이 못박았으므로 **0 을 낸 안을 고른다.**

## 3. 계약

`e2e/design_check.py` — `INDIRECT_RE` 정의 옆에 헬퍼를 두고 234행 `if` 를 루프로 바꾼다.

```python
def _top_level(text, seps):
    """괄호 `()`·대괄호 `[]` **밖**의 `seps` 에서만 가른다. 깊이만 세고 셀렉터 문법은 안 읽는다."""
    depth, buf, out = 0, [], []
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        elif depth == 0 and ch in seps:
            out.append("".join(buf)); buf = []; continue
        buf.append(ch)
    out.append("".join(buf))
    return out
```

```python
for part in _top_level(selector, ","):
    last = _top_level(part.strip(), " \t\n>+~")[-1]
    if not FOCUS_RE.search(INDIRECT_RE.sub("", last)):
        raise ValueError("outline 을 정하는 유일한 규칙이 키보드 포커스용이 아니다: %s"
                         % " ".join(selector.split()))
```

- **메시지 문자열은 한 글자도 안 바꾼다.** 기존 변이 표 6행(V11·ⓒ·ⓓ·ⓔ·ⓕ·ⓖ)이
  `"포커스용이 아니다"` 로 붙들려 있다.
- **`part.strip()` 이 계약이다.** `RULE_RE.group(1)` 은 앞 규칙의 개행을 달고 온다
  (제품 실측: `'\n.sb input:focus-visible,…'`). 꼬리 공백이면 마지막 compound 가
  빈 문자열이 돼 **오탐**이 난다 — 표의 `a:focus-visible ` 행이 그 자리다.
- `max(0, depth - 1)` 은 짝 안 맞는 `)` 가 깊이를 음수로 끌고 가 뒤 전체를
  「괄호 안」으로 만드는 것을 막는다.

## 4. 천장 (ponytail 주석으로 코드에 남긴다)

- **CSS 파서가 아니다.** 문자열·주석은 `COMMENT_OR_STRING_RE` 가 이미 지운 뒤라
  따옴표 안의 괄호는 여기 안 온다. 백슬래시 이스케이프(`.a\,b`)는 안 읽는다 — 0곳.
- `INDIRECT_RE` 의 **괄호 한 겹** 천장은 그대로다(계획 49). 이 변경은 «어디를 볼까»만
  옮기고 «무엇을 지울까»는 안 건드린다. 별개 후보 [4](두 겹 중첩)는 여전히 안 연다.
- 마지막 compound 안에서 선언 순서로 자기를 뒤엎는 형태는 여전히 못 잡는다(변경 없음).

## 5. 완료 기준 (계획서 5절 + 설계가 더한 것)

계획서 5절 1~8 을 그대로 받고 **4번(오탐 0)의 표를 위 ★ 여섯 행으로 못박는다** —
`:not(.x + .y)` · `:is(.x + .y)` · `:is(.x, .y)` · `:not(.x, .y)` · `:is(.x, .y > .z)` ·
`[class~=btn]`. 앞의 정상 넷(제품 3조각 · `:is` · `:where` · 대문자)은 이미 표에 있다.

**미탐 표에 더할 행 일곱**: 결합자 4종 · 공백 낀 `>` · 쉼표 목록 `a:focus-visible,.x` ·
`:is(a:focus-visible) .hint`. 전부 `twist(":focus-visible", …)` 로 표현된다.

**변이는 넷이다**(계획서는 셋). 넷째가 A·C 를 B 와 가르는 자리다.

| 변이 | 되돌리는 것 | 죽어야 하는 행 |
|---|---|---|
| ① 마지막 compound → 조각 전체 | `[-1]` 제거 | 결합자 4종 |
| ② 쉼표 가르기 제거 | 바깥 `_top_level(selector, ",")` → `[selector]` | `a:focus-visible,.x` |
| ③ 결합자 집합에서 `~` 를 뺀다 | `" \t\n>+~"` → `" \t\n>+"` | `a:focus-visible~.hint` |
| ④ **깊이 세기 제거** | `_top_level` → `str.split` (= 순진한 처방) | ★ 여섯 행 전부 |

심기 전에 `count(원문) == 1` 로 원문 존재를 먼저 단언한다(`digest [8]` BSD sed 거짓 초록).

## 6. 안 할 것 / 되돌리기

계획서 7절 그대로 — CSS 파서 없음 · 괄호 두 겹 안 엶 · 제품 CSS 무변 · 조건 1·4·6 무변.
되돌리기는 **커밋 하나 revert**(3절 셋 중 ③). 피처 플래그는 안 쓴다 — 검사기 내부라
설정 표면이 없고, 플래그가 곧 「거짓 초록으로 되돌아가는 스위치」가 된다.
