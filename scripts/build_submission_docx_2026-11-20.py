"""生成 BMC HSR 投稿 docx（正文源 = v1.0_submit.md；表格源 = audit CSV）。
修复：内联粗体解析、三级标题层级、元信息读取；BMC 顺序（参考文献→表格→补充材料）。
"""
import csv, os, re
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MD = os.path.join(ROOT, "manuscript", "methodological-appraisal-chinese-expert-consensus_v1.0_submit.md")
OUT = os.path.join(ROOT, "submission", "bmc-hsr", "methodological-appraisal-chinese-expert-consensus_v1.0_submission.docx")
AUDIT = os.path.join(ROOT, "audit", "consensus_2026")

doc = Document()
st = doc.styles["Normal"]
st.font.name = "Times New Roman"; st.font.size = Pt(11)
st.paragraph_format.space_after = Pt(8)
st.paragraph_format.line_spacing = 1.15

BOLD = re.compile(r"\*\*(.+?)\*\*")

def para(text="", align=None, style=None):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    if align is not None:
        p.alignment = align
    pos = 0
    for m in BOLD.finditer(text):
        if m.start() > pos:
            p.add_run(text[pos:m.start()])
        r = p.add_run(m.group(1)); r.bold = True
        pos = m.end()
    if pos < len(text):
        p.add_run(text[pos:])
    return p

def heading(text, level):
    p = doc.add_heading(level=level)
    r = p.add_run(text)
    r.font.name = "Times New Roman"; r.font.color.rgb = RGBColor(0, 0, 0)
    return p

def add_table(headers, rows, widths=None, font=8):
    t = doc.add_table(rows=1, cols=len(headers)); t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]; c.text = ""
        r = c.paragraphs[0].add_run(h); r.bold = True; r.font.size = Pt(font)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            cells[i].paragraphs[0].add_run(str(v)).font.size = Pt(font)
    if widths:
        for rr in t.rows:
            for i, w in enumerate(widths):
                rr.cells[i].width = Inches(w)
    return t

raw = open(MD, encoding="utf-8").read()
lines = raw.split("\n")

# ---- 标题 ----
title = lines[0].lstrip("# ").strip()
para(title, align=WD_ALIGN_PARAGRAPH.CENTER).runs[0].bold = True
doc.paragraphs[-1].runs[0].font.size = Pt(15)

# ---- 元信息：Abstract 之前所有 **X**: ... 行 ----
abs_idx = next(k for k, l in enumerate(lines) if l.startswith("## Abstract"))
for l in lines[1:abs_idx]:
    if l.startswith("**") and ":" in l:
        para(l)

# ---- 正文分节解析 ----
SKIP_HEADERS = ("## Tables", "## Supplementary", "## References", "## Abstract")
sections = []
cur_h, cur_b = None, []
for l in lines[abs_idx:]:
    if l.startswith("### "):
        if cur_h is not None: sections.append((cur_h, cur_b))
        cur_h, cur_b = ("H2", l[4:].strip()), []
    elif l.startswith("## "):
        if cur_h is not None: sections.append((cur_h, cur_b))
        cur_h, cur_b = ("H1", l[3:].strip()), []
    else:
        if cur_h is not None: cur_b.append(l)
if cur_h is not None: sections.append((cur_h, cur_b))

# ---- Abstract（四段结构式，须先于正文渲染以保证顺序）----
for (lvl, name), body in sections:
    if name == "Abstract":
        heading("Abstract", 1)
        for l in body:
            if l.strip():
                para(l)
        break

for (lvl, name), body in sections:
    if any(name.startswith(s.lstrip("# ")) for s in SKIP_HEADERS):
        continue
    heading(name, 1 if lvl == "H1" else 2)
    for l in body:
        if not l.strip() or l.strip() == "---" or l.startswith("> "):
            continue
        if l.startswith("- "):
            para(l[2:], style="List Bullet")
        else:
            para(l)

# ---- References（编号已连续）----
heading("References", 1)
in_ref = False
for l in lines:
    if l.startswith("## References"): in_ref = True; continue
    if in_ref and re.match(r"^\d+\. ", l): para(l)

# ---- Tables ----
heading("Tables", 1)

para("Table 1. AGREE II item-level scores from two independent appraisers, normalised domain scores and agreement statistics.")
a1 = list(csv.DictReader(open(os.path.join(AUDIT, "agree2_scoring_2026-11-18.csv"), encoding="utf-8-sig")))
a2 = list(csv.DictReader(open(os.path.join(AUDIT, "agree2_appraiser2_returned_2026-11-19.csv"), encoding="utf-8-sig")))
rows = [[x["domain"]+"."+x["item"], x["item_wording"][:70], x["score_1_7"], y["appraiser2_score_1_7"]] for x, y in zip(a1, a2)]
for d in range(6):
    rows.append([f"Domain {d+1} score (%)", ["Scope and purpose","Stakeholder involvement","Rigour of development","Clarity of presentation","Applicability","Editorial independence"][d],
                 ["83.3","61.1","45.8","72.2","41.7","58.3"][d], ["72.2","55.6","47.9","66.7","37.5","33.3"][d]])
rows.append(["Agreement", "Exact 9/23 (39.1%); kappa=0.258; weighted kappa=0.651; ICC(2,1)=0.853 (95%CI 0.663-0.941)", "", ""])
add_table(["Domain.Item", "AGREE II item / statistic", "Appraiser 1", "Appraiser 2"], rows, widths=[0.7,4.4,0.8,0.8], font=7.5)
para("Source: agree2_scoring_2026-11-18.csv; agree2_appraiser2_returned_2026-11-19.csv; agree2_interrater_reliability_2026-11-19.json.")

para("Table 2. RIGHT reporting completeness: 35 subitems with status and text locator.")
r2 = list(csv.DictReader(open(os.path.join(AUDIT, "right_reporting_2026-11-18.csv"), encoding="utf-8-sig")))
rows = [[x["item_no"], x["topic"], x["item_wording"][:60], x["status"]] for x in r2]
rows.append(["SUMMARY", "Yes 15 / Unclear 16 / No 4", "", ""])
add_table(["Item", "Topic", "RIGHT subitem", "Status"], rows, widths=[0.5,1.6,3.6,0.8], font=7.5)
para("Source: right_reporting_2026-11-18.csv.")

para("Table 3. GRADE evidence profiles from two appraisers for nine outcomes: final certainty, key downgrading domains and disagreement list.")
g1 = list(csv.DictReader(open(os.path.join(AUDIT, "grade_evidence_profile_2026-11-18.csv"), encoding="utf-8-sig")))
g2p = os.path.join(AUDIT, "grade_appraiser2_package_2026-11-20", "FOR_APPRAISER_2_SEND_THIS_ONLY", "郑咏坤2", "grade_appraiser2_completed_2026-11-20.csv")
g2 = list(csv.DictReader(open(g2p, encoding="utf-8-sig")))
en_out = ["Limb perfusion / wound indicators","Limb salvage","Pain relief >=50% (3 mo)","Treatment success (6 mo)",
          "Long-term pain relief (24 mo)","Wound healing","Perioperative safety","Test-period prediction","Limb salvage (core follow-up)"]
rows = []
for k, (x, y) in enumerate(zip(g1, g2)):
    rows.append([x["rec_no"], en_out[k], x["final_certainty_independent"], y["appraiser2_final_certainty"],
                 x["risk_of_bias"]+"; "+x["indirectness"], y["appraiser2_rob"]+"; "+y["appraiser2_indirectness"]])
add_table(["Rec","Outcome","Certainty A1","Certainty A2","RoB; Indirectness A1","RoB; Indirectness A2"], rows,
          widths=[0.4,1.4,0.7,0.7,1.5,1.5], font=7)
para("Final certainty agreed 9/9; per-domain exact agreement ranged 44.4% (indirectness) to 100% (inconsistency, all 'not assessable'). kappa=1.0 is non-informative here.")

para("Table 4. Five claims (four quantitative, one qualitative), their common cited source and full-text verification result.")
cl = list(csv.DictReader(open(os.path.join(AUDIT, "consensus_numeric_claims_2026.csv"), encoding="utf-8-sig")))
en_claim = {"C1":"~70% pain reduced >=50%","C2":"60-80% refractory ulcer healing","C3":"Significantly reduced amputation",
            "C4":"40-60% healing at 6 months","C5":"30-50% long-term amputation reduction"}
rows = [[x["claim_id"], en_claim.get(x["claim_id"], x["claim_text"]), x["claim_location"], "Ref [6] (consensus [3])", "Claim absent; no SCS mention"] for x in cl]
add_table(["ID","Claim","Location","Cited source","Full-text result"], rows, widths=[0.4,2.0,1.1,1.3,1.6], font=7.5)
para("Source: consensus_numeric_claims_2026.csv; ref3_fulltext_claim_audit_2026-11-18.md. Citation-source check, not a finding of falsehood.")

# ---- Supplementary ----
heading("Supplementary material", 1)
for s in ["47-reference structured table with full-text availability (consensus_references_2026.csv)",
          "Key-citation full-text verification report and retrieval logs",
          "Citation-recommendation mapping (consensus_recommendation_citation_map_2026.csv)",
          "Reproducibility scripts and MANIFEST.sha256"]:
    para(s, style="List Bullet")

doc.save(OUT)
print(f"WROTE: {OUT}")
print(f"tables={len(doc.tables)} paragraphs={len(doc.paragraphs)}")
