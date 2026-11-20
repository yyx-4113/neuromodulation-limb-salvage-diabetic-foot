"""Inter-rater reliability for AGREE II once the second appraiser's scores return.

INPUTS
- agree2_scoring_2026-11-18.csv                 (appraiser 1, column score_1_7)
- agree2_appraiser2_returned_2026-11-19.csv (appraiser 2 actual scores, column appraiser2_score_1_7;
  falls back to the blank blind template until return, which triggers PENDING)

METRICS (item-level, 23 scores):
- percent exact agreement
- Cohen's kappa (unweighted) and linear-weighted kappa
- ICC(2,1) two-way random, absolute agreement, single measure (Shrout-Fleiss)
- per-domain: both appraisers' standardized scores, absolute gap

NO FABRICATION: if appraiser-2 scores are blank/incomplete, the script REFUSES to
compute and exits with a PENDING message. It never imputes, copies, or synthesizes
the second rater's scores.

Domain score = (obtained - n_items) / (7*n_items - n_items) * 100  (official AGREE II).

Run: py -3.14 compute_agree2_interrater_2026-11-19.py
"""
import csv, json, os, sys
try:
    import numpy as np
except ImportError:
    np = None
HERE = os.path.dirname(os.path.abspath(__file__))

# --- SELFTEST: formula sanity check with SYNTHETIC data (never written to any deliverable) ---
if "--selftest" in sys.argv:
    def _kappa(a,b,weight):
        n=len(a); k=7; O=[[0]*k for _ in range(k)]
        for x,y in zip(a,b): O[x-1][y-1]+=1
        row=[sum(r) for r in O]; col=[sum(O[i][j] for i in range(k)) for j in range(k)]
        po=sum(weight(i,j)*O[i][j] for i in range(k) for j in range(k))/n
        pe=sum(weight(i,j)*row[i]*col[j] for i in range(k) for j in range(k))/(n*n)
        return (po-pe)/(1-pe)
    def _icc(a,b):
        n=len(a); gm=sum(a+b)/(2*n); rm=[(a[i]+b[i])/2 for i in range(n)]
        cm=[sum(a)/n,sum(b)/n]
        MSR=2*sum((m-gm)**2 for m in rm)/(n-1); MSC=n*sum((m-gm)**2 for m in cm)
        SSE=sum((a[i]-rm[i]-cm[0]+gm)**2+(b[i]-rm[i]-cm[1]+gm)**2 for i in range(n))
        MSE=SSE/(n-1)
        return (MSR-MSE)/(MSR+MSE+2*(MSC-MSE)/n)
    ident=[3,4,5]*7+[4,5]  # 23 synthetic identical scores
    shifted=[min(7,x+1) for x in ident]
    assert abs(_kappa(ident,ident,lambda i,j:1.0 if i==j else 0.0)-1.0)<1e-9
    assert abs(_kappa(ident,ident,lambda i,j:1.0-abs(i-j)/6)-1.0)<1e-9
    assert abs(_icc(ident,ident)-1.0)<1e-9
    kk=_kappa(ident,shifted,lambda i,j:1.0 if i==j else 0.0)
    kw=_kappa(ident,shifted,lambda i,j:1.0-abs(i-j)/6)
    assert -1<=kk<1 and -1<=kw<1, (kk,kw)
    print("SELFTEST PASS: identical->kappa=1.0/ICC=1.0; shifted->kappa=%.3f wkappa=%.3f (synthetic, not saved)"%(kk,kw))
    sys.exit(0)

p1 = os.path.join(HERE, "agree2_scoring_2026-11-18.csv")
# Second-appraiser scores: prefer the RETURNED file (actual data).
# Fall back to the blind template, which is blank until return -> triggers PENDING.
_ret = os.path.join(HERE, "agree2_appraiser2_returned_2026-11-19.csv")
_tpl = os.path.join(HERE, "agree2_appraiser2_blind_template_2026-11-19.csv")
p2 = _ret if os.path.exists(_ret) else _tpl

r1 = list(csv.DictReader(open(p1, encoding="utf-8-sig")))
r2 = list(csv.DictReader(open(p2, encoding="utf-8-sig")))
assert len(r1) == 23 and len(r2) == 23
assert [int(x["item"]) for x in r1] == list(range(1,24))
assert [int(x["item"]) for x in r2] == list(range(1,24))

missing = [x["item"] for x in r2 if not str(x["appraiser2_score_1_7"]).strip()]
if missing:
    print(f"PENDING: second appraiser scores not yet returned. Blank items: {missing}")
    print("No metrics computed. No scores imputed or copied.")
    sys.exit(0)

a = [int(x["score_1_7"]) for x in r1]          # appraiser 1
b = [int(x["appraiser2_score_1_7"]) for x in r2]  # appraiser 2
assert all(1 <= v <= 7 for v in a + b), "scores must be integers 1-7"
n = len(a)

# --- percent exact agreement ---
exact = sum(1 for x,y in zip(a,b) if x==y)/n*100

# --- Cohen's kappa (unweighted) + linear-weighted kappa ---
cats = list(range(1,8)); k = len(cats)
def kappa(weight):
    O = [[0]*k for _ in range(k)]
    for x,y in zip(a,b): O[x-1][y-1]+=1
    row=[sum(r) for r in O]; col=[sum(O[i][j] for i in range(k)) for j in range(k)]
    po=sum(weight(i,j)*O[i][j] for i in range(k) for j in range(k))/n
    pe=sum(weight(i,j)*row[i]*col[j] for i in range(k) for j in range(k))/(n*n)
    return (po-pe)/(1-pe) if abs(1-pe)>1e-12 else float("nan")
kw  = kappa(lambda i,j: 1.0 if i==j else 0.0)
kwl = kappa(lambda i,j: 1.0 - abs(i-j)/(k-1))

# --- ICC(2,1) two-way random, absolute agreement, single measure ---
gm=sum(a+b)/(2*n)
rowmean=[(a[i]+b[i])/2 for i in range(n)]
cmean=[sum(a)/n, sum(b)/n]
MSR=2*sum((m-gm)**2 for m in rowmean)/(n-1)
MSC=n*sum((m-gm)**2 for m in cmean)/(2-1)
SSE=sum((a[i]-rowmean[i]-cmean[0]+gm)**2 + (b[i]-rowmean[i]-cmean[1]+gm)**2 for i in range(n))
MSE=SSE/((n-1)*(2-1))
icc21=(MSR-MSE)/(MSR+(2-1)*MSE+2*(MSC-MSE)/n)

# --- ICC(2,1) 95% CI via nonparametric bootstrap over the 23 targets ---
# Uses the SAME two-way formula above (not the one-way F-ratio approximation).
icc_ci = None
icc_ci_method = None
if np is not None:
    def _icc_pair(x, y):
        nn = len(x); kk = 2
        g = (sum(x) + sum(y)) / (2 * nn)
        rm = [(x[i] + y[i]) / 2 for i in range(nn)]
        cm = [sum(x) / nn, sum(y) / nn]
        msr = kk * sum((m - g) ** 2 for m in rm) / (nn - 1)
        msc = nn * sum((m - g) ** 2 for m in cm) / (kk - 1)
        sse = sum((x[i]-rm[i]-cm[0]+g)**2 + (y[i]-rm[i]-cm[1]+g)**2 for i in range(nn))
        mse = sse / ((nn - 1) * (kk - 1))
        return (msr - mse) / (msr + (kk - 1) * mse + kk * (msc - mse) / nn)
    rng = np.random.default_rng(20261119)
    boots = []
    for _ in range(5000):
        idx = rng.integers(0, n, n)
        v = _icc_pair([a[i] for i in idx], [b[i] for i in idx])
        if v == v and abs(v) != float("inf"):  # finite
            boots.append(v)
    if boots:
        lo, hi = np.percentile(boots, [2.5, 97.5])
        icc_ci = [round(float(lo), 3), round(float(hi), 3)]
        icc_ci_method = "nonparametric bootstrap, 5000 resamples, seed=20261119, two-way formula"

# --- per-domain standardized scores (both raters) + gaps ---
doms={}
for i in range(n):
    d=r1[i]["domain"]
    doms.setdefault(d,{"n":0,"s1":0,"s2":0})
    doms[d]["n"]+=1; doms[d]["s1"]+=a[i]; doms[d]["s2"]+=b[i]
dom_out={}
for d,v in doms.items():
    ni=v["n"]; base=(7*ni-ni)
    p1s=round((v["s1"]-ni)/base*100,1); p2s=round((v["s2"]-ni)/base*100,1)
    dom_out[d]={"items":ni,"appraiser1_pct":p1s,"appraiser2_pct":p2s,
                "absolute_gap_pct":round(abs(p1s-p2s),1)}

disagreement=[{"item":r1[i]["item"],"appraiser1":a[i],"appraiser2":b[i],
               "abs_diff":abs(a[i]-b[i])} for i in range(n) if abs(a[i]-b[i])>=2]

out={"status":"COMPUTED","date":"2026-11-19","n_items":n,
     "percent_exact_agreement_pct":round(exact,1),
     "cohen_kappa_unweighted":round(kw,3),"cohen_kappa_linear_weighted":round(kwl,3),
     "ICC_2_1_absolute_agreement":round(icc21,3),
     "ICC_2_1_95CI":icc_ci,"ICC_2_1_CI_method":icc_ci_method,
     "domains":dom_out,"disagreement_abs_ge_2":disagreement,
     "note":"AGREE II manual recommends >=2 appraisers; kappa/ICC with n=23 items are item-level reliability, not a substitute for 4-appraiser scoring."}

jf=os.path.join(HERE,"agree2_interrater_reliability_2026-11-19.json")
json.dump(out,open(jf,"w",encoding="utf-8"),ensure_ascii=False,indent=2)

md=["# AGREE II 双评价者一致性（2026-11-19）","",
    f"- 条目数：{n}",
    f"- 完全一致率：{exact:.1f}%",
    f"- Cohen's κ（未加权）：{kw:.3f}",
    f"- Cohen's κ（线性加权）：{kwl:.3f}",
    f"- ICC(2,1) 双向随机/绝对一致/单测量：{icc21:.3f}"
    + (f" （95% CI {icc_ci[0]:.3f}–{icc_ci[1]:.3f}，bootstrap 5000 次）" if icc_ci else ""),
    "","## 各域标准化分","","| 域 | 条目数 | 评价者1 | 评价者2 | 差值 |","|---|---|---|---|---|"]
for d,v in dom_out.items():
    md.append(f"| {d} | {v['items']} | {v['appraiser1_pct']}% | {v['appraiser2_pct']}% | {v['absolute_gap_pct']}pp |")
md+=["","## 分歧条目（|差值|≥2）",""]
if disagreement:
    md.append("| 条目 | 评价者1 | 评价者2 | 差值 |"); md.append("|---|---|---|---|")
    for x in disagreement:
        md.append(f"| {x['item']} | {x['appraiser1']} | {x['appraiser2']} | {x['abs_diff']} |")
else:
    md.append("(无)")
md+=["","纪律：分歧条目保留原分，不回头对齐；不预设结论。",""]
mf=os.path.join(HERE,"agree2_interrater_reliability_2026-11-19.md")
open(mf,"w",encoding="utf-8").write("\n".join(md))

# gate: derived, not hardcoded expected values
assert 0 <= exact <= 100
assert -1 <= kw <= 1 and -1 <= kwl <= 1 and -1 <= icc21 <= 1
assert len(dom_out)==6 and len(disagreement)+sum(1 for x,y in zip(a,b) if abs(x-y)<2)==n
print("COMPUTED. exact=",round(exact,1),"kappa=",round(kw,3),"kwl=",round(kwl,3),"ICC21=",round(icc21,3))
print("disagreements(|diff|>=2)=",len(disagreement))
print("wrote",jf,"and",mf)
