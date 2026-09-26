"""Case Study 5 (Harborline Mutual) — illustrative 5-year TCO, FinOps and value model.

Builds TCO-Analysis.xlsx. Every hardcoded number is a blue input on the Assumptions or
OneTime sheet with its basis stated; every other cell is a formula. All prices are
ILLUSTRATIVE planning assumptions, not quotes. BigQuery edition slot prices are the
September 2026 US list prices; the rest (Apigee, Vector Search sizing, model token prices,
Teradata bridge hardware support, loaded labour rates) must be replaced with real quotes.
Year 1 = Oct 2026 – Sep 2027 (M1–M12), matching docs/migration-roadmap.md.

Two cases are kept separate, as driver 5 requires:
  A. Data platform: a COST case against the $6.8M/yr legacy baseline (status quo = renew
     Teradata and refresh the appliance).
  B. Claims assistant: a VALUE case that must justify itself on unit economics
     (NFR-11: <= $0.05 per query all-in = retrieval + inference + logging).
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.chart import BarChart, Reference
from openpyxl.utils import get_column_letter as L

FONT = "Arial"
BLUE = Font(name=FONT, color="0000FF")
BLACK = Font(name=FONT, color="000000")
GREEN = Font(name=FONT, color="008000")
BOLD_WHITE = Font(name=FONT, bold=True, color="FFFFFF")
TITLE = Font(name=FONT, bold=True, size=14)
SECTION = Font(name=FONT, bold=True, size=11)
NOTE = Font(name=FONT, italic=True, color="595959", size=9)
YELLOW = PatternFill("solid", fgColor="FFFF00")
HEADER = PatternFill("solid", fgColor="1F4E79")
SUB = PatternFill("solid", fgColor="D9E1F2")
TOTAL = PatternFill("solid", fgColor="E2EFDA")
THIN = Side(style="thin", color="B7B7B7")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
CUR = '$#,##0;($#,##0);"-"'
PCT = '0.0%;(0.0%);"-"'
NUM = '#,##0;(#,##0);"-"'
DEC = '#,##0.00;(#,##0.00);"-"'
DEC4 = '$0.0000;($0.0000);"-"'
YEARS = ["Y1", "Y2", "Y3", "Y4", "Y5"]

wb = openpyxl.Workbook()


def hdr(ws, row, labels, start=1):
    for i, t in enumerate(labels):
        c = ws.cell(row=row, column=start + i, value=t)
        c.font, c.fill, c.border = BOLD_WHITE, HEADER, BOX
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def widths(ws, ws_widths):
    for i, w in enumerate(ws_widths, start=1):
        ws.column_dimensions[L(i)].width = w


def put(ws, row, col, value, font=BLACK, fmt=None, fill=None, bold=False):
    c = ws.cell(row=row, column=col, value=value)
    c.font = Font(name=FONT, color=font.color, bold=bold or font.bold)
    c.border = BOX
    if fmt:
        c.number_format = fmt
    if fill:
        c.fill = fill
    return c


# ============================================================
# Sheet 1: Assumptions
# ============================================================
A = wb.active
A.title = "Assumptions"
widths(A, [52, 14, 14, 14, 14, 14, 78])
A["A1"] = "Harborline Mutual — TCO, FinOps and Value Assumptions (ILLUSTRATIVE)"
A["A1"].font = TITLE
A["A2"] = ("Legend: blue = input you can change · black = formula · green = link to another sheet · "
           "yellow fill = quote-based or key assumption to replace. Year 1 = Oct 2026–Sep 2027 (M1–M12).")
A["A2"].font = NOTE

A["A4"] = "Timeline drivers (from docs/migration-roadmap.md)"
A["A4"].font = SECTION
hdr(A, 5, ["Driver"] + YEARS + ["Basis"])
TL = {}
timeline = [
    ("td_base_m", "Teradata months at current contract rate", [9, 0, 0, 0, 0], NUM,
     "Oct 2026 – Jun 2027: term ends 30 Jun 2027 (M9)"),
    ("td_bridge_m", "Teradata months on the one-year bridge (+25%)", [3, 9, 0, 0, 0], NUM,
     "ADR-028: bridge Jul 2027 – Jun 2028. Paid to term end even though switch-off is May 2028 (M20)"),
    ("info_m", "Informatica PowerCenter months licensed", [12, 8, 0, 0, 0], NUM,
     "Switched off with Teradata in May 2028 (M20). Assumes co-termination is negotiable (yellow input below)"),
    ("sas_share", "SAS licence share still paid", [1.0, 0.75, 0, 0, 0], PCT,
     "Phase 8: desktop seats step down as programs port from M9; grid kept until reserving ports; retired M24"),
    ("dc_share", "Data-center hosting share still paid", [1.0, 0.7, 0, 0, 0], PCT,
     "Falls away with the appliance (M20) and the SAS grid (M24)"),
    ("sq_refresh", "Status quo: appliance refresh (1 = in this year)", [1, 0, 0, 0, 0], NUM,
     "current-state.md §6: ~$6.0M one-time refresh if Teradata is renewed"),
    ("plat_share", "GCP data platform live (share of steady-state run)", [0.40, 0.90, 1, 1, 1], PCT,
     "Phase 0 foundation + claims domain in Y1; policy, reserving, regulatory in Y2"),
    ("dual_slots", "Dual-run migration reservation (avg slots)", [300, 300, 0, 0, 0], NUM,
     "ADR-030: dedicated migration reservation while domains dual-run (to M18)"),
    ("ai_users", "Assistant average active users", [808, 4358, 4400, 4400, 4400], NUM,
     "Pilot 300 (Mar–May 2027) + scale ramp Jun–Sep → 9,700 user-months in Y1; full 4,400 from Nov 2027"),
    ("ai_fixed_share", "Assistant fixed infrastructure share", [0.5, 1, 1, 1, 1], PCT,
     "Pilot-scope hot tier and gateway from M3–M6; full sizing from Y2"),
    ("ai_team_share", "Assistant run-team share", [0.75, 1, 1, 1, 1], PCT,
     "Team stands up at M3 (Phase 1)"),
    ("search_red", "Search-time reduction achieved (claims staff)", [0.15, 0.25, 0.25, 0.25, 0.25], PCT,
     "ASSUMPTION — no target is stated in requirements.md; A2 measures it in the pilot"),
]
r = 6
for key, label, vals, fmt, basis in timeline:
    put(A, r, 1, label)
    for j, v in enumerate(vals):
        put(A, r, 2 + j, v, BLUE, fmt, YELLOW if key == "search_red" else None)
    put(A, r, 7, basis).font = NOTE
    TL[key] = r
    r += 1

r += 1
INP = {}


def section(title):
    global r
    A.cell(row=r, column=1, value=title).font = SECTION
    r += 1
    hdr(A, r, ["Input", "Value", "Unit", "", "", "", "Basis / source"])
    r += 1


def inp(key, label, value, unit, basis, fmt=CUR, quote=False):
    global r
    put(A, r, 1, label)
    put(A, r, 2, value, BLUE, fmt, YELLOW if quote else None)
    put(A, r, 3, unit)
    put(A, r, 7, basis).font = NOTE
    INP[key] = f"Assumptions!$B${r}"
    r += 1


section("Legacy estate (current-state.md §6)")
inp("td_lic", "Teradata licence and support", 3900000, "$ / yr", "current-state.md")
inp("bridge_up", "Bridge-extension uplift", 0.25, "%", "requirements.md: one-year bridge at +25%", PCT)
inp("td_exthw", "Extended hardware support for the ageing appliance", 250000, "$ / bridge-yr",
    "ILLUSTRATIVE — ADR-028 negotiating term; quote-based", CUR, True)
inp("sas", "SAS licences (grid + desktop)", 1400000, "$ / yr", "current-state.md")
inp("info", "Informatica PowerCenter licence and support", 900000, "$ / yr",
    "current-state.md. Month-by-month exit assumes co-termination — confirm contract", CUR, True)
inp("dc", "Data-center hosting share", 600000, "$ / yr", "current-state.md")
inp("refresh", "Teradata appliance refresh (status quo only)", 6000000, "$ one-time", "current-state.md")
inp("baseline", "Legacy data-platform run baseline (NFR-11)", "=B{0}+B{1}+B{2}+B{3}", "$ / yr", "Sum of the four recurring lines = $6.8M")

section("GCP data platform — steady state (gcp-implementation.md, ADR-021/026)")
inp("ent_slots", "BigQuery Enterprise baseline reservation (ELT, BI, data science)", 1200, "slots", "ILLUSTRATIVE sizing; reservations per workload project (ADR-026)", NUM, True)
inp("ent_price", "BigQuery Enterprise, 1-year commitment", 0.054, "$ / slot-hr", "Google list price, US, Sept 2026", DEC4)
inp("ep_slots", "BigQuery Enterprise Plus reservation (reserving, regulatory; managed DR)", 300, "slots", "ILLUSTRATIVE; Enterprise Plus for managed disaster recovery (NFR-9)", NUM, True)
inp("ep_price", "BigQuery Enterprise Plus, 1-year commitment", 0.09, "$ / slot-hr", "Google list price, US, Sept 2026", DEC4)
inp("auto_slots", "Autoscale slots above baselines (average)", 400, "slots", "ILLUSTRATIVE — close-week and month-end peaks", NUM, True)
inp("auto_price", "BigQuery Enterprise, pay-as-you-go (autoscale)", 0.06, "$ / slot-hr", "Google list price, US, Sept 2026", DEC4)
inp("bi_gib", "BI Engine reservation for Tableau", 100, "GiB", "ILLUSTRATIVE", NUM)
inp("bi_price", "BI Engine price", 0.0416, "$ / GiB-hr", "ILLUSTRATIVE list-price basis", DEC4)
inp("raw_tb", "Raw data estate today", 450, "TB", "NFR-10", NUM)
inp("growth", "Data growth", 0.20, "% / yr", "NFR-10", PCT)
inp("stor_factor", "Billable storage per raw TB (compression vs. bronze/silver/gold + time travel)", 0.8, "×", "ASSUMPTION: ~3:1 compression offset by three layers", DEC)
inp("gcs_price", "Cloud Storage Standard (Iceberg data files)", 0.023, "$ / GB-month", "ILLUSTRATIVE list-price basis; Iceberg-managed tables store data in Cloud Storage", DEC4)
inp("ds_gb", "Datastream CDC volume (Guidewire Oracle)", 2000, "GB / month", "ILLUSTRATIVE", NUM)
inp("ds_price", "Datastream CDC price", 2.0, "$ / GB", "ILLUSTRATIVE list-price basis (first volume tier)", DEC)
inp("dataflow", "Dataflow (batch files, vendor feeds, document chunker)", 60000, "$ / yr", "ILLUSTRATIVE")
inp("notebooks", "Colab Enterprise / serverless Spark (actuarial, data science)", 90000, "$ / yr", "ILLUSTRATIVE — replaces SAS compute")
inp("dataplex", "Dataplex Universal Catalog + lineage", 40000, "$ / yr", "ILLUSTRATIVE")
inp("sdp", "Sensitive Data Protection discovery", 45000, "$ / yr", "ILLUSTRATIVE")
inp("ic", "Dedicated Interconnect (redundant ports, cross-connects, carrier)", 120000, "$ / yr", "ILLUSTRATIVE — ADR-026", CUR, True)
inp("obs", "Cloud Logging / Monitoring", 60000, "$ / yr", "ILLUSTRATIVE")
inp("sec", "Security Command Center, KMS/CMEK, Cloud Armor", 90000, "$ / yr", "ILLUSTRATIVE")
inp("archive", "Archive + regulatory export buckets", 10000, "$ / yr", "ILLUSTRATIVE")
inp("support", "Google Cloud support", 0.04, "% of platform spend", "ILLUSTRATIVE — premium-class support", PCT, True)
inp("dual_price", "Dual-run reservation price (pay-as-you-go)", 0.06, "$ / slot-hr", "Enterprise PAYG: temporary, no commitment", DEC4)
inp("finops", "FinOps analyst, loaded (ADR-008)", 170000, "$ / yr", "ILLUSTRATIVE — new role, hired in Phase 0")

section("Claims assistant — per-query drivers (ADR-006, ADR-008, ADR-024)")
inp("total_users", "Assistant population at scale", 4400, "users", "NFR-10: ~3,800 claims + ~600 underwriting", NUM)
inp("claims_users", "of which claims staff", 3800, "users", "ADR-029", NUM)
inp("qpd", "Queries per user per business day", 25, "queries", "NFR-10: ~110K/day ÷ 4,400", NUM)
inp("days", "Business days per year", 250, "days", "Assumption", NUM)
inp("in_tok", "Input tokens per query (retrieved context + claim + system)", 6000, "tokens", "ADR-008 decomposition", NUM)
inp("out_tok", "Output tokens per query", 500, "tokens", "ADR-008 decomposition", NUM)
inp("fast_share", "Share routed to the fast model", 0.70, "%", "ADR-008 lever: small model for lookups, frontier for summaries", PCT, True)
inp("fast_in", "Fast model input price", 0.30, "$ / M tokens", "ILLUSTRATIVE Flash-class price; confirm on Vertex AI", DEC, True)
inp("fast_out", "Fast model output price", 2.50, "$ / M tokens", "ILLUSTRATIVE Flash-class price", DEC, True)
inp("front_in", "Frontier model input price", 3.00, "$ / M tokens", "ILLUSTRATIVE Sonnet-class price; confirm US multi-region pricing", DEC, True)
inp("front_out", "Frontier model output price", 15.00, "$ / M tokens", "ILLUSTRATIVE Sonnet-class price", DEC, True)
inp("rerank", "Reranking (Vertex ranking)", 1.00, "$ / 1,000 queries", "ILLUSTRATIVE", DEC)
inp("armor", "Model Armor screening", 0.10, "$ / M tokens", "ILLUSTRATIVE", DEC, True)
inp("eval_s", "Online evaluation sample scored by a second model", 0.05, "% of queries", "ADR-007: different scorer model", PCT)
inp("log_q", "Audit + logging per query", 0.0002, "$ / query", "ILLUSTRATIVE — ~30 KB per interaction", DEC4)
inp("vs", "Vertex AI Vector Search serving (hot + reference, 2 regions)", 150000, "$ / yr", "ILLUSTRATIVE sizing (ADR-023)", CUR, True)
inp("docs_day", "New claim documents per day", 25000, "docs", "NFR-10", NUM)
inp("pages", "Pages per document", 4, "pages", "Assumption", NUM)
inp("ocr", "Document AI OCR price", 1.50, "$ / 1,000 pages", "ILLUSTRATIVE list-price basis", DEC)
inp("embed", "Embeddings (new documents + re-embeds)", 10000, "$ / yr", "ILLUSTRATIVE", CUR)
inp("warm", "Warm tier: BigQuery search index + queries", 40000, "$ / yr", "ILLUSTRATIVE (ADR-023)")
inp("apigee", "Apigee subscription (AI gateway)", 180000, "$ / yr", "ILLUSTRATIVE — quote-based (ADR-024)", CUR, True)
inp("cloudrun", "Cloud Run (assistant + retrieval service)", 50000, "$ / yr", "ILLUSTRATIVE")
inp("evalh", "Evaluation harness runs + red-team suite", 40000, "$ / yr", "ILLUSTRATIVE (ADR-007)")
inp("audit", "Audit store (Bucket Lock + BigQuery copy)", 15000, "$ / yr", "ILLUSTRATIVE — 7-year retention (NFR-6)")
inp("team", "Assistant run team (product owner, 2 engineers, golden-set SME share)", 600000, "$ / yr", "ILLUSTRATIVE loaded cost; outside NFR-11's unit-cost definition", CUR, True)
inp("pilot_users", "Pilot users (A2 is measured here)", 300, "users", "ADR-029", NUM)

section("Assistant value (capacity released)")
inp("loaded", "Loaded cost per claims FTE", 95000, "$ / yr", "ILLUSTRATIVE — quote from HR/Finance", CUR, True)
inp("search_share", "Share of adjuster time spent searching", 0.30, "%", "problem-statement.md (adjusters report ~30%)", PCT)
inp("realize", "Share of released capacity that becomes financial value", 0.50, "%", "ASSUMPTION: avoided hiring, overtime and independent-adjuster spend; the rest is quality", PCT, True)

section("NFR-11 ceilings and decision robustness")
inp("ceiling", "Assistant unit-cost ceiling (all-in)", 0.05, "$ / query", "NFR-11", DEC4)
inp("var_gate", "Proposed pilot gate on variable cost per query", 0.02, "$ / query", "Step 12 amendment to gate A2 (ADR-029)", DEC4)
inp("s_gcp", "GCP weighted score (Step 9)", 3.90, "/ 5", "decision-matrix.md", DEC)
inp("s_az", "Azure weighted score (Step 9)", 3.675, "/ 5", "decision-matrix.md (runner-up)", DEC)
inp("w_cost", "Cost criterion weight", 0.15, "%", "decision-matrix.md", PCT)

# fix the baseline formula to real cell refs
brow = int(INP["baseline"].split("$")[-1])
rows_leg = [int(INP[k].split("$")[-1]) for k in ("td_lic", "sas", "info", "dc")]
A.cell(row=brow, column=2, value="=" + "+".join(f"B{x}" for x in rows_leg)).font = BLACK
A.cell(row=brow, column=2).fill = PatternFill(fill_type=None)


def T(key, j):
    return f"Assumptions!${L(2 + j)}${TL[key]}"


def I(key):
    return INP[key]


# ============================================================
# Sheet 2: PlatformRunRate (steady state, today's storage)
# ============================================================
P = wb.create_sheet("PlatformRunRate")
widths(P, [56, 18, 70])
P["A1"] = "GCP Data Platform — Steady-State Run-Rate (annual, illustrative)"
P["A1"].font = TITLE
P["A2"] = "Like-for-like with the $6.8M legacy baseline: licences, infrastructure and support only. People, Tableau and Guidewire are outside both."
P["A2"].font = NOTE
hdr(P, 4, ["Line item", "Annual $", "Formula basis"])
svc = [
    ("BigQuery Enterprise baseline reservation", f"={I('ent_slots')}*{I('ent_price')}*8760", "slots × $/slot-hr × 8,760"),
    ("BigQuery Enterprise Plus reservation", f"={I('ep_slots')}*{I('ep_price')}*8760", "slots × $/slot-hr × 8,760"),
    ("BigQuery autoscale slots", f"={I('auto_slots')}*{I('auto_price')}*8760", "avg slots × $/slot-hr × 8,760"),
    ("BI Engine", f"={I('bi_gib')}*{I('bi_price')}*8760", "GiB × $/GiB-hr × 8,760"),
    ("Datastream CDC", f"={I('ds_gb')}*{I('ds_price')}*12", "GB/month × $/GB × 12"),
    ("Dataflow", f"={I('dataflow')}", "input"),
    ("Colab Enterprise / serverless Spark", f"={I('notebooks')}", "input"),
    ("Dataplex Universal Catalog + lineage", f"={I('dataplex')}", "input"),
    ("Sensitive Data Protection", f"={I('sdp')}", "input"),
    ("Dedicated Interconnect", f"={I('ic')}", "input"),
    ("Logging / Monitoring", f"={I('obs')}", "input"),
    ("Security services", f"={I('sec')}", "input"),
    ("Archive + export buckets", f"={I('archive')}", "input"),
]
row = 5
s0 = row
for label, f, basis in svc:
    put(P, row, 1, label); put(P, row, 2, f, BLACK, CUR); put(P, row, 3, basis).font = NOTE
    row += 1
put(P, row, 1, "Subtotal — services (before support)", bold=True, fill=TOTAL)
put(P, row, 2, f"=SUM(B{s0}:B{row - 1})", BLACK, CUR, TOTAL, bold=True)
SVC_SUB = row
row += 1
put(P, row, 1, "Google Cloud support on services")
put(P, row, 2, f"=B{SVC_SUB}*{I('support')}", BLACK, CUR)
put(P, row, 3, "subtotal × support %").font = NOTE
row += 1
put(P, row, 1, "Services incl. support (does not grow with data)", bold=True, fill=TOTAL)
put(P, row, 2, f"=B{SVC_SUB}+B{row - 1}", BLACK, CUR, TOTAL, bold=True)
SVC = f"PlatformRunRate!$B${row}"
row += 2
put(P, row, 1, "Storage at today's volume, incl. support")
put(P, row, 2, f"={I('raw_tb')}*{I('stor_factor')}*1000*{I('gcs_price')}*12*(1+{I('support')})", BLACK, CUR)
put(P, row, 3, "raw TB × billable factor × 1,000 × $/GB-mo × 12 × (1 + support); grows with data in FiveYearTCO").font = NOTE
STOR = f"PlatformRunRate!$B${row}"
row += 2
put(P, row, 1, "Steady-state platform run-rate at today's volume", bold=True, fill=TOTAL)
put(P, row, 2, f"={SVC}+{STOR}", BLACK, CUR, TOTAL, bold=True)
PLAT_TODAY = f"PlatformRunRate!$B${row}"
row += 1
put(P, row, 1, "Share of the $6.8M legacy baseline")
put(P, row, 2, f"=IFERROR({PLAT_TODAY}/{I('baseline')},0)", BLACK, PCT)

# ============================================================
# Sheet 3: AssistantUnitCost
# ============================================================
U = wb.create_sheet("AssistantUnitCost")
widths(U, [56, 18, 70])
U["A1"] = "Claims Assistant — Unit Cost per Query (illustrative)"
U["A1"].font = TITLE
U["A2"] = "NFR-11 defines 'all-in' as retrieval + inference + logging. The run team is shown separately as 'fully loaded'."
U["A2"].font = NOTE
hdr(U, 4, ["Line item", "Value", "Formula basis"])
urow = 5
UR = {}


def uline(key, label, f, basis, fmt=DEC4, bold=False, fill=None):
    global urow
    put(U, urow, 1, label, bold=bold, fill=fill)
    put(U, urow, 2, f, BLACK, fmt, fill, bold)
    put(U, urow, 3, basis).font = NOTE
    UR[key] = f"AssistantUnitCost!$B${urow}"
    urow += 1


def uband(title):
    global urow
    for c in range(1, 4):
        put(U, urow, c, title if c == 1 else None, bold=True, fill=SUB)
    urow += 1


uband("Variable cost per query")
uline("fast", "Fast-model generation", f"=({I('in_tok')}*{I('fast_in')}+{I('out_tok')}*{I('fast_out')})/1000000", "(in × $in + out × $out) ÷ 1M")
uline("front", "Frontier-model generation", f"=({I('in_tok')}*{I('front_in')}+{I('out_tok')}*{I('front_out')})/1000000", "(in × $in + out × $out) ÷ 1M")
uline("gen", "Routed generation", f"={I('fast_share')}*{UR['fast']}+(1-{I('fast_share')})*{UR['front']}", "fast share × fast + rest × frontier")
uline("rr", "Reranking", f"={I('rerank')}/1000", "$/1,000 ÷ 1,000")
uline("arm", "Model Armor screening", f"=({I('in_tok')}+{I('out_tok')})*{I('armor')}/1000000", "tokens × $/M ÷ 1M")
uline("ev", "Online evaluation sampling", f"={I('eval_s')}*{UR['front']}", "sample % × frontier cost")
uline("log", "Audit + logging", f"={I('log_q')}", "input")
uline("var", "Variable cost per query", f"={UR['gen']}+{UR['rr']}+{UR['arm']}+{UR['ev']}+{UR['log']}", "sum", DEC4, True, TOTAL)
uband("Fixed AI infrastructure (annual, at scale)")
uline("f_vs", "Vector Search serving", f"={I('vs')}", "input", CUR)
uline("f_ocr", "Document AI OCR (new documents)", f"={I('docs_day')}*{I('pages')}*365*{I('ocr')}/1000", "docs/day × pages × 365 × $/1,000 pages", CUR)
uline("f_emb", "Embeddings", f"={I('embed')}", "input", CUR)
uline("f_warm", "Warm tier (BigQuery search)", f"={I('warm')}", "input", CUR)
uline("f_api", "Apigee", f"={I('apigee')}", "input", CUR)
uline("f_run", "Cloud Run", f"={I('cloudrun')}", "input", CUR)
uline("f_ev", "Evaluation harness + red team", f"={I('evalh')}", "input", CUR)
uline("f_aud", "Audit store", f"={I('audit')}", "input", CUR)
uline("fixed", "Fixed AI infrastructure", f"=SUM({UR['f_vs'].replace('AssistantUnitCost!', '')}:{UR['f_aud'].replace('AssistantUnitCost!', '')})", "sum", CUR, True, TOTAL)
uband("Unit cost at full scale")
uline("q", "Queries per year at full scale", f"={I('total_users')}*{I('qpd')}*{I('days')}", "users × queries/day × days", NUM)
uline("fixed_q", "Fixed infrastructure per query", f"=IFERROR({UR['fixed']}/{UR['q']},0)", "fixed ÷ queries")
uline("unit", "All-in unit cost per query (NFR-11 definition)", f"={UR['var']}+{UR['fixed_q']}", "variable + fixed share", DEC4, True, TOTAL)
uline("team_q", "Run team per query", f"=IFERROR({I('team')}/{UR['q']},0)", "team ÷ queries")
uline("loaded_q", "Fully loaded cost per query (incl. run team)", f"={UR['unit']}+{UR['team_q']}", "all-in + team", DEC4, True)

# ============================================================
# Sheet 4: OneTime
# ============================================================
O = wb.create_sheet("OneTime")
widths(O, [58, 8, 11, 12, 14, 15] + [9] * 5 + [13] * 5 + [58, 11])
O["A1"] = "One-Time Program Costs and Phasing (illustrative)"
O["A1"].font = TITLE
O["A2"] = "Blue = inputs. Track: Data = Teradata/SAS exit and platform; AI = claims assistant. Phasing % must sum to 100% (column R)."
O["A2"].font = NOTE
hdr(O, 4, ["Item", "Track", "Quantity", "Unit cost ($)", "Unit", "Total ($)"] +
    [f"{y} %" for y in YEARS] + [f"{y} $" for y in YEARS] + ["Basis", "Phasing check"])
onetime = [
    ("Gate G0 proofs of concept (Iceberg parity, translation, model terms)", "Data", 1, 300000, "lump sum", [1, 0, 0, 0, 0], "ADR-027 gate G0, M1–M3"),
    ("Landing zone, VPC-SC, WIF⇄Entra, Dataplex, Apigee setup (partner)", "Data", 1, 450000, "lump sum", [1, 0, 0, 0, 0], "Phase 0"),
    ("Historical bulk load (Transfer Appliance, Data Transfer Service)", "Data", 1, 80000, "lump sum", [1, 0, 0, 0, 0], "ADR-025/026"),
    ("Automated translation runs + test harness", "Data", 1, 250000, "lump sum", [0.7, 0.3, 0, 0, 0], "BigQuery translator (SQL, BTEQ, TPT)"),
    ("Manual rewrite of untranslated objects (1,800 × 30%)", "Data", 540, 3500, "per object", [0.45, 0.55, 0, 0, 0], "25–35% midpoint; G0 check 3 resizes this"),
    ("Informatica job re-engineering to Dataform (2,400 × 60% retained)", "Data", 1440, 1800, "per job", [0.4, 0.6, 0, 0, 0], "Rationalization retires ~40% of jobs"),
    ("Unified silver model (party/policy/claim, survivorship, crosswalks)", "Data", 1, 900000, "lump sum", [0.6, 0.4, 0, 0, 0], "ADR-001, logical-design.md"),
    ("Domain reconciliation + dual-run effort", "Data", 5, 250000, "per domain", [0.4, 0.6, 0, 0, 0], "ADR-030: claims, policy/billing, reserving, regulatory, remaining"),
    ("Coastal ingestion + 2024 Snowflake account close-out", "Data", 1, 200000, "lump sum", [1, 0, 0, 0, 0], "Phases 0 and 5"),
    ("Tableau repointing of retained reports", "Data", 1, 350000, "lump sum", [0.5, 0.5, 0, 0, 0], "~30% of reports retained"),
    ("SAS program porting to Python/SQL (900 × ~65% retained)", "Data", 600, 2500, "per program", [0.25, 0.75, 0, 0, 0], "Phase 8, M9–M24"),
    ("Decommission + final archive (Teradata, Informatica)", "Data", 1, 200000, "lump sum", [0, 1, 0, 0, 0], "M19–M20, gate T"),
    ("Program management + change (data track)", "Data", 1, 1000000, "lump sum", [0.5, 0.5, 0, 0, 0], "Illustrative"),
    ("Assistant build (6 engineers × 6 months)", "AI", 36, 15000, "per eng-month", [1, 0, 0, 0, 0], "Phase 1, M3–M6 + pilot hardening"),
    ("Golden set + red-team suite (Claims SMEs, red team)", "AI", 1, 250000, "lump sum", [1, 0, 0, 0, 0], "ADR-007, ~1,500 questions"),
    ("Initial document indexing (hot + reference tiers, OCR, embeddings)", "AI", 1, 200000, "lump sum", [0.6, 0.4, 0, 0, 0], "ADR-006; Coastal from M12"),
    ("Training and adoption (4,400 users)", "AI", 1, 350000, "lump sum", [0.5, 0.5, 0, 0, 0], "ADR-029 scale phase"),
]
row = 5
o_start = row
for label, track, qty, unit_cost, unit, phase, basis in onetime:
    put(O, row, 1, label)
    put(O, row, 2, track, BLUE)
    put(O, row, 3, qty, BLUE, NUM)
    put(O, row, 4, unit_cost, BLUE, CUR, YELLOW if "rewrite" in label else None)
    put(O, row, 5, unit)
    put(O, row, 6, f"=C{row}*D{row}", BLACK, CUR)
    for j, p in enumerate(phase):
        put(O, row, 7 + j, p, BLUE, PCT)
        put(O, row, 12 + j, f"=$F{row}*{L(7 + j)}{row}", BLACK, CUR)
    put(O, row, 17, basis).font = NOTE
    put(O, row, 18, f"=SUM(G{row}:K{row})", BLACK, PCT)
    row += 1
o_end = row - 1
OT = {}
for key, label, crit in (("data", "Total one-time — Data track", "Data"), ("ai", "Total one-time — AI track", "AI")):
    put(O, row, 1, label, bold=True, fill=TOTAL)
    put(O, row, 6, f'=SUMIF($B${o_start}:$B${o_end},"{crit}",F${o_start}:F${o_end})', BLACK, CUR, TOTAL, True)
    for j in range(5):
        col = L(12 + j)
        put(O, row, 12 + j, f'=SUMIF($B${o_start}:$B${o_end},"{crit}",{col}${o_start}:{col}${o_end})', BLACK, CUR, TOTAL, True)
    OT[key] = row
    row += 1
put(O, row, 1, "Total one-time", bold=True, fill=TOTAL)
for c in [6] + list(range(12, 17)):
    put(O, row, c, f"={L(c)}{OT['data']}+{L(c)}{OT['ai']}", BLACK, CUR, TOTAL, True)
OT["all"] = row

# ============================================================
# Sheet 5: FiveYearTCO
# ============================================================
F = wb.create_sheet("FiveYearTCO")
widths(F, [60, 15, 15, 15, 15, 15, 17, 62])
F["A1"] = "Five-Year Cost and Value — GCP Target vs. Status Quo (illustrative)"
F["A1"].font = TITLE
F["A2"] = "All figures in $ unless stated. Year 1 = Oct 2026–Sep 2027. Green = links to other sheets."
F["A2"].font = NOTE
hdr(F, 4, ["Line"] + YEARS + ["5-yr total", "Formula basis"])
rows = {}
row = 5


def band(title):
    global row
    for c in range(1, 9):
        put(F, row, c, title if c == 1 else None, bold=True, fill=SUB)
    row += 1


def line(key, label, fn, basis, font=BLACK, fmt=CUR, total=True):
    global row
    put(F, row, 1, label)
    for j in range(5):
        put(F, row, 2 + j, fn(j), font, fmt)
    put(F, row, 7, f"=SUM(B{row}:F{row})" if total else None, BLACK, fmt)
    put(F, row, 8, basis).font = NOTE
    rows[key] = row
    row += 1


def total(key, label, keys, fill=TOTAL):
    global row
    put(F, row, 1, label, bold=True, fill=fill)
    for j in range(6):
        col = L(2 + j)
        put(F, row, 2 + j, "=" + "+".join(f"{col}{rows[k]}" for k in keys), BLACK, CUR, fill, True)
    rows[key] = row
    row += 1


def diff(key, label, a, b, bold=True):
    global row
    put(F, row, 1, label, bold=bold, fill=TOTAL)
    for j in range(6):
        col = L(2 + j)
        put(F, row, 2 + j, f"={col}{rows[a]}-{col}{rows[b]}", BLACK, CUR, TOTAL, bold)
    rows[key] = row
    row += 1


def cumulative(key, src):
    global row
    put(F, row, 1, "Cumulative", bold=True)
    for j in range(5):
        col = L(2 + j)
        f = f"={col}{rows[src]}" if j == 0 else f"={L(1 + j)}{row}+{col}{rows[src]}"
        put(F, row, 2 + j, f, BLACK, CUR, bold=True)
    rows[key] = row
    row += 1


band("A1. Data platform — STATUS QUO (renew Teradata, refresh appliance, keep SAS + Informatica)")
line("sq_td", "Teradata licence and support", lambda j: f"={I('td_lic')}", "Flat — conservative (no renewal uplift)")
line("sq_ref", "Appliance refresh", lambda j: f"={I('refresh')}*{T('sq_refresh', j)}", "current-state.md §6")
line("sq_sas", "SAS", lambda j: f"={I('sas')}", "Flat")
line("sq_inf", "Informatica", lambda j: f"={I('info')}", "Flat")
line("sq_dc", "Data-center hosting", lambda j: f"={I('dc')}", "Flat")
total("sq", "STATUS QUO TOTAL", ["sq_td", "sq_ref", "sq_sas", "sq_inf", "sq_dc"])
row += 1

band("A2. Data platform — TARGET (GCP-native, per the Step 11 roadmap)")
line("td_base", "Teradata at current rate", lambda j: f"={I('td_lic')}/12*{T('td_base_m', j)}", "$/yr ÷ 12 × months")
line("td_br", "Teradata bridge (+25%)", lambda j: f"={I('td_lic')}*(1+{I('bridge_up')})/12*{T('td_bridge_m', j)}", "ADR-028")
line("td_hw", "Teradata extended hardware support", lambda j: f"={I('td_exthw')}/12*{T('td_bridge_m', j)}", "ADR-028 negotiating term")
line("inf", "Informatica (until M20)", lambda j: f"={I('info')}/12*{T('info_m', j)}", "$/yr ÷ 12 × months")
line("sas", "SAS (step-down to M24)", lambda j: f"={I('sas')}*{T('sas_share', j)}", "$/yr × share")
line("dc", "Data-center hosting", lambda j: f"={I('dc')}*{T('dc_share', j)}", "$/yr × share")
line("gsvc", "GCP platform services incl. support", lambda j: f"={SVC}*{T('plat_share', j)}", "PlatformRunRate × share live", GREEN)
line("gsto", "GCP storage (grows 20%/yr)", lambda j: f"={STOR}*{T('plat_share', j)}*(1+{I('growth')})^{j}", "Today's storage × share live × growth", GREEN)
line("dual", "Dual-run migration reservation", lambda j: f"={T('dual_slots', j)}*{I('dual_price')}*8760", "ADR-030 avg slots × PAYG × 8,760")
line("fin", "FinOps analyst", lambda j: f"={I('finops')}", "ADR-008 (people; outside the NFR-11 test)")
line("one_d", "One-time program — Data track", lambda j: f"=OneTime!{L(12 + j)}{OT['data']}", "OneTime sheet", GREEN)
total("tg", "TARGET TOTAL", ["td_base", "td_br", "td_hw", "inf", "sas", "dc", "gsvc", "gsto", "dual", "fin", "one_d"])
row += 1
diff("save", "DATA PLATFORM SAVING (status quo − target)", "sq", "tg")
cumulative("save_cum", "save")
row += 1

band("B. Claims assistant — cost and value (NFR-11: must justify itself on unit economics)")
line("q", "Assistant queries (count)",
     lambda j: f"={T('ai_users', j)}*{I('qpd')}*{I('days')}", "avg users × queries/day × days", BLACK, NUM)
line("ai_var", "Variable (inference, rerank, screening, eval, logging)",
     lambda j: f"={L(2 + j)}{rows['q']}*{UR['var']}", "queries × variable $/query", GREEN)
line("ai_fix", "Fixed AI infrastructure",
     lambda j: f"={UR['fixed']}*{T('ai_fixed_share', j)}", "AssistantUnitCost × share", GREEN)
line("ai_team", "Assistant run team", lambda j: f"={I('team')}*{T('ai_team_share', j)}", "input × share")
line("one_ai", "One-time program — AI track", lambda j: f"=OneTime!{L(12 + j)}{OT['ai']}", "OneTime sheet", GREEN)
total("ai_cost", "ASSISTANT COST", ["ai_var", "ai_fix", "ai_team", "one_ai"])
line("ai_val", "Value: claims capacity released",
     lambda j: f"={T('ai_users', j)}*{I('claims_users')}/{I('total_users')}*{I('loaded')}*{I('search_share')}*{T('search_red', j)}*{I('realize')}",
     "claims users × $/FTE × 30% searching × reduction × realization")
diff("ai_net", "ASSISTANT NET (value − cost)", "ai_val", "ai_cost")
cumulative("ai_cum", "ai_net")
put(F, row, 1, "All-in unit cost per query (infra only, NFR-11 definition)")
for j in range(5):
    col = L(2 + j)
    put(F, row, 2 + j, f"=IFERROR(({col}{rows['ai_var']}+{col}{rows['ai_fix']})/{col}{rows['q']},0)", BLACK, DEC4)
put(F, row, 8, "Above the $0.05 ceiling in Y1 by construction: fixed costs over pilot volumes").font = NOTE
rows["ai_unit"] = row
row += 2

band("C. Program overall (A + B)")
put(F, row, 1, "Total benefit (data-platform saving + assistant value)", bold=True)
for j in range(6):
    col = L(2 + j)
    put(F, row, 2 + j, f"={col}{rows['save']}+{col}{rows['ai_val']}", BLACK, CUR, bold=True)
rows["ben"] = row
row += 1
put(F, row, 1, "Total assistant cost", bold=True)
for j in range(6):
    col = L(2 + j)
    put(F, row, 2 + j, f"={col}{rows['ai_cost']}", BLACK, CUR, bold=True)
rows["tc"] = row
row += 1
diff("net", "PROGRAM NET", "ben", "tc")
cumulative("net_cum", "net")
row += 1

band("Summary metrics")
SUMM = {}


def metric(key, label, f, fmt=CUR):
    global row
    put(F, row, 1, label)
    put(F, row, 4, f, BLACK, fmt, TOTAL, True)
    SUMM[key] = f"FiveYearTCO!$D${row}"
    row += 1


metric("plat_y3", "Steady-state data-platform run-rate, Y3 (GCP services + storage)", f"=D{rows['gsvc']}+D{rows['gsto']}")
metric("plat_pct", "  as a share of the $6.8M baseline", f"=IFERROR(D{rows['gsvc']}/{I('baseline')}+D{rows['gsto']}/{I('baseline')},0)", PCT)
metric("save_y3", "Steady-state data-platform saving, Y3", f"=D{rows['save']}")
sc = rows["save_cum"]
metric("payback", "Data-platform payback year", f'=IF(B{sc}>=0,"Y1",IF(C{sc}>=0,"Y2",IF(D{sc}>=0,"Y3",IF(E{sc}>=0,"Y4",IF(F{sc}>=0,"Y5","beyond Y5")))))', None)
metric("bridge_total", "Bridge-year Teradata payment (licence + hardware support)", f"=SUM(B{rows['td_br']}:F{rows['td_br']})+SUM(B{rows['td_hw']}:F{rows['td_hw']})")
metric("ai_ratio", "Assistant steady-state value ÷ steady-state cost (Y3)", f"=IFERROR(D{rows['ai_val']}/D{rows['ai_cost']},0)", '0.0"x"')
nc = rows["net_cum"]
metric("net_payback", "Program payback year (A + B)", f'=IF(B{nc}>=0,"Y1",IF(C{nc}>=0,"Y2",IF(D{nc}>=0,"Y3",IF(E{nc}>=0,"Y4",IF(F{nc}>=0,"Y5","beyond Y5")))))', None)

ch = BarChart()
ch.type = "col"
ch.title = "Data platform: status quo vs. target (illustrative)"
ch.y_axis.title = "$"
for k in ("sq", "tg"):
    ch.add_data(Reference(F, min_col=1, max_col=6, min_row=rows[k], max_row=rows[k]), titles_from_data=True, from_rows=True)
ch.set_categories(Reference(F, min_col=2, max_col=6, min_row=4, max_row=4))
ch.height, ch.width = 8, 16
F.add_chart(ch, f"A{row + 2}")

# ============================================================
# Sheet 6: NFR11Tests
# ============================================================
G = wb.create_sheet("NFR11Tests")
widths(G, [70, 18, 22, 60])
G["A1"] = "NFR-11 Tests, Gate A2 Check and Decision Robustness"
G["A1"].font = TITLE
hdr(G, 3, ["Test", "Value", "Result", "Basis"])
grow = 4


def gtest(label, f, fmt, result=None, basis="", bold=False):
    global grow
    put(G, grow, 1, label, bold=bold)
    put(G, grow, 2, f, BLACK, fmt, None, bold)
    put(G, grow, 3, result, BLACK, None, TOTAL if result else None, True)
    put(G, grow, 4, basis).font = NOTE
    ref = f"B{grow}"
    grow += 1
    return ref


def gband(title):
    global grow
    for c in range(1, 5):
        put(G, grow, c, title if c == 1 else None, bold=True, fill=SUB)
    grow += 1


gband("1. Data-platform run-rate ≤ $6.8M legacy baseline (excluding the AI capability)")
b1 = gtest("Legacy baseline", f"={I('baseline')}", CUR, None, "current-state.md §6")
b2 = gtest("GCP steady-state run-rate (Y3)", f"={SUMM['plat_y3']}", CUR,
           f'=IF(B{grow}<=B{grow - 1},"PASS","FAIL")', "FiveYearTCO summary")
b3 = gtest("Headroom below baseline", f"={b1}-{b2}", CUR, None, "")
gtest("Extra average BigQuery slots before the baseline is breached",
      f"=IFERROR({b3}/((1+{I('support')})*{I('auto_price')}*8760),0)", NUM, None,
      "headroom ÷ (PAYG $/slot-hr × 8,760 × (1 + support))")
gtest("Run-rate multiple that would breach the baseline", f"=IFERROR({b1}/{b2},0)", '0.0"x"', None, "baseline ÷ run-rate")

grow += 1
gband("2. Assistant unit cost ≤ $0.05 per query (all-in = retrieval + inference + logging)")
c1 = gtest("Variable cost per query", f"={UR['var']}", DEC4, None, "AssistantUnitCost")
c2 = gtest("All-in unit cost at full scale", f"={UR['unit']}", DEC4,
           f'=IF(B{grow}<={I("ceiling")},"PASS","FAIL")', "AssistantUnitCost")
c3 = gtest("Break-even queries per year for the ceiling", f"=IFERROR({UR['fixed']}/({I('ceiling')}-{c1}),0)", NUM, None,
           "fixed ÷ (ceiling − variable)")
c4 = gtest("Break-even active users", f"=IFERROR({c3}/({I('qpd')}*{I('days')}),0)", NUM, None, "queries ÷ (queries/day × days)")
gtest("  as a share of the 4,400-user population", f"=IFERROR({c4}/{I('total_users')},0)", PCT, None, "")
gtest("Fully loaded unit cost incl. run team", f"={UR['loaded_q']}", DEC4,
      f'=IF(B{grow}<={I("ceiling")},"under ceiling","over ceiling")', "Outside NFR-11's definition; shown for honesty")

grow += 1
gband("3. Gate A2 as written in ADR-029 (cost per query ≤ $0.05, measured in the pilot)")
p1 = gtest("Pilot queries per year (300 users)", f"={I('pilot_users')}*{I('qpd')}*{I('days')}", NUM, None, "")
gtest("All-in unit cost during the pilot",
      f"=IFERROR({c1}+{UR['fixed']}*{T('ai_fixed_share', 0)}/{p1},0)", DEC4,
      f'=IF(B{grow}<={I("ceiling")},"PASS","FAILS BY CONSTRUCTION")', "variable + pilot-sized fixed ÷ pilot queries")
gtest("Amended A2: variable cost per query ≤ $0.02 (measured)", f"={c1}", DEC4,
      f'=IF(B{grow}<={I("var_gate")},"PASS","FAIL")', "Step 12 amendment (ADR-029 addendum)")
gtest("Amended A2: modeled all-in at scale ≤ $0.05 (from measured tokens)", f"={c2}", DEC4,
      f'=IF(B{grow}<={I("ceiling")},"PASS","FAIL")', "")

grow += 1
gband("4. Assistant value robustness")
gtest("Break-even search-time reduction (steady state)",
      f"=IFERROR((FiveYearTCO!D{rows['ai_cost']})/({I('claims_users')}*{I('loaded')}*{I('search_share')}*{I('realize')}),0)",
      PCT, None, "Y3 assistant cost ÷ (claims FTE × $ × 30% × realization)")
gtest("  as a share of an adjuster's working day", f"=B{grow - 1}*{I('search_share')}", PCT, None, "")

grow += 1
gband("5. Can cost evidence alone flip ADR-027?")
gtest("GCP lead over Azure (weighted)", f"={I('s_gcp')}-{I('s_az')}", DEC, None, "decision-matrix.md")
gtest("GCP cost-score drop needed to lose the lead", f"=IFERROR(B{grow - 1}/{I('w_cost')},0)", DEC,
      f'=IF(B{grow}>1,"No — needs >1 point","Possible")', "lead ÷ cost weight; GCP scored 3.5 on cost")

for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False
F.freeze_panes = "B5"

wb.save("TCO-Analysis.xlsx")
print("saved TCO-Analysis.xlsx")
