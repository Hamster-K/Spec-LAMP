import pandas as pd
import numpy as np
from scipy.stats import ttest_ind, ks_2samp

# =========================
# 参数
# =========================
excel_path = ""

feature_cols = []
label_col = 15

alpha = 0.05
lambda_weight = 0.5
MIN_P = 1e-300

# =========================
# 数据加载
# =========================
df = pd.read_excel(excel_path)

X = df.iloc[:, feature_cols]
y = df.iloc[:, label_col]

X_attack = X[y == 1]
X_benign = X[y == 0]

# =========================
# Step 1
# =========================
records = []

for feature in X.columns:
    attack_vals = X_attack[feature].dropna()
    benign_vals = X_benign[feature].dropna()

    t_stat, p_t = ttest_ind(
        attack_vals,
        benign_vals,
        equal_var=False
    )

    ks_stat, p_ks = ks_2samp(
        attack_vals,
        benign_vals
    )

    p_t = max(p_t, MIN_P)
    p_ks = max(p_ks, MIN_P)

    records.append({
        "Event": feature,
        "t_stat": t_stat,
        "p_t": p_t,
        "ks_stat": ks_stat,
        "p_ks": p_ks,
        "mean_attack": attack_vals.mean(),
        "mean_benign": benign_vals.mean()
    })

df_all = pd.DataFrame(records)

# =========================
# Step 2
# =========================
df_all["significant"] = (
    (df_all["p_t"] < alpha) &
    (df_all["p_ks"] < alpha)
)

# =========================
# Step 3
# =========================
df_all["abs_t"] = df_all["t_stat"].abs()

df_sig = df_all[df_all["significant"]].copy()

def min_max_norm(x):
    return (x - x.min()) / (x.max() - x.min() + 1e-12)

df_all["t_norm"] = np.nan
df_all["ks_norm"] = np.nan

df_all.loc[df_sig.index, "t_norm"] = min_max_norm(df_sig["abs_t"])
df_all.loc[df_sig.index, "ks_norm"] = min_max_norm(df_sig["ks_stat"])

# =========================
# Step 4
# =========================
df_all["score"] = np.nan

df_all.loc[df_sig.index, "score"] = (
    lambda_weight * df_all.loc[df_sig.index, "t_norm"] +
    (1 - lambda_weight) * df_all.loc[df_sig.index, "ks_norm"]
)

# =========================
# Step 5
# =========================
df_all["Rank"] = np.nan

df_ranked_sig = df_all[df_all["significant"]] \
    .sort_values("score", ascending=False)

df_all.loc[df_ranked_sig.index, "Rank"] = range(1, len(df_ranked_sig) + 1)

# =========================
# output
# =========================
df_all_sorted = df_all.sort_values(
    by=["significant", "Rank"],
    ascending=[False, True]
)

df_all_sorted.to_excel("hpc_event_ranking_full.xlsx", index=False)

print(df_all_sorted[[
    "Rank",
    "Event",
    "significant",
    "score",
    "t_stat",
    "ks_stat",
    "p_t",
    "p_ks"
]])
