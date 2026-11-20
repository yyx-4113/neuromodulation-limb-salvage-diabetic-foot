"""编号转换：正文中的"共识引用编号"改为稿件的 Vancouver 连续编号。
生成 v1.0_submit.md（供 docx 导出），审计源文件 v1.0_clean.md 不动。
带严格断言；数字/结论零改动。
"""
import re, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "manuscript", "methodological-appraisal-chinese-expert-consensus_v1.0_clean.md")
DST = os.path.join(ROOT, "manuscript", "methodological-appraisal-chinese-expert-consensus_v1.0_submit.md")

s = open(SRC, encoding="utf-8").read()

# 共识编号 -> 论文编号（仅这些出现在正文且已著录于13条参考表）
MAP = {"3": "6", "4": "7", "25": "8", "26": "9", "27": "10",
       "42": "11", "43": "12", "47": "13"}

def repl_once(old, new, label):
    global s
    n = s.count(old)
    assert n == 1, f"{label}: expected 1, found {n}"
    s = s.replace(old, new)

# 1) 先处理 [37–41] 与 [46]（不在13条表内）为描述性表述，避免悬空引用
repl_once(
    "[37–41] contained no DF wound-healing SCS trial",
    "the citations attached to recommendation 3 contained no DF wound-healing SCS trial",
    "37-41 descriptive")
repl_once(
    "and [46] and [47] reported PDN pain and health-related quality-of-life outcomes without a limb-salvage endpoint.",
    "and two further cited reports addressed PDN pain and health-related quality-of-life outcomes, including the 24-month follow-up [47], without a limb-salvage endpoint.",
    "46/47 descriptive")

# 2) 保护 References 区里的 [Consensus reference [N]] 审计说明（替换成哨兵）
protected = []
def protect(m):
    protected.append(m.group(0))
    return f"\x00PROT{len(protected)-1}\x00"
s = re.sub(r"\[Consensus reference \[(?:3|4|25|26|27|42|43|47)\][^\]]*\]", protect, s)
assert len(protected) == 8, f"expected 8 protected consensus-reference notes, got {len(protected)}"

# 3) 正文裸共识编号替换（纯数字方括号；[1.00, 1.00] 等不匹配）
def conv(m):
    num = m.group(1)
    return f"[{MAP[num]}]" if num in MAP else m.group(0)

# 只替换正文区（Abstract 之后到 Tables 之前），跳过 References 与 protected 哨兵
i = s.find("## 1 Introduction")
j = s.find("## Tables (main, for insertion)")
assert i != -1 and j != -1 and i < j
head, body, tail = s[:i], s[i:j], s[j:]
body_new = re.sub(r"\[(\d+)\]", conv, body)
s = head + body_new + tail

# Table 4 caption 中的 [3]（在 Tables 区，非 References）也需转换
s = s.replace("their common cited source [3], and full-text verification result",
              "their common cited source [6], and full-text verification result")
assert "cited source [6]" in s

# 4) 还原受保护的审计说明
for k, val in enumerate(protected):
    s = s.replace(f"\x00PROT{k}\x00", val)
assert "\x00PROT" not in s

# 5) 断言：正文不再有裸共识编号（除 bootstrap [1.00,1.00] 与论文编号）
body2 = s[s.find("## 1 Introduction"):s.find("## Tables (main, for insertion)")]
for old in ["[3]", "[4]", "[25]", "[26]", "[27]", "[42]", "[43]", "[47]", "[37–41]", "[46]"]:
    assert old not in body2, f"residual consensus label in body: {old}"
# 论文编号应已出现
for new in ["[6]", "[7]", "[8]", "[9]", "[10]", "[11]", "[12]", "[13]"]:
    assert new in body2, f"missing converted journal number: {new}"
# 审计说明保留
assert "[Consensus reference [3]; full text verified.]" in s
# 数字不变
for tok in ["39.1%", "0.258", "0.651", "0.853", "0.663", "0.941", "44.4%", "73.6", "94.74%", "0.17"]:
    assert tok in s, f"number lost: {tok}"

open(DST, "w", encoding="utf-8").write(s)
print(f"WROTE: {DST}  chars={len(s)}")
print(f"converted {len(protected)} protected reference notes unchanged")
