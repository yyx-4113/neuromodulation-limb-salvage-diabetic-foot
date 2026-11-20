"""生成清洁投稿版稿件：从 v0.3 删除所有内部批注块，保留正文/表格/参考文献。
摘要整块替换为投稿版四段（来自 abstract_for_submission_v0.2.md）。
数字零改动；每处删除前断言唯一命中。
"""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "manuscript", "methodological-appraisal-chinese-expert-consensus_v0.3.md")
DST = os.path.join(ROOT, "manuscript", "methodological-appraisal-chinese-expert-consensus_v1.0_clean.md")
ABS = os.path.join(ROOT, "submission", "bmc-hsr", "abstract_for_submission_v0.2.md")

s = open(SRC, encoding="utf-8").read()

def repl(old, new, label, count=1):
    global s
    n = s.count(old)
    assert n == count, f"{label}: expected {count}, found {n}"
    s = s.replace(old, new)

# 1) Version 元信息行 -> 简洁署名版本行
repl(
    "**Version**: v0.3 — 2026-11-20 (round-1 expert-panel revision of v0.2; see `audit/consensus_2026/expert_panel_review_v0.2_2026-11-20.md`). Title first-five-content-words filename prefix: `methodological-appraisal-chinese-expert-consensus`.",
    "**Version**: v1.0 — clean submission copy (2026-11-20).", "version line")

# 2) 整个 AUTHOR NOTE 引用块
i = s.find("> **AUTHOR NOTE — REMOVE BEFORE SUBMISSION")
assert i != -1, "AUTHOR NOTE start not found"
j = s.find("\n---\n", i)
assert j != -1, "AUTHOR NOTE terminator not found"
s = s[:i] + s[j + 1:]  # 保留 --- 分隔线

# 3) Authors' contributions 末尾内部指令括号
repl(" (Authors: confirm the CRediT mapping in the submission system; the second author is in the Department of Anesthesiology and has no ORCID, left blank as confirmed.)", "", "CRediT note")

# 4) 文末 Reference note + Pre-submission checks 两个引用块
i = s.find("> **Reference note**:")
assert i != -1, "Reference note not found"
j = s.find("none has been performed.", i)
assert j != -1, "Pre-submission end not found"
j += len("none has been performed.")
s = s[:i] + s[j:]

# 5) 摘要整块替换：从投稿版摘要文件抽取四段（Background/Methods/Results/Conclusions）+ Keywords
ab = open(ABS, encoding="utf-8").read()
def grab(label, next_label=None):
    a = ab.find(f"**{label}**:")
    assert a != -1, f"abstract {label} not found"
    if next_label:
        b = ab.find(f"**{next_label}**:", a)
        assert b != -1
        return ab[a:b].rstrip()
    return ab[a:].rstrip()

bg = grab("Background", "Methods")
me = grab("Methods", "Results")
re_ = grab("Results", "Conclusions")
co = grab("Conclusions", "Keywords")
kw = grab("Keywords")
new_abstract = "\n\n".join([bg, me, re_, co, kw])

a = s.find("## Abstract")
assert a != -1
b = s.find("## 1 Introduction", a)
assert b != -1
body_before = s[:a]
head = "## Abstract\n\n"
s = body_before + head + new_abstract + "\n\n---\n\n" + s[b:]

# 6) Data availability 去粗体占位符（保留占位，待用户回填真实值）
repl(
    "at `[REPOSITORY URL]` under release `[VERSION TAG]` (archived at `[ZENODO DOI]`).",
    "at [REPOSITORY URL] under release [VERSION TAG] (archived at [ZENODO DOI]).",
    "data availability placeholder")

while "\n\n\n" in s:
    s = s.replace("\n\n\n", "\n\n")
s = s.rstrip() + "\n"
open(DST, "w", encoding="utf-8").write(s)
print(f"WROTE: {DST}  chars={len(s)}")
