"""1초 하한을 **재는 자리와 값**이 제자리에 있는지 e2e 소스에서 본다.

이 파일이 있는 이유는 계획 105 가 이틀에 걸쳐 찾아낸 것이 **전수 809건에 아무 자국도
안 남기기 때문이다**. 실측(2026-09-18 반복 619): 단언을 옛 자리로 되돌리는 변이와
못을 `0.5` 로 내리는 변이가 **둘 다 809 OK** 였다.

막는 재발 경로는 둘이다:

1. **재는 자리** — `deadline_e2e` 의 핸들러는 `PAGE_DELAY` 만큼 자고 **난 뒤** 시각을
   찍는다(`REQUEST_LOG`). 그 자리로 재면 이 파일 자신의 `time.sleep` 초과분이 간격에
   섞여 4도메인 동시일 때 100ms 넘게 흔들린다 — 10판 실측에서 도착은 전부 1.0 이상인데
   응답 시작만 0.907s 까지 내려갔다. 단언은 `ARRIVAL_LOG` 를 돌아야 한다.
2. **못의 값** — 사양 `docs/specs/concept.md:25` 는 "도메인당 요청 간격 1초 이상" 이다.
   두 e2e 가 9일 동안 `0.95` 를 썼고, 그래서 0.948 이 지터로 읽혔다.

ponytail: 소스의 **낱말**을 센다 — 실제 간격을 재는 것은 e2e 자신이고 이 자는 그 e2e 가
제 자리에서 제 값으로 재는지만 본다. 변수 이름을 바꾸면 여기가 빨개진다. 그것은 조용한
초록보다 낫다 — 이 두 줄은 그렇게 조용히 9일을 살았다.
"""

import pathlib
import re
import unittest

E2E = pathlib.Path(__file__).resolve().parent.parent / "e2e"

SPEC_FLOOR = 1.0  # `docs/specs/concept.md:25` "요청 간격 1초 이상" — 내리는 것은 사양 위반이다

# 파일마다 「간격을 하한과 대는」 줄. 숫자를 한 칸으로 뽑는다.
FLOOR_LINES = {
    "deadline_e2e.py": re.compile(r"assert gap >= ([0-9.]+)"),
    "crawl_delay_e2e.py": re.compile(r"for g in floor if g < ([0-9.]+)"),
}
# 단언 루프가 도는 자리. `page_gaps(port)` 는 잠 뒤(`REQUEST_LOG`)를 준다.
ARRIVAL_LOOP = re.compile(r"for gap in page_gaps\(port, ARRIVAL_LOG\)")

# 재는 자를 **부르는** 자리. `def` 줄은 빼고 센다.
CHECK_CALLS = re.compile(r"^(?!def )\s*(?:\w+\s*=\s*)?check_intervals\(", re.MULTILINE)
# 오늘 크롤을 돌리는 대목 셋: 대조군 · 시나리오 1 · 시나리오 2.
CHECK_CALL_COUNT = 3


def e2e_source(name):
    return (E2E / name).read_text(encoding="utf-8")


class IntervalFloorTest(unittest.TestCase):
    def test_both_floors_are_the_spec_value(self):
        """두 e2e 의 하한이 사양값이어야 한다."""
        for name, pattern in sorted(FLOOR_LINES.items()):
            with self.subTest(name):
                found = pattern.findall(e2e_source(name))
                # **하한 못** — 0건이면 아래 비교가 빈 목록 위에서 조용히 통과한다
                self.assertEqual(
                    1, len(found),
                    "%s 에서 하한을 대는 줄을 %d 개 찾았다 — 정규식이 낡았다"
                    % (name, len(found)))
                self.assertEqual(
                    SPEC_FLOOR, float(found[0]),
                    "%s 의 하한이 %s 다 — 사양은 1초 이상이라 내리면 위반을 지터로 읽는다"
                    % (name, found[0]))

    def test_deadline_asserts_on_arrival(self):
        """단언은 **도착** 시각을 돌아야 한다 — 응답 시작은 이 파일 제 잠이 섞인 값이다."""
        self.assertTrue(
            ARRIVAL_LOOP.search(e2e_source("deadline_e2e.py")),
            "단언 루프가 `ARRIVAL_LOG` 를 안 돈다 — 옛 자리로 돌아가면 제 `time.sleep`"
            " 초과분이 간격에서 빠져 1초를 지킨 크롤도 0.9 대로 찍힌다")

    def test_every_crawl_run_calls_the_check(self):
        """재는 자는 **불려야** 잰다 — 몸만 보면 호출을 지운 트리가 조용히 초록이다.

        실측(2026-09-19): `check_intervals` 호출 세 자리를 지우면 `deadline_e2e` 는
        `rc=0` 이고 `[간격]` 판정 줄만 사라지는데 전수는 **811 그대로 OK** 였다.
        위 두 단언은 함수의 몸을 읽으므로 호출이 0이어도 전부 통과한다.
        """
        found = CHECK_CALLS.findall(e2e_source("deadline_e2e.py"))
        self.assertEqual(
            CHECK_CALL_COUNT, len(found),
            "`check_intervals` 호출이 %d 자리다 — 크롤을 돌리는 대목이 늘거나 줄었으면"
            " 이 수를 함께 고친다. 줄었다면 그 대목은 간격을 안 재고 지나간다"
            % len(found))


if __name__ == "__main__":
    unittest.main()
