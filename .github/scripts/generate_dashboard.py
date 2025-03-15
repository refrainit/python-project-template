"""
Issue追跡ダッシュボード生成スクリプト
GitHubのIssue情報を集計し、HTMLダッシュボードを生成します。
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timedelta
from github import Github
from jinja2 import Template

# GitHubとの接続設定
g = Github(os.environ["GITHUB_TOKEN"])
repo = g.get_repo(os.environ["GITHUB_REPOSITORY"])

# ダッシュボード出力ディレクトリ
output_dir = Path("dashboard")
output_dir.mkdir(exist_ok=True)
img_dir = output_dir / "img"
img_dir.mkdir(exist_ok=True)

# Issueデータの取得と加工
def get_issues_data():
    """Issueデータを取得"""
    all_issues = list(repo.get_issues(state="all"))
    
    data = []
    for issue in all_issues:
        # PRはスキップ
        if issue.pull_request:
            continue
            
        # ラベル情報
        labels = [label.name for label in issue.labels]
        
        # Issue種別の特定
        issue_type = "その他"
        if "bug" in labels:
            issue_type = "バグ"
        elif "enhancement" in labels:
            issue_type = "機能リクエスト"
        elif "task" in labels:
            issue_type = "タスク"
            
        # 優先度の特定
        priority = "未設定"
        if any(l in ["高", "緊急", "high", "critical"] for l in labels):
            priority = "高"
        elif any(l in ["中", "medium"] for l in labels):
            priority = "中"
        elif any(l in ["低", "low"] for l in labels):
            priority = "低"
        
        data.append({
            "番号": issue.number,
            "タイトル": issue.title,
            "種別": issue_type,
            "優先度": priority,
            "状態": "オープン" if issue.state == "open" else "クローズ",
            "作成日": issue.created_at,
            "更新日": issue.updated_at,
            "クローズ日": issue.closed_at,
            "担当者": issue.assignee.login if issue.assignee else "未割り当て",
            "URL": issue.html_url,
        })
    
    return pd.DataFrame(data)

# データの集計と可視化
def generate_charts(df):
    """グラフを生成"""
    plt.figure(figsize=(10, 6))
    
    # 種別ごとの集計
    plt.subplot(2, 2, 1)
    type_counts = df["種別"].value_counts()
    type_counts.plot.bar()
    plt.title("種別ごとのIssue数")
    plt.tight_layout()
    
    # 優先度ごとの集計
    plt.subplot(2, 2, 2)
    priority_counts = df["優先度"].value_counts()
    priority_counts.plot.bar()
    plt.title("優先度ごとのIssue数")
    plt.tight_layout()
    
    # 状態ごとの集計
    plt.subplot(2, 2, 3)
    state_counts = df["状態"].value_counts()
    state_counts.plot.pie(autopct='%1.1f%%', startangle=140)
    plt.title("Issue状態の分布")
    plt.tight_layout()
    
    # 最近のアクティビティ（週ごとの作成数）
    plt.subplot(2, 2, 4)
    df['週'] = pd.to_datetime(df['作成日']).dt.isocalendar().week
    weekly = df.groupby('週').size()
    weekly.plot.line()
    plt.title("週ごとのIssue作成数")
    plt.tight_layout()
    
    # 保存
    plt.savefig(img_dir / "issue_charts.png")
    
    # 最近のアクティビティ（月ごと）
    plt.figure(figsize=(12, 5))
    df['月'] = pd.to_datetime(df['作成日']).dt.strftime('%Y-%m')
    monthly = df.groupby('月').size()
    monthly.plot.bar()
    plt.title("月ごとのIssue作成数")
    plt.tight_layout()
    plt.savefig(img_dir / "monthly_issues.png")

# HTMLダッシュボード生成
def generate_dashboard(df):
    """HTMLダッシュボードを生成"""
    # データの集計
    total_issues = len(df)
    open_issues = len(df[df["状態"] == "オープン"])
    closed_issues = len(df[df["状態"] == "クローズ"])
    
    by_type = df["種別"].value_counts().to_dict()
    by_priority = df["優先度"].value_counts().to_dict()
    
    # 最近の未解決Issue（上位5件）
    recent_issues = df[df["状態"] == "オープン"].sort_values(by="作成日", ascending=False).head(5)
    recent_issues_list = recent_issues[["番号", "タイトル", "種別", "優先度", "URL"]].to_dict(orient="records")
    
    # 最も長く未解決のIssue（上位5件）
    oldest_issues = df[df["状態"] == "オープン"].sort_values(by="作成日").head(5)
    oldest_issues_list = oldest_issues[["番号", "タイトル", "作成日", "種別", "優先度", "URL"]].to_dict(orient="records")
    
    # HTMLテンプレート
    template_html = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>プロジェクト Issue ダッシュボード</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            .card { margin-bottom: 20px; }
            .stat-card { text-align: center; padding: 15px; }
            .stat-number { font-size: 2.5rem; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="container mt-4">
            <h1>プロジェクト Issue ダッシュボード</h1>
            <p>最終更新: {{ update_time }}</p>
            
            <div class="row mt-4">
                <div class="col-md-4">
                    <div class="card stat-card">
                        <div class="stat-number text-primary">{{ total_issues }}</div>
                        <div>総Issue数</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card stat-card">
                        <div class="stat-number text-success">{{ open_issues }}</div>
                        <div>未解決Issue</div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card stat-card">
                        <div class="stat-number text-secondary">{{ closed_issues }}</div>
                        <div>解決済Issue</div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            種別ごとのIssue数
                        </div>
                        <div class="card-body">
                            <ul class="list-group">
                                {% for type, count in by_type.items() %}
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    {{ type }}
                                    <span class="badge bg-primary rounded-pill">{{ count }}</span>
                                </li>
                                {% endfor %}
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            優先度ごとのIssue数
                        </div>
                        <div class="card-body">
                            <ul class="list-group">
                                {% for priority, count in by_priority.items() %}
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    {{ priority }}
                                    <span class="badge bg-primary rounded-pill">{{ count }}</span>
                                </li>
                                {% endfor %}
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            Issue統計
                        </div>
                        <div class="card-body">
                            <img src="img/issue_charts.png" class="img-fluid" alt="Issue統計">
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            月ごとのIssue作成数
                        </div>
                        <div class="card-body">
                            <img src="img/monthly_issues.png" class="img-fluid" alt="月間Issue統計">
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            最近作成されたIssue
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>タイトル</th>
                                            <th>種別</th>
                                            <th>優先度</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for issue in recent_issues %}
                                        <tr>
                                            <td>{{ issue.番号 }}</td>
                                            <td><a href="{{ issue.URL }}" target="_blank">{{ issue.タイトル }}</a></td>
                                            <td>{{ issue.種別 }}</td>
                                            <td>{{ issue.優先度 }}</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            最も古い未解決Issue
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>タイトル</th>
                                            <th>作成日</th>
                                            <th>優先度</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for issue in oldest_issues %}
                                        <tr>
                                            <td>{{ issue.番号 }}</td>
                                            <td><a href="{{ issue.URL }}" target="_blank">{{ issue.タイトル }}</a></td>
                                            <td>{{ issue.作成日.strftime('%Y-%m-%d') }}</td>
                                            <td>{{ issue.優先度 }}</td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="bg-light text-center py-3 mt-5">
            <p>自動生成されたダッシュボード - <a href="https://github.com/{{ repo_name }}" target="_blank">{{ repo_name }}</a></p>
        </footer>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    # テンプレート適用
    template = Template(template_html)
    html = template.render(
        update_time=datetime.now().strftime("%Y年%m月%d日 %H:%M"),
        total_issues=total_issues,
        open_issues=open_issues,
        closed_issues=closed_issues,
        by_type=by_type,
        by_priority=by_priority,
        recent_issues=recent_issues_list,
        oldest_issues=oldest_issues_list,
        repo_name=os.environ["GITHUB_REPOSITORY"]
    )
    
    # HTML保存
    with open(output_dir / "index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    # データをJSONとしても保存
    summary = {
        "total_issues": total_issues,
        "open_issues": open_issues,
        "closed_issues": closed_issues,
        "by_type": by_type,
        "by_priority": by_priority,
        "update_time": datetime.now().isoformat()
    }
    
    with open(output_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    print("Issueデータを取得中...")
    df = get_issues_data()
    
    print(f"合計 {len(df)} 件のIssueを処理しています")
    
    print("グラフを生成中...")
    generate_charts(df)
    
    print("ダッシュボードを生成中...")
    generate_dashboard(df)
    
    print("完了！ダッシュボードは dashboard/index.html に生成されました")
