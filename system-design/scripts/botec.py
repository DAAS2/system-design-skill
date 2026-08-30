#!/usr/bin/env python3
"""botec.py -- back-of-the-envelope calculator for system design.

Stdlib only, deterministic. Forces architecture claims through numbers.

Examples:
  python botec.py full --dau 1000000 --reads-per-user 50 --writes-per-user 5
  python botec.py qps --events-per-day 86400000
  python botec.py storage --events-per-day 5000000 --bytes 1000 --years 5
  python botec.py bandwidth --rps 10000 --bytes-per-response 10000
  python botec.py servers --peak-rps 100000 --per-server-rps 2000
  python botec.py cache --objects-per-day 5000000 --bytes-per-object 1000
  python botec.py nines
  python botec.py latency
"""

import argparse
import math
import sys

DAY = 86_400


def human_int(n: float) -> str:
    return f"{int(round(n)):,}"


def human_bytes(n: float) -> str:
    if n <= 0:
        return "0 B"
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB"]
    i = min(int(math.log(n, 1024)), len(units) - 1)
    return f"{n / (1024 ** i):,.2f} {units[i]}"


def human_bits_per_s(n: float) -> str:
    if n <= 0:
        return "0 bit/s"
    units = ["bit/s", "Kbit/s", "Mbit/s", "Gbit/s", "Tbit/s"]
    i = min(int(math.log(n, 1000)), len(units) - 1)
    return f"{n / (1000 ** i):,.2f} {units[i]}"


def qps_from_events(events_per_day: float) -> float:
    return events_per_day / DAY


def storage_total(events_per_day: float, bytes_each: float, years: float,
                  replication: float, growth_per_year: float = 1.0) -> float:
    total = 0.0
    for _ in range(int(years)):
        total += events_per_day * bytes_each * 365 * replication
        events_per_day *= growth_per_year  # compounding growth, 1.0 = flat
    return total


def bandwidth(rps: float, bytes_per_response: float) -> float:
    return rps * bytes_per_response * 8  # bits per second


def forces(peak_read_qps: float, peak_write_qps: float, total_storage: float,
           hot_cache: float, avg_read_mbps: float) -> list[str]:
    out = []
    if peak_write_qps > 5_000:
        out.append("peak write QPS > 5k: a single relational primary will strain; "
                   "plan partitioning or queue-buffered writes")
    if peak_read_qps > 10_000:
        out.append("peak read QPS > 10k: a cache layer is mandatory; CDN too if responses are cacheable")
    if total_storage > 5 * 1024 ** 4:
        out.append("5-yr storage > 5 TiB: plan storage tiering and/or sharding now, not later")
    if hot_cache > 50 * 1024 ** 3:
        out.append("hot set > 50 GiB: single cache node is marginal; plan a cache cluster")
    if avg_read_mbps > 1_000:
        out.append("read bandwidth > 1 Gbps sustained: push bulk/static content to a CDN")
    if not out:
        out.append("no thresholds crossed: prefer the boring tier-appropriate design")
    return out


def row(label: str, value: str) -> str:
    return f"  {label:<34} {value}"


def cmd_full(a) -> None:
    reads = a.dau * a.reads_per_user
    writes = a.dau * a.writes_per_user
    r_qps = qps_from_events(reads)
    w_qps = qps_from_events(writes)
    r_peak = r_qps * a.peak_factor
    w_peak = w_qps * a.peak_factor
    s_day = writes * a.write_size * a.replication
    s_total = storage_total(writes, a.write_size, a.years, a.replication, a.growth)
    bw_avg_bps = bandwidth(r_qps, a.read_size)
    bw_peak_bps = bandwidth(r_peak, a.read_size)
    hot = a.hot_frac * writes * max(a.write_size, a.read_size)
    app_nodes = max(2, math.ceil(r_peak / a.per_server_rps))
    concurrency = r_peak * (a.p99_latency_ms / 1000.0)

    print("Capacity worksheet")
    print(row("DAU", human_int(a.dau)))
    print(row("Read events/day", human_int(reads)))
    print(row("Write events/day", human_int(writes)))
    print(row("Read:write ratio", f"{reads / max(writes, 1):,.0f}:1"))
    print()
    print(row("Read QPS avg / peak", f"{r_qps:,.1f} / {r_peak:,.1f}"))
    print(row("Write QPS avg / peak", f"{w_qps:,.1f} / {w_peak:,.1f}"))
    print(row("Read bandwidth avg / peak", f"{human_bits_per_s(bw_avg_bps)} / {human_bits_per_s(bw_peak_bps)}"))
    print()
    print(row(f"Storage/day (x{a.replication:g} replication)", human_bytes(s_day)))
    print(row(f"Storage over {a.years:g} yr (growth x{a.growth:g}/yr)", human_bytes(s_total)))
    print(row(f"Hot-set cache ({a.hot_frac:.0%} of daily writes)", human_bytes(hot)))
    print()
    print(row(f"App nodes @ {human_int(a.per_server_rps)} RPS/node", f"{human_int(app_nodes)} (min 2 for HA)"))
    print(row("In-flight requests at peak (Little)", f"{concurrency:,.0f} "
          f"(= peak QPS x {a.p99_latency_ms:g} ms p99; size pools/connections for this)"))
    print()
    print("Decisions these numbers force:")
    for f in forces(r_peak, w_peak, s_total, hot, bw_avg_bps / 1e6):
        print(f"  - {f}")


def cmd_qps(a) -> None:
    avg = qps_from_events(a.events_per_day)
    print(row("QPS avg", f"{avg:,.1f}"))
    print(row(f"QPS peak (x{a.peak_factor:g})", f"{avg * a.peak_factor:,.1f}"))


def cmd_storage(a) -> None:
    day = a.events_per_day * a.bytes * a.replication
    print(row("Storage/day", human_bytes(day)))
    print(row(f"Storage over {a.years:g} yr", human_bytes(
        storage_total(a.events_per_day, a.bytes, a.years, a.replication, a.growth))))


def cmd_bandwidth(a) -> None:
    print(row("Bandwidth", human_bits_per_s(bandwidth(a.rps, a.bytes_per_response))))


def cmd_servers(a) -> None:
    n = math.ceil(a.peak_rps / a.per_server_rps)
    print(row("Servers for peak", human_int(n)))
    print(row("With N+2 redundancy", human_int(max(n + 2, 3))))


def cmd_cache(a) -> None:
    hot = a.hot_frac * a.objects_per_day * a.bytes_per_object
    print(row(f"Hot set ({a.hot_frac:.0%} of daily objects)", human_bytes(hot)))
    print(row("Single Redis-class node fits?", "yes" if hot < 50 * 1024 ** 3 else "no - plan cache cluster"))


NINES = [
    (99.0, "3.65 days", "43.2 min"),
    (99.9, "8.76 hours", "4.32 min"),
    (99.99, "52.6 min", "25.9 s"),
    (99.999, "5.26 min", "2.59 s"),
    (99.9999, "31.5 s", "0.259 s"),
]


def cmd_nines(_a) -> None:
    print("  Availability | Downtime/year | Error budget (30-day window)")
    for pct, per_year, per_month in NINES:
        print(f"  {pct:>9g}%     | {per_year:>13} | {per_month}")


LATENCY = [
    ("L1 / L2 / L3 cache ref", "0.7 ns / 2.5 ns / 8 ns"),
    ("Main memory ref", "~90 ns"),
    ("Compress 1 KiB (LZ4/Zippy)", "1-3 us"),
    ("NVMe 4 KiB random read", "20-100 us"),
    ("Read 1 MiB: memory / SSD / HDD", "~10 us / ~100 us / ~6 ms (plus seek ~10 ms)"),
    ("Same-DC round trip", "200-500 us"),
    ("Cross-zone round trip", "~1 ms"),
    ("Cross-region RTT (US<->EU)", "70-150 ms"),
    ("Redis GET (same DC)", "0.2-1 ms"),
    ("Simple Postgres query (indexed)", "1-5 ms"),
    ("S3 PUT small object", "10-50 ms"),
    ("TLS handshake + HTTP round trip", "50-250 ms"),
    ("LLM short response", "~3 s"),
    ("LLM long-context prefill", "~10 s"),
    ("LLM reasoning call", "~30 s+"),
]


def cmd_latency(_a) -> None:
    print("  Operation                          Latency")
    for name, val in LATENCY:
        print(f"  {name:<34} {val}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="botec", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp):
        sp.add_argument("--peak-factor", type=float, default=2.0,
                        help="peak/avg multiplier (2-3 typical, up to 10 login-heavy)")

    f = sub.add_parser("full", help="full capacity worksheet")
    f.add_argument("--dau", type=float, required=True, help="daily active users")
    f.add_argument("--reads-per-user", type=float, required=True)
    f.add_argument("--writes-per-user", type=float, required=True)
    f.add_argument("--read-size", type=float, default=10_000, help="bytes per read response")
    f.add_argument("--write-size", type=float, default=1_000, help="bytes per write event")
    f.add_argument("--replication", type=float, default=3.0)
    f.add_argument("--years", type=float, default=5.0)
    f.add_argument("--growth", type=float, default=1.0, help="traffic growth multiplier per year (1.0=flat)")
    f.add_argument("--hot-frac", type=float, default=0.2, help="hot-set fraction (80/20 rule)")
    f.add_argument("--per-server-rps", type=float, default=2_000)
    f.add_argument("--p99-latency-ms", type=float, default=200.0)
    add_common(f)
    f.set_defaults(fn=cmd_full)

    q = sub.add_parser("qps", help="events/day to QPS")
    q.add_argument("--events-per-day", type=float, required=True)
    add_common(q)
    q.set_defaults(fn=cmd_qps)

    s = sub.add_parser("storage", help="storage math")
    s.add_argument("--events-per-day", type=float, required=True)
    s.add_argument("--bytes", type=float, required=True)
    s.add_argument("--replication", type=float, default=3.0)
    s.add_argument("--years", type=float, default=5.0)
    s.add_argument("--growth", type=float, default=1.0)
    s.set_defaults(fn=cmd_storage)

    b = sub.add_parser("bandwidth", help="bandwidth from RPS and response size")
    b.add_argument("--rps", type=float, required=True)
    b.add_argument("--bytes-per-response", type=float, required=True)
    b.set_defaults(fn=cmd_bandwidth)

    v = sub.add_parser("servers", help="server count from peak RPS")
    v.add_argument("--peak-rps", type=float, required=True)
    v.add_argument("--per-server-rps", type=float, default=2_000)
    v.set_defaults(fn=cmd_servers)

    c = sub.add_parser("cache", help="hot-set cache size")
    c.add_argument("--objects-per-day", type=float, required=True)
    c.add_argument("--bytes-per-object", type=float, required=True)
    c.add_argument("--hot-frac", type=float, default=0.2)
    c.set_defaults(fn=cmd_cache)

    n = sub.add_parser("nines", help="availability table")
    n.set_defaults(fn=cmd_nines)

    l = sub.add_parser("latency", help="latency reference table")
    l.set_defaults(fn=cmd_latency)

    a = p.parse_args(argv)
    a.fn(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
