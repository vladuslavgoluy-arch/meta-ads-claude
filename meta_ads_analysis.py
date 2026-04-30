"""
Meta Ads API - Campaign Analysis Script
King of Marketplace (act_1679843539291786)
Campaigns: labgramm* | Period: Feb-Apr 2026
"""

import requests
import json
from datetime import datetime

TOKEN = "EAANodKckp00BRbWwqZB8ZBxpOZBNNXoAyD6YwgZAO8ZAuluZC9V0Pfsmn84nwPghLqiTQOQRcKuoFGU6ebMAvQIQ6FCLQOq7MHtbVBYZBoknyXIgEeTu5xb0TBuIpitrXZByduEWi53NwA5SMVB1VN7xtU0PSxkfJTBmDZAaq98fJ8HjZCrUCZC8EfHsQvhK6Pqh0wlVB4aIJPXtD9eLGdRL6IpZAM5TuVPjsY7KPbrqI3UM7VVdwYZAUz2Bpva2eYvP6fNxzPDSnAHHKUy9UUJuZCTWddTyCF"
AD_ACCOUNT = "act_1679843539291786"
BASE_URL = "https://graph.facebook.com/v22.0"

PERIODS = {
    "february": ("2026-02-01", "2026-02-28"),
    "march":    ("2026-03-01", "2026-03-31"),
    "april":    ("2026-04-01", "2026-04-30"),
}

INSIGHTS_FIELDS = [
    "campaign_name", "campaign_id",
    "spend", "clicks", "impressions", "reach",
    "cpc", "cpm", "ctr",
    "actions", "action_values",
    "cost_per_action_type",
    "frequency",
    "unique_clicks", "unique_ctr",
]

ACTION_TYPES = [
    "onsite_conversion.messaging_conversation_started_7d",
    "offsite_conversion.fb_pixel_lead",
    "offsite_conversion.fb_pixel_purchase",
    "lead",
    "purchase",
    "omni_purchase",
    "omni_lead",
]


def get(path, params=None):
    p = {"access_token": TOKEN, "limit": 500}
    if params:
        p.update(params)
    r = requests.get(f"{BASE_URL}/{path}", params=p, timeout=30)
    if not r.ok:
        print(f"\n❌ API Error {r.status_code}:")
        print(r.text)
        r.raise_for_status()
    return r.json()


def get_all_pages(path, params=None):
    result = []
    data = get(path, params)
    result.extend(data.get("data", []))
    while "paging" in data and "next" in data["paging"].get("cursors", {}):
        after = data["paging"]["cursors"]["after"]
        p = {"access_token": TOKEN, "limit": 500, "after": after}
        if params:
            p.update(params)
        data = get(path, p)
        result.extend(data.get("data", []))
        if not data.get("paging", {}).get("cursors", {}).get("after"):
            break
    return result


def extract_action(actions, action_type):
    if not actions:
        return 0
    for a in actions:
        if a["action_type"] == action_type:
            return float(a["value"])
    return 0


def fetch_campaigns():
    data = get(f"{AD_ACCOUNT}/campaigns", {
        "fields": "id,name,status,objective,created_time",
        "limit": 500,
    })
    campaigns = data.get("data", [])
    labgramm = [c for c in campaigns if c["name"].lower().startswith("labgramm")]
    print(f"\nFound {len(campaigns)} total campaigns, {len(labgramm)} labgramm campaigns:\n")
    for c in labgramm:
        print(f"  [{c['status']}] {c['name']} (id={c['id']})")
    return labgramm


def fetch_insights_by_period(campaign_ids, period_name, date_start, date_stop):
    print(f"\n{'='*60}")
    print(f"PERIOD: {period_name.upper()} ({date_start} → {date_stop})")
    print(f"{'='*60}")

    params = {
        "fields": ",".join(INSIGHTS_FIELDS),
        "time_range": json.dumps({"since": date_start, "until": date_stop}),
        "level": "campaign",
        "filtering": json.dumps([{
            "field": "campaign.id",
            "operator": "IN",
            "value": campaign_ids,
        }]),
        "breakdowns": "",
        "limit": 500,
    }

    data = get(f"{AD_ACCOUNT}/insights", params)
    rows = data.get("data", [])

    totals = {
        "spend": 0, "clicks": 0, "impressions": 0, "reach": 0,
        "conversations": 0, "leads": 0, "purchases": 0,
        "revenue": 0,
    }

    print(f"\n{'Campaign':<40} {'Spend':>8} {'Clicks':>7} {'Conv':>6} {'Leads':>6} {'Purch':>6} {'CTR':>6} {'CPC':>6}")
    print("-" * 95)

    for row in rows:
        spend = float(row.get("spend", 0))
        clicks = int(row.get("clicks", 0))
        impressions = int(row.get("impressions", 0))
        reach = int(row.get("reach", 0))
        ctr = float(row.get("ctr", 0))
        cpc = float(row.get("cpc", 0))
        freq = float(row.get("frequency", 0))
        actions = row.get("actions", [])
        action_values = row.get("action_values", [])

        conversations = extract_action(actions, "onsite_conversion.messaging_conversation_started_7d")
        leads = extract_action(actions, "lead")
        purchases = extract_action(actions, "purchase")
        revenue = extract_action(action_values, "purchase")

        name = row.get("campaign_name", "?")[:38]
        print(f"  {name:<38} ${spend:>7.2f} {clicks:>7} {int(conversations):>6} {int(leads):>6} {int(purchases):>6} {ctr:>5.1f}% ${cpc:>5.2f}")

        totals["spend"] += spend
        totals["clicks"] += clicks
        totals["impressions"] += impressions
        totals["reach"] += reach
        totals["conversations"] += conversations
        totals["leads"] += leads
        totals["purchases"] += purchases
        totals["revenue"] += revenue

    print("-" * 95)
    print(f"\nTOTALS:")
    print(f"  Spend:              ${totals['spend']:.2f}")
    print(f"  Clicks:             {int(totals['clicks'])}")
    print(f"  Impressions:        {int(totals['impressions'])}")
    print(f"  Reach:              {int(totals['reach'])}")
    print(f"  Conversations:      {int(totals['conversations'])}")
    print(f"  Leads (labels):     {int(totals['leads'])}")
    print(f"  Purchases (labels): {int(totals['purchases'])}")
    print(f"  Revenue:            ${totals['revenue']:.2f}")

    s = totals["spend"]
    cl = totals["clicks"]
    conv = totals["conversations"]
    leads = totals["leads"]
    purch = totals["purchases"]

    print(f"\nFUNNEL METRICS:")
    cr_conv_clicks = (conv / cl * 100) if cl else 0
    cr_leads_conv = (leads / conv * 100) if conv else 0
    cr_purch_leads = (purch / leads * 100) if leads else 0
    cr_purch_clicks = (purch / cl * 100) if cl else 0
    cpm = (s / totals["impressions"] * 1000) if totals["impressions"] else 0
    cpc = (s / cl) if cl else 0
    cpp = (s / purch) if purch else 0
    roas = (totals["revenue"] / s) if s else 0

    print(f"  CR% Clicks→Conversations: {cr_conv_clicks:.2f}%")
    print(f"  CR% Conversations→Leads:  {cr_leads_conv:.2f}%")
    print(f"  CR% Leads→Purchases:      {cr_purch_leads:.2f}%")
    print(f"  CR% Clicks→Purchases:     {cr_purch_clicks:.2f}%")
    print(f"  CPM:                      ${cpm:.2f}")
    print(f"  CPC:                      ${cpc:.2f}")
    print(f"  Cost per Purchase:        ${cpp:.2f}")
    print(f"  ROAS (API revenue):       {roas:.2f}x")

    return totals


def fetch_adset_breakdown(campaign_ids, period_name, date_start, date_stop):
    """Breakdown by adset for deeper analysis."""
    print(f"\n{'='*60}")
    print(f"ADSET BREAKDOWN: {period_name.upper()}")
    print(f"{'='*60}")

    params = {
        "fields": ",".join(INSIGHTS_FIELDS),
        "time_range": json.dumps({"since": date_start, "until": date_stop}),
        "level": "adset",
        "filtering": json.dumps([{
            "field": "campaign.id",
            "operator": "IN",
            "value": campaign_ids,
        }]),
        "limit": 500,
    }

    data = get(f"{AD_ACCOUNT}/insights", params)
    rows = data.get("data", [])

    print(f"\n{'AdSet':<35} {'Campaign':<25} {'Spend':>8} {'Clicks':>7} {'Conv':>6} {'Purch':>6} {'CR%':>6}")
    print("-" * 100)

    for row in rows:
        spend = float(row.get("spend", 0))
        clicks = int(row.get("clicks", 0))
        actions = row.get("actions", [])
        conv = extract_action(actions, "onsite_conversion.messaging_conversation_started_7d")
        purch = extract_action(actions, "purchase")
        cr = (conv / clicks * 100) if clicks else 0
        adset_name = row.get("adset_name", "?")[:33]
        camp_name = row.get("campaign_name", "?")[:23]
        print(f"  {adset_name:<33} {camp_name:<23} ${spend:>7.2f} {clicks:>7} {int(conv):>6} {int(purch):>6} {cr:>5.1f}%")


def fetch_placement_breakdown(campaign_ids, period_name, date_start, date_stop):
    """Breakdown by placement."""
    print(f"\n{'='*60}")
    print(f"PLACEMENT BREAKDOWN: {period_name.upper()}")
    print(f"{'='*60}")

    params = {
        "fields": "spend,clicks,impressions,actions,ctr,cpc",
        "time_range": json.dumps({"since": date_start, "until": date_stop}),
        "level": "campaign",
        "filtering": json.dumps([{
            "field": "campaign.id",
            "operator": "IN",
            "value": campaign_ids,
        }]),
        "breakdowns": "publisher_platform,platform_position",
        "limit": 500,
    }

    data = get(f"{AD_ACCOUNT}/insights", params)
    rows = data.get("data", [])

    placement_totals = {}
    for row in rows:
        platform = row.get("publisher_platform", "unknown")
        position = row.get("platform_position", "unknown")
        key = f"{platform} / {position}"
        spend = float(row.get("spend", 0))
        clicks = int(row.get("clicks", 0))
        actions = row.get("actions", [])
        conv = extract_action(actions, "onsite_conversion.messaging_conversation_started_7d")

        if key not in placement_totals:
            placement_totals[key] = {"spend": 0, "clicks": 0, "conv": 0}
        placement_totals[key]["spend"] += spend
        placement_totals[key]["clicks"] += clicks
        placement_totals[key]["conv"] += conv

    print(f"\n{'Placement':<40} {'Spend':>8} {'Clicks':>7} {'Conv':>6} {'CR%':>6}")
    print("-" * 75)
    for k, v in sorted(placement_totals.items(), key=lambda x: -x[1]["spend"]):
        cr = (v["conv"] / v["clicks"] * 100) if v["clicks"] else 0
        print(f"  {k:<38} ${v['spend']:>7.2f} {v['clicks']:>7} {int(v['conv']):>6} {cr:>5.1f}%")


def fetch_daily_breakdown(campaign_ids, date_start, date_stop, label):
    """Daily time series."""
    print(f"\n{'='*60}")
    print(f"DAILY BREAKDOWN: {label.upper()}")
    print(f"{'='*60}")

    params = {
        "fields": "spend,clicks,actions,ctr,cpc,date_start",
        "time_range": json.dumps({"since": date_start, "until": date_stop}),
        "level": "campaign",
        "filtering": json.dumps([{
            "field": "campaign.id",
            "operator": "IN",
            "value": campaign_ids,
        }]),
        "time_increment": 1,
        "limit": 500,
    }

    data = get(f"{AD_ACCOUNT}/insights", params)
    rows = data.get("data", [])

    daily = {}
    for row in rows:
        d = row.get("date_start", "?")
        spend = float(row.get("spend", 0))
        clicks = int(row.get("clicks", 0))
        actions = row.get("actions", [])
        conv = extract_action(actions, "onsite_conversion.messaging_conversation_started_7d")
        purch = extract_action(actions, "purchase")

        if d not in daily:
            daily[d] = {"spend": 0, "clicks": 0, "conv": 0, "purch": 0}
        daily[d]["spend"] += spend
        daily[d]["clicks"] += clicks
        daily[d]["conv"] += conv
        daily[d]["purch"] += purch

    print(f"\n{'Date':<12} {'Spend':>8} {'Clicks':>7} {'Conv':>6} {'Purch':>6} {'CR%':>6}")
    print("-" * 55)
    for d in sorted(daily.keys()):
        v = daily[d]
        cr = (v["conv"] / v["clicks"] * 100) if v["clicks"] else 0
        print(f"  {d:<10} ${v['spend']:>7.2f} {v['clicks']:>7} {int(v['conv']):>6} {int(v['purch']):>6} {cr:>5.1f}%")


def main():
    print("=" * 70)
    print("META ADS ANALYSIS — King of Marketplace (labgramm campaigns)")
    print("=" * 70)

    labgramm_campaigns = fetch_campaigns()
    if not labgramm_campaigns:
        print("\nNo labgramm campaigns found!")
        return

    # Exclude traffic campaigns — only analyze messaging/sales campaigns
    sales_campaigns = [c for c in labgramm_campaigns if "traffic" not in c["name"].lower()]
    traffic_campaigns = [c for c in labgramm_campaigns if "traffic" in c["name"].lower()]
    print(f"\nExcluding {len(traffic_campaigns)} traffic campaigns:")
    for c in traffic_campaigns:
        print(f"  ⛔ {c['name']}")
    print(f"\nAnalyzing {len(sales_campaigns)} SALES/MESSAGING campaigns only.")

    campaign_ids = [c["id"] for c in sales_campaigns]

    period_results = {}
    for period_name, (date_start, date_stop) in PERIODS.items():
        totals = fetch_insights_by_period(campaign_ids, period_name, date_start, date_stop)
        period_results[period_name] = totals

    # Adset-level for March and April
    for period_name in ["march", "april"]:
        date_start, date_stop = PERIODS[period_name]
        fetch_adset_breakdown(campaign_ids, period_name, date_start, date_stop)

    # Placement breakdown
    for period_name in ["march", "april"]:
        date_start, date_stop = PERIODS[period_name]
        fetch_placement_breakdown(campaign_ids, period_name, date_start, date_stop)

    # Daily for March and April
    for period_name in ["march", "april"]:
        date_start, date_stop = PERIODS[period_name]
        fetch_daily_breakdown(campaign_ids, date_start, date_stop, period_name)

    # Debug: show ALL action_types returned by Meta for March (to find Purchase label type)
    print(f"\n{'='*60}")
    print("DEBUG: ALL ACTION TYPES FROM META (March, sales campaigns only)")
    print(f"{'='*60}")
    sales_ids = campaign_ids
    debug_params = {
        "fields": "campaign_name,actions,action_values",
        "time_range": json.dumps({"since": "2026-03-01", "until": "2026-03-31"}),
        "level": "campaign",
        "filtering": json.dumps([{"field": "campaign.id", "operator": "IN", "value": sales_ids}]),
        "limit": 10,
    }
    debug_data = get(f"{AD_ACCOUNT}/insights", debug_params)
    all_action_types = set()
    for row in debug_data.get("data", []):
        for a in row.get("actions", []):
            all_action_types.add(a["action_type"])
        for a in row.get("action_values", []):
            all_action_types.add(f"value:{a['action_type']}")
    for at in sorted(all_action_types):
        print(f"  {at}")

    # Summary comparison
    print(f"\n{'='*60}")
    print("MONTH-OVER-MONTH COMPARISON")
    print(f"{'='*60}")

    for metric in ["spend", "clicks", "conversations", "leads", "purchases", "revenue"]:
        feb = period_results["february"].get(metric, 0)
        mar = period_results["march"].get(metric, 0)
        apr = period_results["april"].get(metric, 0)
        mar_delta = ((mar - feb) / feb * 100) if feb else 0
        apr_delta = ((apr - mar) / mar * 100) if mar else 0
        print(f"  {metric:<16}: Feb={feb:.1f}  Mar={mar:.1f} ({mar_delta:+.1f}%)  Apr={apr:.1f} ({apr_delta:+.1f}%)")


if __name__ == "__main__":
    main()
