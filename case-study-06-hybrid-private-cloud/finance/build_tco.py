"""Case Study 6 (Alder Valley Bancorp) — illustrative 5-year TCO model for the hybrid platform decision.

Builds TCO-Analysis.xlsx. Every hardcoded number is a blue input on the Assumptions or OneTime
sheet with its basis stated; every other cell is a formula. Prices are ILLUSTRATIVE planning
assumptions (yellow = quote-based, replace with real quotes). Year 1 = Oct 2026 – Sep 2027 (M1–M12).

Three paths are compared:
  SQ    Status quo as defined in requirements.md NFR-10: renew VCF (3-yr quote) + like-for-like refresh
  VCF   The VCF track (Step 6): renew + vDefend + Live Recovery + vSAN ESA refresh + enablement
  AZ    The selected Azure Local + Arc track (Steps 7, 11, 12): 15-month VCF bridge, then Azure Local
Common lines (Windows Server SA, RHEL, Veeam, facilities, the MRA resilience program) appear in all three.
The ThresholdTest sheet computes the Broadcom renewal price at which gate G0-2 would reverse ADR-031.
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
NUM = '#,##0.##;(#,##0.##);"-"'
DEC = '#,##0.00;(#,##0.00);"-"'
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
# Assumptions
# ============================================================
A = wb.active
A.title = "Assumptions"
widths(A, [58, 14, 14, 14, 14, 14, 80])
A["A1"] = "Alder Valley Bancorp — Hybrid Platform TCO Assumptions (ILLUSTRATIVE)"
A["A1"].font = TITLE
A["A2"] = ("Legend: blue = input · black = formula · green = link · yellow fill = quote-based or key assumption. "
           "Year 1 = Oct 2026–Sep 2027. $ unless stated.")
A["A2"].font = NOTE
A["A4"] = "Timeline drivers (docs/migration-roadmap.md)"
A["A4"].font = SECTION
hdr(A, 5, ["Driver"] + YEARS + ["Basis"])
TL = {}
timeline = [
    ("cur_m", "VCF current subscription: months", [6, 0, 0, 0, 0], NUM, "Current term ends 31 Mar 2027 (M6)"),
    ("ren_m", "SQ/VCF paths: months at the 3-yr renewal quote", [6, 12, 12, 6, 0], NUM, "Apr 2027 – Mar 2030"),
    ("up_m", "SQ/VCF paths: months at the next renewal (uplifted)", [0, 0, 0, 6, 12], NUM, "From Apr 2030"),
    ("br_m", "AZ path: months on the VCF bridge", [6, 9, 0, 0, 0], NUM, "ADR-032: 1 Apr 2027 – 30 Jun 2028 (15 months)"),
    ("hz_az", "AZ path: Horizon share still paid", [1, 2 / 12, 0, 0, 0], PCT, "Horizon retired M14 (Nov 2027)"),
    ("avd", "AZ path: AVD share of full estate", [0.25, 0.95, 1, 1, 1], PCT, "Pilot + rollout M9–M14"),
    ("maint_sq", "SQ/VCF paths: legacy hardware maintenance ($)", [550000, 350000, 300000, 300000, 300000], CUR,
     "Refreshed kit carries 5-yr warranty in capex; 2023 hosts out of warranty from 2028"),
    ("maint_az", "AZ path: legacy hardware maintenance ($)", [550000, 400000, 150000, 150000, 150000], CUR,
     "Legacy retired M20; 2023 hosts re-imaged into Azure Local (maintenance on those only)"),
    ("gov", "Guest governance services ramp (VCF and AZ)", [0.5, 1, 1, 1, 1], PCT, "Arc-enabled servers on all guests from Phase 0"),
    ("lz", "Azure landing zone ramp (VCF and AZ)", [0.6, 1, 1, 1, 1], PCT, "Landing zone from M2; dev/test moves M8–M13"),
    ("fte", "Added FTE ramp", [0.5, 1, 1, 1, 1], PCT, "Hires in Phase 0–1"),
    ("vdf_vcf", "VCF path: vDefend + Live Recovery ramp", [0.5, 1, 1, 1, 1], PCT, "From renewal (Apr 2027)"),
    ("vdf_az", "AZ path: vDefend on Tier-0 hosts during the bridge (share of full scope)", [0.25, 0.375, 0, 0, 0], PCT,
     "ADR-033: NSX parity for the MRA tests on VMware — half the scope for the bridge months"),
]
r = 6
for key, label, vals, fmt, basis in timeline:
    put(A, r, 1, label)
    for j, v in enumerate(vals):
        put(A, r, 2 + j, v, BLUE, fmt)
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


section("VMware (Broadcom)")
inp("vcf_cur", "VCF subscription, current term", 1250000, "$ / yr", "current-state.md §6")
inp("vcf_quote", "VCF 3-year renewal quote (P0)", 1650000, "$ / yr", "current-state.md §6 — the G0-2 comparison point", CUR, True)
inp("vcf_up", "Uplift at the following renewal (Apr 2030)", 0.15, "%", "ASSUMPTION — reported renewal increases", PCT, True)
inp("br_prem", "Short-term (bridge) premium over the renewal rate", 0.10, "%", "ASSUMPTION — ADR-032", PCT, True)
inp("vdf_core", "vDefend distributed firewall add-on", 90, "$ / core-yr", "ILLUSTRATIVE — quote-based (ADR-011)", CUR, True)
inp("vdf_cores", "Cores needing vDefend (Z0, PCI, Oracle, Z1 hosts, both sites)", 1600, "cores", "ADR-011 scope", NUM)
inp("live_rec", "VMware Live Recovery add-on", 250000, "$ / yr", "ILLUSTRATIVE — quote-based (ADR-010)", CUR, True)
inp("horizon", "Omnissa Horizon", 350000, "$ / yr", "current-state.md §6")

section("Azure Local + Arc")
inp("host_fee", "Azure Local host fee (L1)", 10, "$ / core-month", "Microsoft pricing (from 25 Jun 2026)", CUR)
inp("az_cores", "Azure Local physical cores at full estate", 4160, "cores", "Same core count as today (no consolidation assumed)", NUM)
inp("ahb", "Share of cores covered by Azure Hybrid Benefit", 1.0, "%", "ASSUMPTION — WS Datacenter + SA covers every host core; VERIFY at G0-2", PCT, True)
inp("avd_vcpu", "AVD session-host vCPUs (1,400 users)", 1760, "vCPU", "ILLUSTRATIVE sizing", NUM)
inp("avd_price", "AVD on Azure Local service fee", 0.01, "$ / vCPU-hr", "ILLUSTRATIVE — confirm; user rights via M365 licences", DEC, True)

section("Governance and landing zone (VCF and AZ paths — driver 3/4 capabilities the status quo lacks)")
inp("servers", "Guest servers under governance", 2040, "servers", "~2,400 VMs less ~15% retired", NUM)
inp("gov_srv", "Guest governance services (Defender for Servers, Update Manager, Policy, logs)", 20, "$ / server-month", "ILLUSTRATIVE — list-price basis", CUR, True)
inp("lz_run", "Azure landing zone run cost (dev/test, analytics, ML, vault copies)", 250000, "$ / yr", "ILLUSTRATIVE")

section("People (NFR-12: at most 4 hires)")
inp("fte_cost", "Loaded cost per added FTE", 170000, "$ / yr", "ILLUSTRATIVE")
inp("fte_vcf", "Added FTEs — VCF path", 1, "FTE", "Automation / VCF Automation", NUM)
inp("fte_az", "Added FTEs — AZ path", 3, "FTE", "Azure Local, automation, platform engineering", NUM)

section("Common to all paths (equal; shown for a complete TCO)")
inp("ws_sa", "Windows Server Datacenter (EA with SA)", 600000, "$ / yr", "current-state.md §6 — also the basis of Azure Hybrid Benefit")
inp("rhel", "RHEL subscriptions", 400000, "$ / yr", "current-state.md §6")
inp("veeam", "Veeam and backup-appliance support", 300000, "$ / yr", "current-state.md §6")
inp("dc", "DC2 colocation + DC1 facility share", 1600000, "$ / yr", "current-state.md §6")

section("Capital (hardware)")
inp("sq_cap", "SQ: like-for-like refresh (44 hosts + DC1 FC array)", 4200000, "$", "current-state.md §6")
inp("vcf_cap", "VCF: 44 vSAN ESA hosts, FC array retired", 3400000, "$", "ILLUSTRATIVE — ADR-009", CUR, True)
inp("az_cap", "AZ: Azure Local validated nodes (replace 44 hosts + Tier-0/Oracle instances)", 3600000, "$", "ILLUSTRATIVE — ADR-015", CUR, True)
inp("az_reuse", "AZ: re-image and upgrade 32 hosts from 2023 (NICs, NVMe)", 300000, "$", "ASSUMPTION — 2023 hosts on the Azure Local catalog; verify", CUR, True)
inp("az_lab", "AZ: G0 lab (8 nodes, later the clean room)", 400000, "$", "ILLUSTRATIVE")

section("Decision robustness (docs/decision-matrix.md)")
inp("sc_az", "Azure cost score", 4.5, "/ 5", "decision-matrix.md", DEC)
inp("sc_vcf", "VCF cost score at the quote", 2.0, "/ 5", "decision-matrix.md", DEC)
inp("sc_flip", "VCF cost score that flips the decision", 3.5, "/ 5", "decision-matrix.md sensitivity (4.025 vs 3.95)", DEC)

section("Oracle consolidation lever (platform-neutral)")
inp("ora_cores", "Oracle-licensed cores today", 640, "cores", "current-state.md §3", NUM)
inp("ora_new", "Oracle-licensed cores after consolidation at refresh", 512, "cores", "ASSUMPTION — fewer, faster cores; subject to the batch PoC (NFR-4)", NUM, True)
inp("ora_cf", "Oracle core factor (x86)", 0.5, "×", "Oracle core factor table", DEC)
inp("ora_sup", "Oracle annual support per processor licence", 10450, "$ / licence-yr", "ILLUSTRATIVE — 22% of $47,500 list; actual per contract", CUR, True)


def T(key, j):
    return f"Assumptions!${L(2 + j)}${TL[key]}"


def I(key):
    return INP[key]


# ============================================================
# OneTime
# ============================================================
O = wb.create_sheet("OneTime")
widths(O, [60, 9, 12, 14, 14, 15] + [9] * 5 + [13] * 5 + [48, 11])
O["A1"] = "One-Time Program Costs and Phasing (illustrative)"
O["A1"].font = TITLE
O["A2"] = "Path: ALL = every path (the MRA program is mandatory regardless); VCF; AZ. Phasing must total 100% (column R)."
O["A2"].font = NOTE
hdr(O, 4, ["Item", "Path", "Quantity", "Unit cost ($)", "Unit", "Total ($)"] + [f"{y} %" for y in YEARS] +
    [f"{y} $" for y in YEARS] + ["Basis", "Check"])
onetime = [
    ("Resilience program: Git plans, orchestrator, NSX/firewall parity, Data Guard sizing", "ALL", 1, 600000, "lump", [0.7, 0.3, 0, 0, 0], "ADR-002, ADR-006, ADR-033"),
    ("Vault + clean-room build", "ALL", 1, 450000, "lump", [0.8, 0.2, 0, 0, 0], "ADR-003"),
    ("Inventory reconciliation + Arc onboarding of existing guests", "ALL", 1, 150000, "lump", [1, 0, 0, 0, 0], "MRA inventory finding"),
    ("Azure landing zone build + AWS account closure", "VCF", 1, 200000, "lump", [1, 0, 0, 0, 0], "ADR-014 / driver 4"),
    ("VCF 9.1 upgrade + VCF Automation / VKS enablement", "VCF", 1, 400000, "lump", [0.6, 0.4, 0, 0, 0], "ADR-009, ADR-013"),
    ("Live Recovery implementation", "VCF", 1, 200000, "lump", [0.8, 0.2, 0, 0, 0], "ADR-010"),
    ("Rancher → VKS", "VCF", 1, 100000, "lump", [0.5, 0.5, 0, 0, 0], "ADR-013"),
    ("Program management + training (VCF)", "VCF", 1, 300000, "lump", [0.5, 0.5, 0, 0, 0], "Illustrative"),
    ("Azure landing zone build + AWS account closure", "AZ", 1, 200000, "lump", [1, 0, 0, 0, 0], "ADR-019"),
    ("G0 proof-of-concept services", "AZ", 1, 150000, "lump", [1, 0, 0, 0, 0], "ADR-031"),
    ("Tier-2/1 migration services (1,895 VMs)", "AZ", 1895, 250, "per VM", [0.5, 0.5, 0, 0, 0], "ADR-034, Azure Migrate"),
    ("Tier-0 migration project (Data Guard switchover, appliances, core app)", "AZ", 1, 600000, "lump", [0, 1, 0, 0, 0], "ADR-034"),
    ("Recovery executors re-targeted to Hyper-V Replica / Datacenter Firewall", "AZ", 1, 200000, "lump", [0.3, 0.7, 0, 0, 0], "ADR-017, ADR-033"),
    ("AVD rollout (1,400 users)", "AZ", 1, 300000, "lump", [0.5, 0.5, 0, 0, 0], "ADR-020"),
    ("Rancher → AKS on Azure Local", "AZ", 1, 100000, "lump", [0.5, 0.5, 0, 0, 0], "ADR-019"),
    ("Training (Azure Local, Hyper-V, Terraform)", "AZ", 1, 200000, "lump", [0.5, 0.5, 0, 0, 0], "Driver 5"),
    ("Program management + change (AZ)", "AZ", 1, 600000, "lump", [0.5, 0.5, 0, 0, 0], "Illustrative"),
]
row = 5
o0 = row
for label, path, qty, uc, unit, ph, basis in onetime:
    put(O, row, 1, label); put(O, row, 2, path, BLUE); put(O, row, 3, qty, BLUE, NUM)
    put(O, row, 4, uc, BLUE, CUR); put(O, row, 5, unit); put(O, row, 6, f"=C{row}*D{row}", BLACK, CUR)
    for j, p in enumerate(ph):
        put(O, row, 7 + j, p, BLUE, PCT)
        put(O, row, 12 + j, f"=$F{row}*{L(7 + j)}{row}", BLACK, CUR)
    put(O, row, 17, basis).font = NOTE
    put(O, row, 18, f"=SUM(G{row}:K{row})", BLACK, PCT)
    row += 1
o1 = row - 1
OT = {}
for key in ("ALL", "VCF", "AZ"):
    put(O, row, 1, f"Total one-time — {key}", bold=True, fill=TOTAL)
    for c in [6] + list(range(12, 17)):
        col = L(c)
        put(O, row, c, f'=SUMIF($B${o0}:$B${o1},"{key}",{col}${o0}:{col}${o1})', BLACK, CUR, TOTAL, True)
    OT[key] = row
    row += 1

# ============================================================
# FiveYearTCO
# ============================================================
F = wb.create_sheet("FiveYearTCO")
widths(F, [64, 15, 15, 15, 15, 15, 17, 60])
F["A1"] = "Five-Year TCO — Status Quo vs. VCF Track vs. Azure Local + Arc (illustrative)"
F["A1"].font = TITLE
F["A2"] = "Year 1 = Oct 2026–Sep 2027. 'Platform TCO' excludes the new governance and landing-zone capabilities the status quo lacks (NFR-10 is tested on it)."
F["A2"].font = NOTE
hdr(F, 4, ["Line"] + YEARS + ["5-yr total", "Formula basis"])
R = {}
row = 5


def band(title):
    global row
    for c in range(1, 9):
        put(F, row, c, title if c == 1 else None, bold=True, fill=SUB)
    row += 1


def line(key, label, fn, basis, font=BLACK):
    global row
    put(F, row, 1, label)
    for j in range(5):
        put(F, row, 2 + j, fn(j), font, CUR)
    put(F, row, 7, f"=SUM(B{row}:F{row})", BLACK, CUR)
    put(F, row, 8, basis).font = NOTE
    R[key] = row
    row += 1


def total(key, label, keys, fill=TOTAL):
    global row
    put(F, row, 1, label, bold=True, fill=fill)
    for j in range(6):
        col = L(2 + j)
        put(F, row, 2 + j, "=" + "+".join(f"{col}{R[k]}" for k in keys), BLACK, CUR, fill, True)
    R[key] = row
    row += 1


def common(prefix):
    line(f"{prefix}_ws", "Windows Server Datacenter + SA (common)", lambda j: f"={I('ws_sa')}", "Equal in all paths")
    line(f"{prefix}_rh", "RHEL (common)", lambda j: f"={I('rhel')}", "Equal")
    line(f"{prefix}_ve", "Veeam (common)", lambda j: f"={I('veeam')}", "Equal")
    line(f"{prefix}_dc", "Facilities (common)", lambda j: f"={I('dc')}", "Equal")
    line(f"{prefix}_res", "MRA resilience program, one-time (common)", lambda j: f"=OneTime!{L(12 + j)}{OT['ALL']}", "OneTime ALL", GREEN)
    return [f"{prefix}_ws", f"{prefix}_rh", f"{prefix}_ve", f"{prefix}_dc", f"{prefix}_res"]


def vmw_renew(j):
    return (f"={I('vcf_cur')}/12*{T('cur_m', j)}+{I('vcf_quote')}/12*{T('ren_m', j)}"
            f"+{I('vcf_quote')}*(1+{I('vcf_up')})/12*{T('up_m', j)}")


band("A. STATUS QUO — renew VCF (3-yr) + like-for-like refresh (NFR-10 baseline)")
line("sq_vmw", "VMware (current term, renewal, next renewal uplifted)", vmw_renew, "months × rate")
line("sq_hz", "Omnissa Horizon", lambda j: f"={I('horizon')}", "Flat")
line("sq_mt", "Legacy hardware maintenance", lambda j: f"={T('maint_sq', j)}", "Timeline input")
line("sq_cap", "Like-for-like refresh (capex)", lambda j: f"={I('sq_cap')}*{[0.5, 0.5, 0, 0, 0][j]}", "50/50 across Y1–Y2 (EOS Dec 2027)")
sq_common = common("sq")
total("sq", "STATUS QUO TOTAL", ["sq_vmw", "sq_hz", "sq_mt", "sq_cap"] + sq_common)
row += 1

band("B. VCF TRACK — modernize in place (Step 6)")
line("v_vmw", "VMware (current term, renewal, next renewal uplifted)", vmw_renew, "Same as status quo")
line("v_vdf", "vDefend add-on", lambda j: f"={I('vdf_core')}*{I('vdf_cores')}*{T('vdf_vcf', j)}", "$/core × cores × ramp")
line("v_lr", "Live Recovery add-on", lambda j: f"={I('live_rec')}*{T('vdf_vcf', j)}", "× ramp")
line("v_hz", "Omnissa Horizon", lambda j: f"={I('horizon')}", "Flat")
line("v_mt", "Legacy hardware maintenance", lambda j: f"={T('maint_sq', j)}", "Timeline input")
line("v_cap", "vSAN ESA refresh (capex)", lambda j: f"={I('vcf_cap')}*{[0.5, 0.5, 0, 0, 0][j]}", "50/50 across Y1–Y2")
line("v_fte", "Added FTEs", lambda j: f"={I('fte_cost')}*{I('fte_vcf')}*{T('fte', j)}", "")
line("v_one", "One-time program (VCF)", lambda j: f"=OneTime!{L(12 + j)}{OT['VCF']}", "OneTime VCF", GREEN)
v_common = common("v")
line("v_gov", "NEW CAPABILITY: guest governance services", lambda j: f"={I('gov_srv')}*{I('servers')}*12*{T('gov', j)}", "$/server-mo × servers × 12")
line("v_lz", "NEW CAPABILITY: Azure landing zone run", lambda j: f"={I('lz_run')}*{T('lz', j)}", "")
total("v_plat", "VCF PLATFORM TCO (excl. new capabilities)", ["v_vmw", "v_vdf", "v_lr", "v_hz", "v_mt", "v_cap", "v_fte", "v_one"] + v_common)
total("v", "VCF TRACK TOTAL", ["v_plat", "v_gov", "v_lz"])
row += 1

band("C. AZURE LOCAL + ARC — selected (Steps 7, 11, 12)")
line("a_vmw", "VMware (current term + 15-month bridge at a premium)",
     lambda j: f"={I('vcf_cur')}/12*{T('cur_m', j)}+{I('vcf_quote')}*(1+{I('br_prem')})/12*{T('br_m', j)}", "ADR-032")
line("a_vdf", "vDefend on Tier-0 hosts during the bridge", lambda j: f"={I('vdf_core')}*{I('vdf_cores')}*{T('vdf_az', j)}", "ADR-033")
line("a_hz", "Omnissa Horizon (until M14)", lambda j: f"={I('horizon')}*{T('hz_az', j)}", "")
line("a_avd", "AVD on Azure Local service fee", lambda j: f"={I('avd_vcpu')}*{I('avd_price')}*8760*{T('avd', j)}", "vCPU × $/hr × 8,760 × share")
line("a_host", "Azure Local host fee net of Azure Hybrid Benefit",
     lambda j: f"={I('host_fee')}*{I('az_cores')}*12*(1-{I('ahb')})*{[0.3, 0.8, 1, 1, 1][j]}", "$/core-mo × cores × 12 × uncovered share × estate share")
line("a_mt", "Legacy hardware maintenance", lambda j: f"={T('maint_az', j)}", "Timeline input")
line("a_cap", "Azure Local nodes + reuse + G0 lab (capex)",
     lambda j: f"={I('az_cap')}*{[0.6, 0.4, 0, 0, 0][j]}+{I('az_reuse')}*{[0, 1, 0, 0, 0][j]}+{I('az_lab')}*{[1, 0, 0, 0, 0][j]}", "ADR-015, ADR-031")
line("a_fte", "Added FTEs", lambda j: f"={I('fte_cost')}*{I('fte_az')}*{T('fte', j)}", "")
line("a_one", "One-time program (AZ)", lambda j: f"=OneTime!{L(12 + j)}{OT['AZ']}", "OneTime AZ", GREEN)
a_common = common("a")
line("a_gov", "NEW CAPABILITY: guest governance services", lambda j: f"={I('gov_srv')}*{I('servers')}*12*{T('gov', j)}", "Same as VCF track")
line("a_lz", "NEW CAPABILITY: Azure landing zone run", lambda j: f"={I('lz_run')}*{T('lz', j)}", "Same as VCF track")
total("a_plat", "AZURE PLATFORM TCO (excl. new capabilities)", ["a_vmw", "a_vdf", "a_hz", "a_avd", "a_host", "a_mt", "a_cap", "a_fte", "a_one"] + a_common)
total("a", "AZURE TRACK TOTAL", ["a_plat", "a_gov", "a_lz"])
row += 1

band("Comparisons")
S = {}


def cmp(key, label, formula_fn, fmt=CUR):
    global row
    put(F, row, 1, label, bold=True)
    for j in range(6):
        col = L(2 + j)
        put(F, row, 2 + j, formula_fn(col), BLACK, fmt, TOTAL, True)
    R[key] = row
    row += 1


cmp("d_sq", "Status quo − Azure platform TCO (NFR-10 margin; positive = Azure cheaper)", lambda c: f"={c}{R['sq']}-{c}{R['a_plat']}")
cmp("d_v", "VCF track − Azure track (positive = Azure cheaper)", lambda c: f"={c}{R['v']}-{c}{R['a']}")
put(F, row, 1, "Cumulative NFR-10 margin", bold=True)
for j in range(5):
    col = L(2 + j)
    f = f"={col}{R['d_sq']}" if j == 0 else f"={L(1 + j)}{row}+{col}{R['d_sq']}"
    put(F, row, 2 + j, f, BLACK, CUR, bold=True)
R["cum_sq"] = row
row += 2
put(F, row, 1, "Steady-state recurring run-rate, Y5 (excl. capex and one-time)", bold=True)
row += 1
RR = {}
for key, label, tot, excl in (("rr_sq", "  Status quo", "sq", ["sq_cap", "sq_res"]),
                               ("rr_v", "  VCF track", "v", ["v_cap", "v_one", "v_res"]),
                               ("rr_a", "  Azure track", "a", ["a_cap", "a_one", "a_res"])):
    put(F, row, 1, label)
    put(F, row, 6, f"=F{R[tot]}-" + "-".join(f"F{R[k]}" for k in excl), BLACK, CUR, TOTAL, True)
    RR[key] = f"FiveYearTCO!$F${row}"
    row += 1

ch = BarChart()
ch.type = "col"
ch.title = "Annual cost by path (illustrative)"
for k in ("sq", "v", "a"):
    ch.add_data(Reference(F, min_col=1, max_col=6, min_row=R[k], max_row=R[k]), titles_from_data=True, from_rows=True)
ch.set_categories(Reference(F, min_col=2, max_col=6, min_row=4, max_row=4))
ch.height, ch.width = 8, 18
F.add_chart(ch, f"A{row + 2}")

# ============================================================
# ThresholdTest (gate G0-2) + NFR-10 + AHB sensitivity
# ============================================================
G = wb.create_sheet("ThresholdTest")
widths(G, [74, 18, 24, 62])
G["A1"] = "Gate G0-2: Broadcom Threshold Price, NFR-10 Test, and Azure Hybrid Benefit Sensitivity"
G["A1"].font = TITLE
hdr(G, 3, ["Test", "Value", "Result", "Basis"])
g = 4
GR = {}


def gt(key, label, f, fmt, result=None, basis="", bold=False):
    global g
    put(G, g, 1, label, bold=bold)
    put(G, g, 2, f, BLACK, fmt, None, bold)
    put(G, g, 3, result, BLACK, None, TOTAL if result else None, True)
    put(G, g, 4, basis).font = NOTE
    GR[key] = f"B{g}"
    g += 1


def gband(t):
    global g
    for c in range(1, 5):
        put(G, g, c, t if c == 1 else None, bold=True, fill=SUB)
    g += 1


gband("1. NFR-10: Azure platform TCO ≤ status quo (5 years)")
gt("sq5", "Status quo 5-yr TCO", f"=FiveYearTCO!G{R['sq']}", CUR, None, "FiveYearTCO")
gt("az5", "Azure platform 5-yr TCO (excl. new capabilities)", f"=FiveYearTCO!G{R['a_plat']}", CUR,
   f'=IF(B{g}<=B{g - 1},"PASS","FAIL")', "FiveYearTCO")
gt("m5", "Margin", f"={GR['sq5']}-{GR['az5']}", CUR, None, "")
gt("rr", "Steady-state run-rate saving, Y5 (status quo − Azure)", f"={RR['rr_sq']}-{RR['rr_a']}", CUR, None, "Recurring only")
g += 1
gband("2. Azure Hybrid Benefit sensitivity (verify at G0-2)")
gt("ahb0", "Extra 5-yr host fees if Hybrid Benefit covered 0% of cores",
   f"={I('host_fee')}*{I('az_cores')}*12*(0.3+0.8+1+1+1)*{I('ahb')}", CUR, None, "Fees currently waived × estate ramp")
gt("ahb_t", "NFR-10 margin with 0% Hybrid Benefit", f"={GR['m5']}-{GR['ahb0']}", CUR,
   f'=IF(B{g}>=0,"still PASS","FAILS")', "")
g += 1
gband("3. Gate G0-2: the renewal price at which VCF would win")
gt("gap", "VCF track − Azure track, 5-yr, at the quote (G)", f"=FiveYearTCO!G{R['v']}-FiveYearTCO!G{R['a']}", CUR, None, "Both include the same new capabilities")
gt("bv", "VCF-track sensitivity to the renewal price (years-equivalent)",
   f"=(SUM(Assumptions!$B${TL['ren_m']}:$F${TL['ren_m']})+SUM(Assumptions!$B${TL['up_m']}:$F${TL['up_m']})*(1+{I('vcf_up')}))/12", DEC, None, "Δ5-yr TCO per $1 of annual price")
gt("ba", "Azure-track sensitivity (bridge months at premium)",
   f"=SUM(Assumptions!$B${TL['br_m']}:$F${TL['br_m']})*(1+{I('br_prem')})/12", DEC, None, "The bridge is priced off the same quote")
gt("share", "Share of the cost gap VCF must close to reach the flip score",
   f"=({I('sc_flip')}-{I('sc_vcf')})/({I('sc_az')}-{I('sc_vcf')})", PCT, None, "Linear score ↔ TCO mapping: (3.5 − 2) ÷ (4.5 − 2)")
gt("p_flip", "THRESHOLD: annual VCF price at which the decision flips (cost score 3.5)",
   f"={I('vcf_quote')}-{GR['share']}*{GR['gap']}/({GR['bv']}-{GR['ba']})", CUR, None,
   "If Broadcom's best 3-yr offer is BELOW this, G0-2 reverses ADR-031 to VCF", True)
gt("p_flip_pct", "  discount from the quote", f"=1-{GR['p_flip']}/{I('vcf_quote')}", PCT, None, "")
gt("p_par", "Parity price (5-yr TCO equal)", f"={I('vcf_quote')}-{GR['gap']}/({GR['bv']}-{GR['ba']})", CUR, None, "")
gt("p_par_pct", "  discount from the quote", f"=1-{GR['p_par']}/{I('vcf_quote')}", PCT, None, "")
G.cell(row=GR["p_flip"][1:] and int(GR["p_flip"][1:]), column=2).fill = YELLOW
g += 1
gband("4. Oracle consolidation lever (platform-neutral; not in the path totals)")
gt("ora_l0", "Processor licences today", f"={I('ora_cores')}*{I('ora_cf')}", NUM, None, "cores × core factor")
gt("ora_l1", "Processor licences after consolidation", f"={I('ora_new')}*{I('ora_cf')}", NUM, None, "")
gt("ora_sav", "Potential annual support saving", f"=({GR['ora_l0']}-{GR['ora_l1']})*{I('ora_sup')}", CUR, None,
   "Realizable only if licences are terminated — subject to Oracle's repricing policy")

for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False
F.freeze_panes = "B5"
wb.save("TCO-Analysis.xlsx")
print("saved TCO-Analysis.xlsx")
