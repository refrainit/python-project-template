import os
import pandas as pd
import matplotlib.pyplot as plt
from github import Github
from datetime import datetime, timedelta, timezone

# tabulateが利用可能か確認
try:
    import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

# GitHubに接続
g = Github(os.environ["GITHUB_TOKEN"])
repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])

# 各種Issueを取得
issues = repo.get_issues(state="open")

# データフレームに変換するためのリスト
data = []

for issue in issues:
    # ラベル情報を取得
    labels = [label.name for label in issue.labels]
    
    # Issue種別（バグ、機能、タスク）を特定
    issue_type = "その他"
    if "bug" in labels:
        issue_type = "バグ"
    elif "enhancement" in labels:
        issue_type = "機能リクエスト"
    elif "task" in labels:
        issue_type = "タスク"
    
    # 優先度を特定（ボディからパースする必要あり）
    priority = "未設定"
    if issue.body and ("高" in issue.body or "緊急" in issue.body):
        priority = "高"
    elif issue.body and "中" in issue.body:
        priority = "中"
    elif issue.body and "低" in issue.body:
        priority = "低"
    
    # データリストに追加
    data.append({
        "番号": issue.number,
        "タイトル": issue.title,
        "種別": issue_type,
        "優先度": priority,
        "作成日": issue.created_at.replace(tzinfo=None),  # タイムゾーン情報を削除
        "更新日": issue.updated_at.replace(tzinfo=None),  # タイムゾーン情報を削除
        "担当者": issue.assignee.login if issue.assignee else "未割り当て",
    })

# データフレームに変換
df = pd.DataFrame(data)

# 種別ごとの集計
type_counts = df["種別"].value_counts() if not df.empty else pd.Series()

# 優先度ごとの集計
priority_counts = df["優先度"].value_counts() if not df.empty else pd.Series()

# 現在時刻（タイムゾーンなし）
now = datetime.now()

# DataFrameをマークダウン形式に変換するヘルパー関数
def df_to_markdown(dataframe):
    if HAS_TABULATE and not dataframe.empty:
        return dataframe.to_markdown()
    
    # tabulateがない場合は簡易的なマークダウンテーブルを作成
    if dataframe.empty:
        return "データなし"
    
    # インデックス名とカラム名
    result = []
    if isinstance(dataframe, pd.Series):
        result.append("| インデックス | 値 |")
        result.append("| --- | --- |")
        for idx, value in dataframe.items():
            result.append(f"| {idx} | {value} |")
    else:
        headers = "| " + " | ".join(str(col) for col in dataframe.columns) + " |"
        separator = "| " + " | ".join(["---"] * len(dataframe.columns)) + " |"
        result.append(headers)
        result.append(separator)
        
        for _, row in dataframe.iterrows():
            row_str = "| " + " | ".join(str(val) for val in row) + " |"
            result.append(row_str)
    
    return "\n".join(result)

# マークダウンレポートの作成
report = f"""# Issue集計レポート
生成日時: {now.strftime("%Y/%m/%d %H:%M")}

## 1. 全体概要
- 未解決Issue数: {len(df)}件
"""

# データフレームが空でない場合のみ平均未解決日数を計算
if not df.empty:
    avg_days = (now - df["作成日"].mean()).days
    report += f"- 平均未解決日数: {avg_days:.1f}日\n"
else:
    report += "- 平均未解決日数: データなし\n"

report += f"""
## 2. 種別ごとの集計
{df_to_markdown(type_counts)}

## 3. 優先度ごとの集計
{df_to_markdown(priority_counts)}
"""

# 直近のアクティビティ（1週間以内の更新）
if not df.empty:
    recent_updates = len(df[df["更新日"] > now - timedelta(days=7)])
    report += f"""
## 4. 直近のアクティビティ
直近1週間で更新されたIssue: {recent_updates}件
"""
else:
    report += """
## 4. 直近のアクティビティ
直近1週間で更新されたIssue: 0件
"""

# 最も長く未解決のIssue
if len(df) >= 5:
    oldest_issues = df.sort_values("作成日").head(5)
    report += f"""
## 5. 最も長く未解決のIssue（トップ5）
{df_to_markdown(oldest_issues[["番号", "タイトル", "種別", "優先度", "作成日"]])}
"""
elif not df.empty:
    oldest_issues = df.sort_values("作成日")
    report += f"""
## 5. 未解決のIssue
{df_to_markdown(oldest_issues[["番号", "タイトル", "種別", "優先度", "作成日"]])}
"""
else:
    report += """
## 5. 最も長く未解決のIssue
未解決のIssueはありません
"""

# レポートをファイルに保存
with open("issue-report.md", "w", encoding="utf-8") as f:
    f.write(report)

# グラフの生成（データがある場合のみ）
if not df.empty:
    plt.figure(figsize=(12, 5))

    # 種別ごとのIssue数
    if not type_counts.empty:
        plt.subplot(1, 2, 1)
        type_counts.plot.bar()
        plt.title("種別ごとのIssue数")
        plt.tight_layout()
    
    # 優先度ごとのIssue数
    if not priority_counts.empty:
        plt.subplot(1, 2, 2)
        priority_counts.plot.bar()
        plt.title("優先度ごとのIssue数")
        plt.tight_layout()
    
    plt.savefig("issue-stats.png")
    print("グラフを生成しました: issue-stats.png")
else:
    print("グラフを生成するデータがありません")

print("レポートを生成しました: issue-report.md")
