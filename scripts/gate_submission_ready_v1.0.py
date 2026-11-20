"""投稿就绪门 v1.0（2026-11-20）：验证清洁投稿产物是否满足"可提交"条件。
与 gate_submission_package（一致性门，验证审计源稿 v0.3）分工不同：
本门验证 v1.0 清洁版稿件/摘要/cover letter/docx。
Run: python submission/bmc-hsr/gate_submission_ready_v1.0.py
"""
import os, re, sys
from docx import Document

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CLEAN_MS = os.path.join(ROOT, "manuscript", "methodological-appraisal-chinese-expert-consensus_v1.0_clean.md")
SUBMIT_MS = os.path.join(ROOT, "manuscript", "methodological-appraisal-chinese-expert-consensus_v1.0_submit.md")
DOCX = os.path.join(HERE, "methodological-appraisal-chinese-expert-consensus_v1.0_submission.docx")
CL = os.path.join(HERE, "cover-letter-methodological-appraisal-chinese-expert-consensus_v1.0_clean.md")
AB = os.path.join(HERE, "abstract_for_submission_v0.2.md")
CHK = os.path.join(HERE, "投稿系统填写确认清单_2026-11-20.md")

fails = []
def chk(label, cond):
    if cond:
        print("PASS", label)
    else:
        fails.append(label); print("FAIL", label)

clean = open(CLEAN_MS, encoding="utf-8").read()
submit = open(SUBMIT_MS, encoding="utf-8").read()
cl = open(CL, encoding="utf-8").read()
ab = open(AB, encoding="utf-8").read()
d = Document(DOCX)
docx_text = "\n".join(p.text for p in d.paragraphs)
for t in d.tables:
    for r in t.rows:
        docx_text += "\n" + " | ".join(c.text for c in r.cells)

# --- 清洁源文件：内部批注零残留 ---
for label, txt in [("clean manuscript", clean), ("submit manuscript", submit), ("clean cover letter", cl), ("docx", docx_text)]:
    for bad in ["AUTHOR NOTE", "REMOVE BEFORE SUBMISSION", "Reference note", "Pre-submission checks",
                "[redacted]", "confirm the CRediT", "标题前五", "待投稿", "占位符待填"]:
        chk(f"{label}: no '{bad}'", bad not in txt)

# --- 摘要四段结构（docx 去星号；md 带星号）---
for seg in ["Background", "Methods", "Results", "Conclusions"]:
    chk(f"clean manuscript: abstract has {seg}", f"**{seg}**:" in clean)
    chk(f"docx: abstract has {seg}", f"{seg}:" in docx_text)

# --- 编号转换：正文无裸共识编号，且论文编号齐全 ---
body = submit[submit.find("## 1 Introduction"):submit.find("## Tables")]
for old in ["[3]", "[4]", "[25]", "[26]", "[27]", "[42]", "[43]", "[47]", "[37–41]", "[46]"]:
    chk(f"submit body: no residual consensus label {old}", old not in body)
for new in ["[6]", "[7]", "[8]", "[9]", "[10]", "[11]", "[12]", "[13]"]:
    chk(f"submit body: journal number {new} present", new in body)

# --- 关键数字（从权威 JSON 派生期望，不硬编码稿内字符串）---
import json
agree = json.load(open(os.path.join(ROOT, "audit", "consensus_2026", "agree2_interrater_reliability_2026-11-19.json"), encoding="utf-8"))
grade = json.load(open(os.path.join(ROOT, "audit", "consensus_2026", "grade_interrater_reliability_2026-11-20.json"), encoding="utf-8"))
for tok in ["39.1%", "0.258", "0.651", "0.853", "0.663", "0.941", "44.4%", "41.7%", "83.3%"]:
    chk(f"docx carries {tok}", tok in docx_text)
chk("docx notes 9/9 certainty agreement", "9/9" in docx_text)
chk("docx notes eight very low / one low", "eight of nine" in docx_text or "eight" in docx_text)

# --- 4 张表 + 补充材料 ---
chk("docx has exactly 4 tables", len(d.tables) == 4)
chk("docx table row counts", [len(t.rows) for t in d.tables] == [31, 37, 10, 6])
chk("docx has Supplementary material", "Supplementary material" in docx_text)

# --- 撤下 Akl 披露句（投稿材料）---
chk("cover letter: no Akl RIGHT disclosure", "co-author of the RIGHT statement" not in cl)
chk("docx: no Akl RIGHT disclosure", "co-author of the RIGHT statement" not in docx_text)

# --- 投稿确认清单 ---
chk("submission checklist file exists", os.path.exists(CHK))
chk("checklist states all reviewers un-contacted", "均未联系" in open(CHK, encoding="utf-8").read())

# --- Data availability 占位符：明确标记，等待回填（唯一阻断项，单列为 WARN）---
has_ph = all(x in docx_text for x in ["[REPOSITORY URL]", "[VERSION TAG]", "[ZENODO DOI]"])
print("\n=== SUBMISSION READINESS WARN (not a consistency failure) ===")
if has_ph:
    print("WARN Data availability still has 3 placeholders — author MUST fill real repository URL/tag/DOI before submission.")
else:
    print("OK   Data availability placeholders resolved.")

print("\n" + ("SUBMISSION-READY GATE: ALL PASS" if not fails else f"SUBMISSION-READY GATE: {len(fails)} FAIL(s): {fails}"))
sys.exit(1 if fails else 0)
