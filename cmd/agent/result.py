import pandas as pd
from datetime import datetime


# ====================================
# 文件路径
# ====================================
BASE_FILE = "漏洞文章知识库.xlsx"
RES_FILE = "res_deepseek.csv"


# ====================================
# 统一格式化
# ====================================
def norm(x):
    """
    统一规则:
    1. Excel空值 -> "null"
    2. bool -> true/false
    3. 1/0 -> true/false
    4. 去前后空格
    5. 忽略大小写
    6. 压缩多余空格
    """

    # Excel空单元格
    if pd.isna(x):
        return "null"

    # bool
    if x is True:
        return "true"

    if x is False:
        return "false"

    # 数字bool
    if x == 1 or x == 1.0:
        return "true"

    if x == 0 or x == 0.0:
        return "false"

    x = str(x)

    # 去空格
    x = x.strip()

    # 空字符串也视作NULL
    if x == "":
        return "null"

    # 忽略大小写
    x = x.lower()

    # 多空格压缩
    x = " ".join(x.split())

    return x


# ====================================
# danger专用比较
# ====================================
def compare_danger(pred, gt1, gt2):
    """
    pred 与 G列/I列任意匹配即正确
    """

    pred = norm(pred)
    gt1 = norm(gt1)
    gt2 = norm(gt2)

    return pred == gt1 or pred == gt2


# ====================================
# 读取基准xlsx
# ====================================
df_base = pd.read_excel(BASE_FILE)

base = {}

for _, row in df_base.iterrows():

    idx = str(row.iloc[0]).strip()

    base[idx] = {
        "cve": norm(row.iloc[2]),        # C
        "vendor": norm(row.iloc[3]),     # D
        "lang": norm(row.iloc[4]),       # E
        "analysis": norm(row.iloc[5]),   # F
        "danger": row.iloc[6],           # G
        "poc": norm(row.iloc[7]),        # H
        "final": row.iloc[8],            # I
    }

print("基准数据读取完成:", len(base))


# ====================================
# 读取实验结果
# ====================================
df_res = pd.read_csv(
    RES_FILE,
    header=None,
    encoding="utf-8"
)

lines = df_res.iloc[:, 0].tolist()

print("实验数据读取完成:", len(lines))


# ====================================
# 计数器
# ====================================
stats = {
    "cve": 0,
    "vendor": 0,
    "lang": 0,
    "analysis": 0,
    "danger": 0,
    "poc": 0
}

errors = []
total = 0


# ====================================
# 开始评分
# ====================================
for line in lines:

    parts = str(line).strip().split(";")

    if len(parts) != 7:
        print("格式错误:", line)
        continue

    idx = parts[0].strip()

    if idx not in base:
        print("编号不存在:", idx)
        continue

    gt = base[idx]
    total += 1

    pred = {
        "cve": norm(parts[1]),
        "vendor": norm(parts[2]),
        "lang": norm(parts[3]),
        "analysis": norm(parts[4]),
        "danger": parts[5],
        "poc": norm(parts[6]),
    }

    # -------------------------
    # 普通字段
    # -------------------------
    for k in ["cve", "vendor", "lang", "analysis", "poc"]:

        if pred[k] == gt[k]:
            stats[k] += 1
        else:
            errors.append([
                idx,
                k,
                pred[k],
                gt[k]
            ])

    # -------------------------
    # danger字段
    # -------------------------
    if compare_danger(
            pred["danger"],
            gt["danger"],
            gt["final"]
    ):
        stats["danger"] += 1
    else:
        errors.append([
            idx,
            "danger",
            norm(pred["danger"]),
            f"{norm(gt['danger'])} | {norm(gt['final'])}"
        ])


# ====================================
# 输出结果
# ====================================
print("\n=========评分结果=========\n")

correct = 0

for k, v in stats.items():

    acc = v / total * 100
    correct += v

    print(
        f"{k:10s}: "
        f"{v}/{total} = "
        f"{acc:.2f}%"
    )

overall = correct / (total * 6) * 100

print("\n----------------------------")
print(
    f"总体准确率: "
    f"{correct}/{total*6} "
    f"= {overall:.2f}%"
)


# ====================================
# 保存错误项
# ====================================
filename = (
    "debug_errors_"
    + datetime.now().strftime("%Y%m%d_%H%M%S")
    + ".xlsx"
)

pd.DataFrame(
    errors,
    columns=[
        "文章编号",
        "错误字段",
        "预测值",
        "真实值"
    ]
).to_excel(
    filename,
    index=False
)

print(f"\n错误项已保存到 {filename}")
print("错误总数:", len(errors))

print("\n前20条错误:")
print(
    pd.DataFrame(
        errors,
        columns=[
            "文章编号",
            "错误字段",
            "预测值",
            "真实值"
        ]
    ).head(20)
)