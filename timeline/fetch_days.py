#!/usr/bin/env python3
"""抓 tznthou 從開帳號到今天的每日貢獻資料，給時間軸主視覺用。"""
import datetime
import json
import subprocess
from collections import Counter
from pathlib import Path

LOGIN = "tznthou"
# 日期一律用台灣時間切：不指定時 GITHUB_TOKEN 用 UTC，台灣早上 8 點前的貢獻會被算到前一天
TZ_HEADER = "Time-Zone: Asia/Taipei"
OUT = Path(__file__).resolve().parent / "contributions.json"
CAL = ("query($login:String!,$from:DateTime!,$to:DateTime!){user(login:$login){"
       "contributionsCollection(from:$from,to:$to){contributionCalendar{totalContributions "
       "weeks{contributionDays{date contributionCount}}}}}}")

now = datetime.datetime.now(datetime.timezone.utc)
days = {}
yearly = {}
for y in range(2012, now.year + 1):
    to = f"{y}-12-31T23:59:59Z" if y < now.year else now.strftime("%Y-%m-%dT%H:%M:%SZ")
    res = json.loads(subprocess.check_output([
        "gh", "api", "graphql", "-H", TZ_HEADER, "-f", f"query={CAL}", "-f", f"login={LOGIN}",
        "-f", f"from={y}-01-01T00:00:00Z", "-f", f"to={to}",
    ]))
    cal = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    yearly[y] = cal["totalContributions"]
    for w in cal["weeks"]:
        for d in w["contributionDays"]:
            if d["contributionCount"] > 0 and d["date"].startswith(str(y)):
                days[d["date"]] = d["contributionCount"]

ordered = sorted(days.items())
with open(OUT, "w", encoding="utf-8") as f:
    json.dump({"login": LOGIN, "fetched_at": now.isoformat(), "yearly": yearly,
               "days": ordered}, f, ensure_ascii=False)

print("yearly:", yearly)
print("green days:", len(ordered), " total:", sum(days.values()))
print("first:", ordered[0], " second:", ordered[1] if len(ordered) > 1 else None)
top = max(ordered, key=lambda kv: kv[1])
print("busiest day:", top)
monthly = Counter()
for date, n in ordered:
    monthly[date[:7]] += n
print("monthly (2025-2026):")
for m in sorted(monthly):
    if m >= "2025":
        print(f"  {m}: {monthly[m]}")
print("saved:", OUT)
