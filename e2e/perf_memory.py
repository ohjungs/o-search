"""검색 서버의 **상주 메모리(RSS)** 를 재서 기준선을 만든다.

컨셉 **경량 2** 는 「검색 서버 상주 메모리 **2GB 이하**(판정: 100만 문서 색인 로드 후
RSS 측정)」다. 이 저장소에 그 판정을 돌리는 코드가 **한 줄도 없었다**(2026-09-15 계획 102).

**여기서 재는 것이 왜 자식 프로세스인가.** 낱말 둘이 측정을 가른다 —

- **「서버」**: 측정 프로세스가 아니라 `serve` 프로세스다. 색인을 **만드는** 일은 서버의
  일이 아닌데, 같은 프로세스에서 재면 빌드 할당이 숫자에 섞인다. 진짜 `serve` 는 있는
  DB 를 **열 뿐** 빌드를 안 한다.
- **「상주」**: 봉우리가 아니라 지금 붙들고 있는 것이다. 그래서
  `resource.getrusage().ru_maxrss` 를 안 쓴다 — 그것은 **peak** 이다.

그래서 `python3 -m websearch.serve <db> --port 0` 을 **자식으로 띄우고 밖에서
`ps -o rss=`** 로 읽는다. 사람에게 시키는 그 명령 그대로다(README). 유도는
`docs/design_serve-rss.md`.

**나오는 숫자는 합격 판정이 아니라 기준선이다** — 컨셉의 판정 규모는 100만 문서인데
여기서 만드는 색인은 그보다 훨씬 작다(100만이면 오늘 기계에서 60GB 다). 대신 **두 규모를
재서 기울기**를 낸다. 기울기가 ~0 이면 SQLite 가 디스크에 남아 있다는 실측 증거이고,
0 이 아니면 그 기울기로 100만을 외삽할 수 있다. `perf_search.py` 와 같은 태도다.

**이 자의 값은 「오늘의 숫자」가 아니라 「기울기를 지키는 것」이다.** 오늘 평평한 이유는
`serve.py:222` 가 요청마다 `indexer.search(db_path, …)` 를 불러 **연결을 상주시키지 않기**
때문이다. 누군가 연결을 올리거나 캐시를 얹는 날 이 측정이 평평하지 않게 된다.

실행: PYTHONPATH=src python3 e2e/perf_memory.py [작은규모] [큰규모] [질의당_반복]

종료 코드는 `project.md` 의 0/1/2 관용구다 — 0 통과 · 1 기준 위반 · **2 는 판정이 아니라
「재지 못했다」**.
"""

import json
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from perf_search import build_index, query_paths  # noqa: E402  색인 만드는 코드를 두 벌로 안 만든다

# 컨셉 경량 2. 100만 문서 기준이라 이 규모에서는 한참 밑이어야 한다.
BUDGET_MB = 2048
# 컨셉 경량 1 의 2단계 규모. 외삽의 도착점이다.
TARGET_DOCS = 1000000
# 자식은 **진짜 진입점**이라 리미터가 켜져 있다(`serve.RATE_LIMIT` 60/분/IP · `serve.main`
# 에는 끄는 갈래가 없다). 넘기면 재는 것이 메모리가 아니라 429 다 — 끄는 대신 적게 쏜다.
RATE_LIMIT_HEADROOM = 60
# 두 규모가 이 배수만큼 벌어져야 기울기를 낸다. 붙은 규모에서는 잡음이 신호를 덮는다
# (리뷰 [R102-3]). 4배는 기본값 500/4000(8배)이 여유로 통과하는 선에서 골랐다.
SCALE_RATIO = 4
# 「뜬 직후」끼리의 차는 0 이어야 하는 값이라 잡음 바닥으로 쓴다 — 단, **이 위는 잡음이
# 아니다.** 실측 잡음은 32~176 KB 인데, 색인을 **기동 때** 올리는 회귀를 심으면 그 차가
# 2,688 KB 로 뛴다(e2e [E102-1] 실측). 그때 바닥이 신호와 같이 커져 「신호 <= 바닥」이
# 성립해 **회귀가 평평으로 보고된다** — 바닥에 천장을 두지 않으면 거짓 음성이 열린다.
NOISE_CEILING_KB = 512


class CannotMeasure(Exception):
    """재지 못했다 — 실패(1)가 아니라 2 로 끝난다."""


def rss_kb(pid):
    """프로세스의 **현재** RSS(KB). darwin·linux 둘 다 `ps` 가 KB 로 준다.

    `/proc` 를 안 보는 이유는 macOS 에 없기 때문이다. 죽은 프로세스는 빈 문자열이
    나오는데 `int("")` 로 죽게 두지 않는다 — **0 을 세는 길**이라 명시적으로 막는다.
    """
    out = subprocess.run(["ps", "-o", "rss=", "-p", str(pid)],
                         capture_output=True, text=True, timeout=30).stdout.strip()
    if not out:
        raise CannotMeasure("pid %d 의 RSS 를 못 읽었다 — 자식이 이미 죽었다" % pid)
    return int(out)


def measure_scale(docs, repeat):
    """색인 `docs` 건을 만들고 자식 서버를 띄워 (색인건수, 뜬 직후 KB, 질의 뒤 KB) 를 준다."""
    paths = query_paths(docs)
    requests = len(paths) * repeat
    if requests >= RATE_LIMIT_HEADROOM:
        raise CannotMeasure(
            "질의 %d회가 리미터(%d/분)에 걸린다 — 재는 것이 메모리가 아니라 429 가 된다"
            % (requests, RATE_LIMIT_HEADROOM))

    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "crawl.db")
        indexed = build_index(db, docs)
        # **잴 것이 있나 ①** — 빈 DB 를 재면 어떤 누수 위에서도 숫자가 예뻐진다.
        if indexed <= 0:
            raise CannotMeasure("색인이 %d건이다 — 잰 것은 빈 DB 다" % indexed)

        # **절대 경로다.** `PYTHONPATH="src"` 는 저장소 루트에서 부를 때만 맞고, 밖에서
        # 부르면 자식이 `websearch` 를 못 찾아 종료 2 로 접힌다(리뷰 [R102-1] 실측).
        # 형제들(`crawl_e2e.py:55`·`hidden_passage_e2e.py:103`)이 쓰는 관용구다.
        env = dict(os.environ, PYTHONPATH=os.path.join(ROOT, "src"))
        child = subprocess.Popen(
            [sys.executable, "-m", "websearch.serve", db, "--port", "0"],
            stdout=subprocess.PIPE, text=True, env=env)
        try:
            # `--port 0` 의 실제 포트는 stdout 첫 줄에 온다 — `serve.py` 가 측정
            # 스크립트용으로 만들어 둔 자리다.
            line = child.stdout.readline().strip()
            if not line.startswith("http://"):
                raise CannotMeasure("자식이 포트 줄을 안 냈다: %r" % line)
            base = line.rsplit("/search", 1)[0]

            # **잴 것이 있나 ②** — 죽은 프로세스의 RSS 는 0 이고, 0 은 통과처럼 보인다.
            if child.poll() is not None:
                raise CannotMeasure("자식이 rc=%s 로 이미 끝났다" % child.poll())
            idle = rss_kb(child.pid)

            # **잴 것이 있나 ③** — 200 을 안 받았으면 서버가 색인을 한 번도 안 만졌다.
            # RSS 를 읽기 **전에** 건다. 나중에 걸면 숫자를 쥔 뒤라 「그래도 값은 나왔다」로 샌다.
            for _ in range(repeat):
                for path in paths:
                    try:
                        with urllib.request.urlopen(base + path, timeout=30) as resp:
                            if resp.status != 200:
                                raise CannotMeasure("%s 가 %d 를 냈다" % (path, resp.status))
                            json.loads(resp.read().decode())
                    except urllib.error.HTTPError as exc:
                        raise CannotMeasure("%s 가 %d 를 냈다 — 리미터일 수 있다"
                                            % (path, exc.code))
            busy = rss_kb(child.pid)
            return indexed, idle, busy
        finally:
            child.terminate()
            child.wait(timeout=30)
            # `terminate()`+`wait()` 는 `communicate()` 와 달리 파이프를 **안 닫는다**
            # (계획 101 이 30건을 그렇게 흘렸다).
            child.stdout.close()


def main(argv):
    small = int(argv[1]) if len(argv) > 1 else 500
    big = int(argv[2]) if len(argv) > 2 else 4000
    repeat = int(argv[3]) if len(argv) > 3 else 3
    if small >= big:
        print("작은 규모(%d)가 큰 규모(%d)보다 작아야 기울기를 낸다" % (small, big),
              file=sys.stderr)
        return 2
    # **두 규모가 붙어 있으면 외삽하지 않는다.** 200/400 으로 돌려 보니 기울기가
    # 0.3200 KB/문서 · 100만 외삽 330MB 가 나왔다 — 같은 트리에서 500/4000 은
    # 0.0503 KB/문서 · 66.8MB 다(리뷰 [R102-3] 실측). 차이는 코드가 아니라 **잡음**이고,
    # 그때 「뜬 직후」끼리도 -48.0 KB 로 벌어졌다(같은 색인을 안 만진 프로세스끼리라
    # 0 이어야 하는 값이다). Δ가 작으면 외삽이 그 잡음을 2,500배로 늘린다.
    if big < small * SCALE_RATIO:
        print("큰 규모(%d)가 작은 규모(%d)의 %d배 미만이다 — 이 간격에서 나오는 기울기는"
              " 색인이 아니라 잡음이고, 100만 외삽이 그것을 2,500배로 늘린다"
              % (big, small, SCALE_RATIO), file=sys.stderr)
        return 2

    try:
        rows = [(n,) + measure_scale(n, repeat) for n in (small, big)]
    except CannotMeasure as exc:
        print("재지 못했다: %s" % exc, file=sys.stderr)
        return 2

    print("검색 서버(자식 프로세스) 상주 메모리 — 질의 %d종 × %d회, 순차·로컬"
          % (len(query_paths(small)), repeat))
    print("  %-10s %14s %14s %14s" % ("색인", "뜬 직후", "질의 뒤", "질의가 더한 것"))
    for docs, indexed, idle, busy in rows:
        print("  %-10s %11.1f MB %11.1f MB %11.1f MB"
              % ("%d문서" % indexed, idle / 1024, busy / 1024, (busy - idle) / 1024))

    (d0, _, idle0, busy0), (d1, _, idle1, busy1) = rows
    # 신호는 **질의 뒤** 값끼리의 차다 — 컨셉이 말하는 「색인 로드 후」가 그쪽이다.
    # 서버는 요청마다 DB 를 여니 뜬 직후에는 색인을 아직 안 만졌다.
    signal = busy1 - busy0                      # KB — 색인이 늘어 붙은 몫
    # **잡음 바닥**: 「뜬 직후」끼리는 색인을 안 만진 같은 인터프리터 둘이라 **0 이어야
    # 하는 값**이다. 0 이 아닌 만큼이 이 측정의 잡음이다.
    noise = abs(idle1 - idle0)                  # KB
    print("  신호 %+.1f KB (질의 뒤끼리) — 잡음 바닥 %.1f KB (뜬 직후끼리, 0 이어야 한다)"
          % (signal, noise))
    if noise > NOISE_CEILING_KB:
        # **이만큼 벌어진 것은 잡음이 아니다.** 질의를 한 번도 안 한 프로세스 둘이
        # 색인 크기를 따라 갈렸다는 뜻이니 **기동 때 색인을 올리고 있다**. 이때는
        # 바닥이 아니라 그쪽이 신호다 — 둘 중 큰 쪽으로 기울기를 낸다.
        print("  **뜬 직후끼리가 이미 갈렸다 — 기동 때 색인을 올린다**(잡음 천장 %d KB 초과)"
              % NOISE_CEILING_KB)

    if abs(signal) <= noise <= NOISE_CEILING_KB:
        # **점추정을 내지 않는다.** 신호가 잡음에 덮였으면 기울기는 수가 아니다 —
        # 같은 트리에서 규모만 바꿔 돌리면 0.0137·0.0503 KB/문서(외삽 31·67MB)처럼
        # 배로 흔들린다(리뷰 [R102-3] 실측). **그리고 덮였다는 것 자체가 답이다**:
        # 색인을 몇 배로 키워도 RSS 가 잡음 안에 머물렀다는 뜻이다. 상한만 준다.
        bound = (busy1 + (noise / (d1 - d0)) * (TARGET_DOCS - d1)) / 1024
        print("  기울기를 수로 주지 않는다 — 신호가 잡음 바닥 아래다. **색인을 따라 크지 않는다**")
        print("  %d만 문서: 점추정 없음. 잡음을 기울기 상한으로 놓아도 %.1f MB 이하"
              " — 예산 %d MB 의 %.1f%% 이하"
              % (TARGET_DOCS // 10000, bound, BUDGET_MB, bound / BUDGET_MB * 100))
    else:
        # 기동 적재 회귀는 「질의 뒤」 차가 「뜬 직후」 차를 거의 안 넘는다(실측 2,848 vs
        # 2,688 KB — 여유 160KB). 큰 쪽으로 재지 않으면 같은 회귀를 작게 보고한다.
        slope = max(abs(signal), noise) / (d1 - d0)   # KB/문서
        projected = (busy1 + slope * (TARGET_DOCS - d1)) / 1024   # MB
        print("  기울기 %.4f KB/문서 — **색인을 따라 큰다**(뜬 직후·질의 뒤 중 큰 쪽)" % slope)
        print("  %d만 문서 외삽 %.1f MB — 예산 %d MB 의 %.1f%%"
              % (TARGET_DOCS // 10000, projected, BUDGET_MB, projected / BUDGET_MB * 100))

    # **합격 판정을 내지 않는다.** 이 규모에서 나온 수는 기준선이지 합격선이 아니고,
    # 외삽은 선형 가정 위에 선다. 예산은 docs/project.md, 기준선은 docs/baselines.md.
    print("기준선 — 자식을 밖에서 `ps -o rss=` 로 읽었다(peak 아님). 유도는 docs/design_serve-rss.md")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
