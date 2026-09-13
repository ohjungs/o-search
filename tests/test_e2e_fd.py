"""e2e 진입점이 듣는 소켓과 자식 파이프를 닫고 끝나는지 **소스에서** 본다.

이 파일이 있는 이유는 **18종 e2e 가 전부 rc=0 인 채로 `ResourceWarning` 30건을
흘리고 있었기 때문이다**(2026-09-14 계획 101 최초 측정). 아무도 못 본 이유는 둘이다 —
`ResourceWarning` 은 파이썬이 **기본으로 무시**하고, 단위 전수는 `-b` 로 한 겹 더
덮는다. 초록은 「샌 적이 없다」가 아니라 「안 봤다」였다.

새던 것은 두 계층이다:

1. `ThreadingHTTPServer` 를 `shutdown()` 만 하고 `server_close()` 를 안 했다.
   `shutdown()` 은 `serve_forever` 루프만 멈춘다 — **듣는 소켓은 그대로 열려 있다.**
   17파일이 그랬고, `design_check`·`passage_eval`·`perf_search` 셋만 옳았다.
2. `Popen(..., stdout=PIPE)` 를 `terminate()`+`wait()` 로만 걷었다.
   `communicate()` 와 달리 이 둘은 파이프를 안 닫는다.

**진짜 측정은 이 파일이 아니다** — `PYTHONWARNINGS=always python3 -W always e2e/<이름>.py`
가 fd 를 실제로 센다. 그것을 단위 전수 안에 넣으면 19초짜리 스위트가 분 단위가 되고
(전수 안에서 전수를 다시 도는 모양), 러너 명령에 `-W` 를 다는 쪽은 승인 대기다.
그래서 여기서는 **낱말을 센다.**

ponytail: 파일 단위 개수 비교라 «호출 하나하나» 를 짝지어 주지 않는다 — `server_close()`
를 부르면서 다른 소켓을 새로 흘리면 이 자는 못 잡는다. 잡는 것은 「복사해서 새 e2e 를
만들 때 닫는 줄을 빠뜨리는 것」이라는 실제 재발 경로 하나다. `docs/project.md` 의 러너
명령에 `-W` 가 붙는 날(게이트 ⑫) 그 실측이 이 대리 측정을 대신한다.
"""

import pathlib
import re
import unittest

E2E = pathlib.Path(__file__).resolve().parent.parent / "e2e"

# `http.server.ThreadingHTTPServer(...)` · `HTTPServer(...)` 둘 다 센다.
# **`\b` 를 앞에 붙이면 안 된다** — `ThreadingHTTPServer` 안에서는 `g`·`H` 가
# 둘 다 낱말 문자라 경계가 없고, 이 자는 0개를 세면서 조용히 초록이 된다
# (첫 판에서 실제로 그랬다 — 아래 «잴 것이 있나» 단언이 그것을 잡았다).
SERVER_NEW = re.compile(r"HTTPServer\(")
SERVER_CLOSE = re.compile(r"\.server_close\(\)")
# 자식을 파이프로 띄우는 자리.
POPEN = re.compile(r"\bPopen\(")
# 파이프를 걷는 세 가지 — `communicate()` 는 닫고, `terminate()`+`wait()` 는 안 닫는다.
PIPE_DISPOSED = re.compile(r"\.communicate\(|\.stdout\.close\(\)|\.stderr\.close\(\)")


def e2e_sources():
    """`e2e/*.py` 를 (이름, 소스) 로 준다. 이름순이라 실패 목록이 안 흔들린다."""
    return [(p.name, p.read_text(encoding="utf-8")) for p in sorted(E2E.glob("*.py"))]


class ServerCloseTest(unittest.TestCase):
    def test_every_server_is_closed(self):
        """서버를 만든 만큼 `server_close()` 도 불러야 한다."""
        offenders = []
        for name, src in e2e_sources():
            made = len(SERVER_NEW.findall(src))
            closed = len(SERVER_CLOSE.findall(src))
            if made > closed:
                offenders.append("%s (만든 것 %d · 닫은 것 %d)" % (name, made, closed))
        self.assertEqual(
            [], offenders,
            "듣는 소켓이 열린 채로 끝난다 — `shutdown()` 뒤에 `server_close()` 를 부른다"
            "(`e2e/design_check.py` 가 그 패턴이다):\n  " + "\n  ".join(offenders))

    def test_the_guard_has_something_to_measure(self):
        """센 것이 0이면 위 단언은 어떤 누수 위에서도 초록이다 — 정규식이 낡으면 여기가 문다."""
        total = sum(len(SERVER_NEW.findall(src)) for _, src in e2e_sources())
        self.assertGreaterEqual(total, 17, "e2e 에서 HTTPServer 를 %d 개만 찾았다" % total)


class PopenPipeTest(unittest.TestCase):
    def test_every_child_pipe_is_disposed(self):
        """`Popen` 으로 연 파이프는 `communicate()` 나 명시적 `close()` 로 걷는다.

        `terminate()` + `wait()` 만으로는 `stdout` 의 `TextIOWrapper` 가 안 닫힌다.
        """
        offenders = []
        for name, src in e2e_sources():
            opened = len(POPEN.findall(src))
            disposed = len(PIPE_DISPOSED.findall(src))
            if opened > disposed:
                offenders.append("%s (연 것 %d · 걷은 것 %d)" % (name, opened, disposed))
        self.assertEqual(
            [], offenders,
            "자식 파이프가 열린 채로 끝난다 — `wait()` 뒤에 `stdout.close()` 를 부르거나"
            " `communicate()` 로 걷는다:\n  " + "\n  ".join(offenders))

    def test_the_guard_has_something_to_measure(self):
        total = sum(len(POPEN.findall(src)) for _, src in e2e_sources())
        self.assertGreaterEqual(total, 8, "e2e 에서 Popen 을 %d 개만 찾았다" % total)


if __name__ == "__main__":
    unittest.main()
