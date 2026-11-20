# -*- coding: utf-8 -*-
"""投稿包文本一致性 gate：cover letter / 投稿摘要 / 清单 / 稿件 与权威产物交叉核对。

纪律：期望值全部从权威产物（JSON/CSV/正文）派生，禁止硬编码旧数字。
范围声明：本 gate 仅验证"文本与权威产物交叉一致"，不代表"可投稿"。
投稿就绪（占位符、内部批注、CRediT、作者确认）由文件末尾 READINESS 块单独提示，不计入一致性 PASS。
Run: python gate_submission_package_2026-11-20.py
"""
import csv, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))  # 项目根
AUDIT = os.path.join(ROOT, "audit", "consensus_2026")

CL = os.path.join(HERE, "cover-letter-methodological-appraisal-chinese-expert-consensus_v0.1.md")
AB = os.path.join(HERE, "abstract_for_submission_v0.2.md")
CH = os.path.join(HERE, "submission_checklist_v0.1.md")
MS = os.path.join(ROOT, "manuscript", "methodological-appraisal-chinese-expert-consensus_v0.3.md")
REL = os.path.join(AUDIT, "grade_interrater_reliability_2026-11-20.json")
AG = os.path.join(AUDIT, "agree2_interrater_reliability_2026-11-19.json")
REFMAN = os.path.join(HERE, "manuscript_references_final_2026-11-20.csv")
REF47 = os.path.join(HERE, "consensus_references_submission_final_2026-11-20.csv")
REFMD = os.path.join(HERE, "reference_table_final_2026-11-20.md")
REVIEWERS = os.path.join(HERE, "suggested_reviewers_2026-11-20.md")

fails = []
def chk(label, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + label + ((" | " + detail) if detail else ""))
    if not cond:
        fails.append(label)

cl = open(CL, encoding="utf-8").read()
ab = open(AB, encoding="utf-8").read()
ch = open(CH, encoding="utf-8").read()
ms = open(MS, encoding="utf-8").read()
rel = json.load(open(REL, encoding="utf-8"))
ag = json.load(open(AG, encoding="utf-8"))

# --- 从权威 JSON 派生期望值（不硬编码）---
pd = rel["primary"]["per_domain_exact_agreement"]
ind = f"{pd['间接性']*100:.1f}%"          # 44.4%
inc = f"{pd['不一致性']*100:.0f}%"        # 100%
agree = rel["primary"]["final_certainty_agreement_count"]  # 9/9
# AGREE II 期望值从 agree2 JSON 派生（原为硬编码，v0.3 修正）
a_exact = f"{ag['percent_exact_agreement_pct']:.1f}%"       # 39.1%
a_d1 = f"{ag['domains']['1']['appraiser1_pct']:.1f}%"       # 83.3%
a_d5 = f"{ag['domains']['5']['appraiser1_pct']:.1f}%"       # 41.7%
a_icc = f"{ag['ICC_2_1_absolute_agreement']:.3f}"            # 0.853
a_lo = f"{ag['ICC_2_1_95CI'][0]:.3f}"                        # 0.663
a_hi = f"{ag['ICC_2_1_95CI'][1]:.3f}"                        # 0.941
a_k = f"{ag['cohen_kappa_unweighted']:.3f}"                  # 0.258
a_kw = f"{ag['cohen_kappa_linear_weighted']:.3f}"            # 0.651

# 摘要：词数与四段
body = ab[ab.index("**Background**:"):ab.index("**Keywords**:")]
wc = len(re.findall(r"[A-Za-z0-9'+.-]+", body))
chk("abstract <=350 words", wc <= 350, f"{wc} words")
chk("abstract four sections", all(f"**{s}**:" in body for s in ["Background","Methods","Results","Conclusions"]))
chk("abstract no Objective section", "**Objective**:" not in body)

# GRADE 双评一致性数字（cover letter 与摘要都须与 JSON 一致）
chk("abstract final-certainty agreement present", "all nine outcomes" in ab)
chk("abstract indirectness rate from JSON", ind in ab, ind)
chk("cover letter dual GRADE appraisers", "Two independent appraisers reached identical final certainty" in cl)
chk("JSON complete", rel["status"] == "COMPLETE")

# 域级一致率派生值须在正文与摘要（间接性）；改为精确匹配（原 "100" in ms 恒真）
chk("manuscript indirectness from JSON", ind in ms, ind)
chk("manuscript inconsistency from JSON", inc in ms, inc)
chk("abstract indirectness caveat present", "not assessable" in ab)

# AGREE II 核心数字全部从 agree2 JSON 派生（原为字面硬编码，v0.3 修正）
a_nums = [a_exact, a_d1, a_d5, a_icc, a_lo, a_hi]
for num in a_nums:
    chk(f"cover letter carries AGREE {num}", num in cl)
    chk(f"abstract carries AGREE {num}", num in ab)
for num in [a_k, a_kw]:
    chk(f"abstract carries kappa {num}", num in ab)

# 一致性声明修正：封面信不得再写"same ordering"
chk("cover letter drops false 'same ordering'", "same ordering" not in cl.lower())
chk("abstract drops false 'same ordering'", "same ordering" not in ab.lower())
# 域分排序 ρ 披露（正文）
chk("manuscript discloses domain-rank Spearman rho", "0.83" in ms)

# [3] 来源与 NNT 溯源修正
chk("manuscript [3] source = author-supplied PDF", "author" in ms.lower() and "document collection" in ms.lower())
chk("manuscript no interlibrary claim", "interlibrary" not in ms.lower())
chk("manuscript composite endpoint stated", "neurological deterioration" in ms)
chk("manuscript NNT marked as derived", "derived number needed to treat" in ms)
chk("manuscript five→five indirectness", "five DF-relevant outcomes" in ms)

# 引文错配事实一致（cover letter 正文用克制措辞 source-claim mismatch / not a determination about intent）
chk("cover letter source-claim mismatch framing", "source" in cl.lower() and "mismatch" in cl.lower())

# 禁用串检查：只在"投稿正文"检查，排除 AUTHOR NOTE 与中文提示行（那些是禁用提示本身，非违规内容）
def submission_text(text):
    # 去掉引用块（> 开头的 AUTHOR NOTE / 提示）与中文"不得/严禁"提示所在行
    lines = [ln for ln in text.splitlines()
             if not ln.strip().startswith(">")
             and not any(k in ln for k in ("不得写", "严禁", "do not describe", "no fabricated", "not as a determination"))]
    return "\n".join(lines)

cl_body = submission_text(cl)
ab_body = submission_text(ab)
ch_body = submission_text(ch)
all_body = cl_body + ab_body + ch_body
chk("no fabrication/misconduct claim in submission text",
    not any(x in all_body.lower() for x in ["fabricated", "misconduct", "造假", "data fabrication"]))
chk("no request-based data wording in submission text", "available on request" not in all_body.lower())
chk("no '已豁免' in submission text", "已豁免" not in all_body)
chk("no 'achieved consensus' claim in submission text",
    not any(x in (cl_body+ab_body).lower() for x in ["achieved consensus", "domain-level consensus", "consensus was reached"]))

# 文件结构与占位（这些在提示/清单里是正常的）
rv = open(REVIEWERS, encoding="utf-8").read()
rev_emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", rv)))
rev_orcids = sorted(set(re.findall(r"\b\d{4}-\d{4}-\d{4}-\d{3}[0-9X]\b", rv)))
chk("reviewer file has 3 ORCIDs and institutional emails",
    len(rev_orcids) == 3 and len(rev_emails) >= 3, f"{len(rev_orcids)} ORCIDs / {len(rev_emails)} emails")
rev_para = cl[cl.index("**Suggested reviewers"):cl.index("We confirm that this manuscript")]
cl_rev_orcids = sorted(set(re.findall(r"\b\d{4}-\d{4}-\d{4}-\d{3}[0-9X]\b", rev_para)))
cl_rev_emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", rev_para)))
chk("all suggested reviewer ORCIDs present in cover letter", all(o in cl for o in rev_orcids))
chk("cover-letter reviewer emails trace to source file",
    len(cl_rev_orcids) == 3 and len(cl_rev_emails) == 3
    and all(e in rv for e in cl_rev_emails) and all(o in rv for o in cl_rev_orcids),
    f"{len(cl_rev_orcids)} ORCIDs / {len(cl_rev_emails)} emails")
chk("checklist reviewer section has no placeholder names",
    "姓名 / 单位 / 邮箱" not in ch.split("## 4")[1].split("## 5")[0])
chk("checklist reviewer entries await author confirmation", "待作者确认" in ch)
chk("reviewer suggestions flagged as uncontacted",
    "has been contacted or has agreed" in cl and "none" in cl.lower())
# AUTHOR NOTE 存在不是"合规"证据，仅登记为待清理项（不计入一致性 FAIL）
chk("cover letter AUTHOR NOTE flagged for removal", "AUTHOR NOTE" in cl)
chk("manuscript AUTHOR NOTE flagged for removal", "AUTHOR NOTE" in ms)
chk("checklist marks red blockers", "必补" in ch)
chk("submission URL from verified report", "submission.nature.com/new-submission/12913/3" in ch)

# 命名纪律：文件名含标题前 5 实词
chk("cover letter filename prefix", "methodological-appraisal-chinese-expert-consensus" in os.path.basename(CL))

# --- 参考文献定稿（期望值从定稿 CSV 派生，不硬编码）---
refman = list(csv.DictReader(open(REFMAN, encoding="utf-8-sig")))
ref47 = {r["ref_no"]: r for r in csv.DictReader(open(REF47, encoding="utf-8-sig"))}
refmd = open(REFMD, encoding="utf-8").read()
chk("manuscript reference table has 13 rows", len(refman) == 13, str(len(refman)))
r3 = next(r for r in refman if r["manuscript_ref_no"] == "3")
chk("[11] page corrected in reference note and 47-table",
    "e0014323" in ms and "e0014323" in refmd)
chk("[9] EJVES target in submission 47-table",
    "Eur J Vasc Endovasc Surg" in ref47["9"]["journal"] and ref47["9"]["vol_issue_pages"] == "66(4):454-483")
chk("[11] page target in submission 47-table", ref47["11"]["vol_issue_pages"] == "37(3):e0014323")
chk("RIGHT first author corrected in final CSV", "Chen Y" in r3["citation"] and "Culvenor" not in r3["citation"])
for r in refman:
    chk(f"doi in manuscript: ref {r['manuscript_ref_no']}", r["doi"].lower() in ms.lower(), r["doi"])
chk("no stale Culvenor attribution in manuscript", "Culvenor" not in ms)
chk("reference finalisation file present", "FINALIZED_CITE_ENGLISH_ORIGINAL" in refmd or "改引英文原文" in refmd)
chk("checklist reference gate green", "已定稿" in ch)
chk("checklist identity gate green", "无 ORCID" in ch and "麻醉科" in ch)
chk("cover letter states no ORCID", "no orcid" in cl.lower())
chk("manuscript states no ORCID and anesthesiology",
    "no orcid" in ms.lower() and "Department of Anesthesiology" in ms)

# --- 投稿就绪提示（不计入一致性 FAIL；gate 全绿不等于可投稿）---
print("\n=== SUBMISSION READINESS (not part of consistency gate) ===")
ready = []
def rdy(label, unresolved):
    print(("TODO " if unresolved else "OK   ") + label)
    if unresolved:
        ready.append(label)

rdy("Data availability placeholders [REPOSITORY URL]/[VERSION TAG]/[ZENODO DOI] all replaced",
    any(x in ms for x in ["[REPOSITORY URL]", "[VERSION TAG]", "[ZENODO DOI]"]))
rdy("AUTHOR NOTE removed from cover letter", "AUTHOR NOTE" in cl)
rdy("AUTHOR NOTE removed from manuscript", "AUTHOR NOTE" in ms)
rdy("CRediT mapping finalised (no 'confirm' instruction in declaration)",
    "confirm the credit mapping" in ms.lower())  # needle 必须小写，与 ms.lower() 同口径
rdy("cover letter no draft-state instruction", "will be inserted" in cl.lower() or "to be replaced" in cl.lower())
rdy("author independence statement present", "Neither author participated in the development" not in ms)
rdy("3 suggested reviewers confirmed by authors (still a draft in checklist)", "待作者确认" in ch)

print("\n" + ("CONSISTENCY GATE: ALL PASS" if not fails else f"CONSISTENCY GATE: {len(fails)} FAIL(s): {fails}"))
print(f"READINESS: {len(ready)} item(s) remain — gate PASS does NOT mean ready to submit")
sys.exit(1 if fails else 0)
