"""投稿就绪门 v1.1（2026-11-20 晚，第3轮修订后）：验证清洁投稿产物是否满足"可提交"条件。
与 gate_submission_package（一致性门，验证审计源稿 v0.3）分工不同：
本门验证 v1.0 清洁版稿件/摘要/cover letter/docx。

v1.1 变更（源自第3轮终审编辑意见 #6）：
- 占位符检查由 WARN 升级为硬 FAIL；
- 删除 "eight of nine" or "eight" 恒真分支，改为精确短语；
- 新增检查面：作者块、缩写定义、参考文献 [1]-[5] 正文引用、首次出现顺序、
  Table 1-4 文内引用、docx 零中文字符、审计注剥除、Version 行剥除。
Run: python submission/bmc-hsr/gate_submission_ready_v1.0.py
"""
import os, re, sys
from docx import Document

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CLEAN_MS = os.path.join(ROOT, "manuscript", "methodological-appraisal-chinese-expert-consensus_v1.0_clean.md")
SUBMIT_MS = os.path.join(ROOT, "manuscript", "methodological-appraisal-chinese-expert-consensus_v1.3_revised.md")
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
                "9918" + "14801@qq.com", "confirm the CRediT", "标题前五", "待投稿", "占位符待填"]:
        chk(f"{label}: no '{bad}'", bad not in txt)

# --- 摘要四段结构（docx 去星号；md 带星号）---
for seg in ["Background", "Methods", "Results", "Conclusions"]:
    chk(f"clean manuscript: abstract has {seg}", f"**{seg}**:" in clean)
    chk(f"docx: abstract has {seg}", f"{seg}:" in docx_text)

# --- 编号转换：正文无裸共识编号（注意：[1]-[5] 已于第3轮合法化为论文编号，勿列入禁表）---
body = submit[submit.find("## 1 Introduction"):submit.find("## Tables")]
for old in ["[25]", "[26]", "[27]", "[42]", "[43]", "[47]", "[37–41]", "[46]"]:
    chk(f"submit body: no residual consensus label {old}", old not in body)
for new in ["[6]", "[7]", "[8]", "[9]", "[10]", "[11]", "[12]", "[13]"]:
    chk(f"submit body: journal number {new} present", new in body)

# --- 第3轮新增：参考文献 [1]-[5] 必须被正文引用且首次出现升序 ---
pos45 = body.find("[4,5]")
firsts = []
for n in range(1, 14):
    x = body.find(f"[{n}]")
    if n in (4, 5) and pos45 != -1 and (x == -1 or x > pos45):
        x = pos45
    firsts.append(x)
chk("submit body: refs [1]-[13] all cited", all(x != -1 for x in firsts))
chk("submit body: first-appearance order ascending", firsts == sorted(firsts))

# --- 第3轮新增：作者块 / 缩写定义 / Version 行 ---
for tok in ["**Authors**: Yongxin Yang", "Jie Hu", "960856791@qq.com", "0009-0004-9698-6552"]:
    chk(f"submit: author block has {tok}", tok in submit)
chk("docx: author block (names/email/ORCID)", all(x in docx_text for x in ["Yongxin Yang", "Jie Hu", "960856791@qq.com", "0009-0004-9698-6552"]))
chk("docx: no internal Version line", "Version:" not in docx_text)
chk("docx: no audit notes in references", "[Consensus reference" not in docx_text and "[Appraisal object" not in docx_text)
for tok in ["Appraisal of Guidelines for Research and Evaluation II",
            "Reporting Items for Practice Guidelines in Healthcare",
            "Grading of Recommendations Assessment, Development and Evaluation",
            "## Abbreviations"]:
    chk(f"submit: abbreviation defined ({tok[:40]}...)", tok in submit)
chk("docx: abbreviations section present", "Abbreviations" in docx_text)

# --- 第3轮新增：docx 零中文字符（Table 3/4 中文渗入修复）---
cjk = re.findall(r"[\u4e00-\u9fff]", docx_text)
chk("docx: zero CJK characters", len(cjk) == 0)

# --- 第3轮新增：Table 1-4 文内引用 ---
chk("submit body: (Table 1)-(Table 4) cited", all(f"(Table {n})" in body for n in range(1, 5)))
chk("docx: (Table 1)-(Table 4) cited", all(f"(Table {n})" in docx_text for n in range(1, 5)))

# --- 关键数字（与权威 JSON 交叉核对）---
import json
agree = json.load(open(os.path.join(ROOT, "audit", "consensus_2026", "agree2_interrater_reliability_2026-11-19.json"), encoding="utf-8"))
grade = json.load(open(os.path.join(ROOT, "audit", "consensus_2026", "grade_interrater_reliability_2026-11-20.json"), encoding="utf-8"))
for tok in ["39.1%", "0.258", "0.651", "0.853", "0.663", "0.941", "44.4%", "41.7%", "83.3%"]:
    chk(f"docx carries {tok}", tok in docx_text)
chk("docx notes 9/9 certainty agreement", "9/9" in docx_text)
chk("docx: exact phrase 'eight of nine'", "eight of nine" in docx_text)
# 期望值从 JSON 派生
ic = agree["interrater"]["icc_21"] if "interrater" in agree else agree.get("primary", {}).get("icc_21")
if ic is not None:
    chk(f"docx ICC matches JSON ({ic})", f"{ic:.3f}" in docx_text)

# --- 4 张表 + 补充材料 ---
chk("docx has exactly 4 tables", len(d.tables) == 4)
chk("docx table row counts", [len(t.rows) for t in d.tables] == [31, 37, 10, 6])
chk("docx has Supplementary material", "Supplementary material" in docx_text)

# --- Akl RIGHT 披露句（作者 2026-11-20 改判恢复；cover letter 必须含披露句，稿件正文不含）---
chk("cover letter: Akl RIGHT disclosure restored", "co-author of the RIGHT statement" in cl)
chk("docx: no Akl RIGHT disclosure", "co-author of the RIGHT statement" not in docx_text)

# --- 投稿确认清单 ---
chk("submission checklist file exists", os.path.exists(CHK))
chk("checklist states all reviewers un-contacted", "均未联系" in open(CHK, encoding="utf-8").read())

# --- Data availability：占位符为硬失败；真实 URL/tag 已回填 ---
chk("docx: no REPOSITORY URL placeholder", "[REPOSITORY URL]" not in docx_text)
chk("docx: no ZENODO DOI placeholder", "[ZENODO DOI]" not in docx_text)
chk("docx: real repository URL present", "github.com/yyx-4113/neuromodulation-limb-salvage-diabetic-foot" in docx_text)
chk("docx: release tag v1.3.0 present", "under release v1.3.0" in docx_text)
chk("docx: real Zenodo DOI present", "doi:10.5281/zenodo.24461453" in docx_text)
chk("docx: no deferred-DOI wording", "will be assigned on acceptance" not in docx_text)
chk("submit source: real Zenodo DOI present", "doi:10.5281/zenodo.24461453" in submit)
chk("cover letter: real Zenodo DOI present", "doi:10.5281/zenodo.24461453" in cl)
chk("cover letter: no deferred-DOI wording", "archival DOI will be assigned on acceptance" not in cl)

print("\n" + ("SUBMISSION-READY GATE: ALL PASS" if not fails else f"SUBMISSION-READY GATE: {len(fails)} FAIL(s): {fails}"))
sys.exit(1 if fails else 0)
