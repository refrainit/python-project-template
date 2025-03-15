/**
 * Issue追跡ダッシュボード生成スクリプト
 * GitHubのIssue情報を集計し、HTMLダッシュボードを生成します。
 */
// ESMモジュールをダイナミックインポートするための関数
async function importESM() {
    const { Octokit } = await import('@octokit/rest');
    const fs = await import('fs/promises');
    const path = await import('path');
    const { createCanvas } = await import('canvas');
    const { Chart } = await import('chart.js/auto');
    
    return { Octokit, fs, path, createCanvas, Chart };
  }
  
  /**
   * メイン実行関数
   */
  async function main() {
    try {
      // ESMモジュールをインポート
      const { Octokit, fs, path, createCanvas, Chart } = await importESM();
      
      // GitHubとの接続設定
      const octokit = new Octokit({
        auth: process.env.GITHUB_TOKEN
      });
  
      // リポジトリ情報
      const [owner, repo] = process.env.GITHUB_REPOSITORY.split('/');
  
      console.log(`リポジトリ: ${owner}/${repo}`);
  
      // ディレクトリの準備
      const outputDir = 'dashboard';
      const imgDir = `${outputDir}/img`;
  
      try {
        await fs.mkdir(outputDir, { recursive: true });
        await fs.mkdir(imgDir, { recursive: true });
      } catch (err) {
        console.error('ディレクトリの作成エラー:', err);
      }
  
      console.log('Issueデータを取得中...');
      
      // すべてのIssueを取得（オープンとクローズ）
      const issues = [];
      let page = 1;
      let hasMore = true;
      
      while (hasMore) {
        const response = await octokit.issues.listForRepo({
          owner,
          repo,
          state: 'all',
          per_page: 100,
          page: page
        });
        
        if (response.data.length === 0) {
          hasMore = false;
        } else {
          // PRを除外
          const filteredIssues = response.data.filter(issue => !issue.pull_request);
          issues.push(...filteredIssues);
          page++;
        }
      }
      
      console.log(`${issues.length} 件のIssueを取得しました`);
      
      // データ加工
      const processedIssues = issues.map(issue => {
        const labels = issue.labels.map(label => label.name);
        
        // Issue種別の特定
        let issueType = 'その他';
        if (labels.includes('bug')) {
          issueType = 'バグ';
        } else if (labels.includes('enhancement')) {
          issueType = '機能リクエスト';
        } else if (labels.includes('task')) {
          issueType = 'タスク';
        }
        
        // 優先度の特定
        let priority = '未設定';
        if (labels.some(l => ['高', '緊急', 'high', 'critical'].includes(l))) {
          priority = '高';
        } else if (labels.some(l => ['中', 'medium'].includes(l))) {
          priority = '中';
        } else if (labels.some(l => ['低', 'low'].includes(l))) {
          priority = '低';
        }
        
        return {
          number: issue.number,
          title: issue.title,
          type: issueType,
          priority: priority,
          state: issue.state === 'open' ? 'オープン' : 'クローズ',
          createdAt: new Date(issue.created_at),
          updatedAt: new Date(issue.updated_at),
          closedAt: issue.closed_at ? new Date(issue.closed_at) : null,
          assignee: issue.assignee ? issue.assignee.login : '未割り当て',
          url: issue.html_url
        };
      });
  
      console.log('グラフを生成中...');
      
      // 種別ごとの集計
      const typeCount = {};
      processedIssues.forEach(issue => {
        typeCount[issue.type] = (typeCount[issue.type] || 0) + 1;
      });
      
      // 優先度ごとの集計
      const priorityCount = {};
      processedIssues.forEach(issue => {
        priorityCount[issue.priority] = (priorityCount[issue.priority] || 0) + 1;
      });
      
      // 状態ごとの集計
      const stateCount = {};
      processedIssues.forEach(issue => {
        stateCount[issue.state] = (stateCount[issue.state] || 0) + 1;
      });
      
      // 月ごとの集計
      const monthlyCount = {};
      processedIssues.forEach(issue => {
        const month = `${issue.createdAt.getFullYear()}-${(issue.createdAt.getMonth() + 1).toString().padStart(2, '0')}`;
        monthlyCount[month] = (monthlyCount[month] || 0) + 1;
      });
      
      // グラフ用の日本語→英語変換マッピング
      const typeMapping = {
        'バグ': 'Bug',
        '機能リクエスト': 'Feature Request',
        'タスク': 'Task',
        'その他': 'Other'
      };
      
      const priorityMapping = {
        '高': 'High',
        '中': 'Medium',
        '低': 'Low',
        '未設定': 'Not Set'
      };
      
      const stateMapping = {
        'オープン': 'Open',
        'クローズ': 'Closed'
      };
      
      // Issue統計グラフ
      const width = 800;
      const height = 600;
      const canvas = createCanvas(width, height);
      const context = canvas.getContext('2d');
      
      // グラフ生成 - 英語ラベル使用
      new Chart(context, {
        type: 'bar',
        data: {
          labels: Object.keys(typeCount).map(type => typeMapping[type] || type),
          datasets: [{
            label: 'Issues by Type',
            data: Object.values(typeCount),
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 1
          }]
        },
        options: {
          plugins: {
            title: {
              display: true,
              text: 'Issues by Type'
            }
          }
        }
      });
      
      // グラフ保存
      const buffer = canvas.toBuffer('image/png');
      await fs.writeFile(`${imgDir}/issue_stats.png`, buffer);
      
      // 状態グラフ（円グラフ） - 英語ラベル使用
      const stateCanvas = createCanvas(400, 400);
      const stateContext = stateCanvas.getContext('2d');
      
      new Chart(stateContext, {
        type: 'pie',
        data: {
          labels: Object.keys(stateCount).map(state => stateMapping[state] || state),
          datasets: [{
            data: Object.values(stateCount),
            backgroundColor: [
              'rgba(54, 162, 235, 0.5)',
              'rgba(255, 99, 132, 0.5)'
            ],
            borderColor: [
              'rgba(54, 162, 235, 1)',
              'rgba(255, 99, 132, 1)'
            ],
            borderWidth: 1
          }]
        },
        options: {
          plugins: {
            title: {
              display: true,
              text: 'Issue Status Distribution'
            }
          }
        }
      });
      
      // 円グラフ保存
      const stateBuffer = stateCanvas.toBuffer('image/png');
      await fs.writeFile(`${imgDir}/issue_state.png`, stateBuffer);
      
      // 月別グラフ
      const monthlyCanvas = createCanvas(800, 400);
      const monthlyContext = monthlyCanvas.getContext('2d');
      
      const sortedMonths = Object.keys(monthlyCount).sort();
      
      new Chart(monthlyContext, {
        type: 'bar',
        data: {
          labels: sortedMonths,
          datasets: [{
            label: 'Monthly Issue Creation',
            data: sortedMonths.map(month => monthlyCount[month]),
            backgroundColor: 'rgba(75, 192, 192, 0.5)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1
          }]
        },
        options: {
          plugins: {
            title: {
              display: true,
              text: 'Monthly Issue Creation'
            }
          }
        }
      });
      
      // 月別グラフ保存
      const monthlyBuffer = monthlyCanvas.toBuffer('image/png');
      await fs.writeFile(`${imgDir}/monthly_issues.png`, monthlyBuffer);
      
      const stats = {
        typeCount,
        priorityCount,
        stateCount,
        monthlyCount
      };
  
      console.log('ダッシュボードを生成中...');
      
      const totalIssues = processedIssues.length;
      const openIssues = processedIssues.filter(issue => issue.state === 'オープン').length;
      const closedIssues = totalIssues - openIssues;
      
      // 最近の未解決Issue（上位5件）
      const recentIssues = processedIssues
        .filter(issue => issue.state === 'オープン')
        .sort((a, b) => b.createdAt - a.createdAt)
        .slice(0, 5);
      
      // 最も長く未解決のIssue（上位5件）
      const oldestIssues = processedIssues
        .filter(issue => issue.state === 'オープン')
        .sort((a, b) => a.createdAt - b.createdAt)
        .slice(0, 5);
      
      // HTMLテンプレート
      const html = `
  <!DOCTYPE html>
  <html lang="ja">
  <head>
      <meta charset="UTF-8">
      <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>プロジェクト Issue ダッシュボード</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
      <style>
          * {
              font-family: "Helvetica Neue", Arial, "Hiragino Kaku Gothic ProN", "Hiragino Sans", Meiryo, sans-serif;
          }
          .card { margin-bottom: 20px; }
          .stat-card { text-align: center; padding: 15px; }
          .stat-number { font-size: 2.5rem; font-weight: bold; }
      </style>
  </head>
  <body>
      <div class="container mt-4">
          <h1>プロジェクト Issue ダッシュボード</h1>
          <p>最終更新: ${new Date().toLocaleString('ja-JP')}</p>
          
          <div class="row mt-4">
              <div class="col-md-4">
                  <div class="card stat-card">
                      <div class="stat-number text-primary">${totalIssues}</div>
                      <div>総Issue数</div>
                  </div>
              </div>
              <div class="col-md-4">
                  <div class="card stat-card">
                      <div class="stat-number text-success">${openIssues}</div>
                      <div>未解決Issue</div>
                  </div>
              </div>
              <div class="col-md-4">
                  <div class="card stat-card">
                      <div class="stat-number text-secondary">${closedIssues}</div>
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
                              ${Object.entries(stats.typeCount).map(([type, count]) => `
                                  <li class="list-group-item d-flex justify-content-between align-items-center">
                                      ${type}
                                      <span class="badge bg-primary rounded-pill">${count}</span>
                                  </li>
                              `).join('')}
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
                              ${Object.entries(stats.priorityCount).map(([priority, count]) => `
                                  <li class="list-group-item d-flex justify-content-between align-items-center">
                                      ${priority}
                                      <span class="badge bg-primary rounded-pill">${count}</span>
                                  </li>
                              `).join('')}
                          </ul>
                      </div>
                  </div>
              </div>
          </div>
          
          <div class="row mt-4">
              <div class="col-md-6">
                  <div class="card">
                      <div class="card-header">
                          Issue統計
                      </div>
                      <div class="card-body">
                          <img src="img/issue_stats.png" class="img-fluid" alt="Issue統計">
                      </div>
                  </div>
              </div>
              
              <div class="col-md-6">
                  <div class="card">
                      <div class="card-header">
                          Issue状態の分布
                      </div>
                      <div class="card-body">
                          <img src="img/issue_state.png" class="img-fluid" alt="Issue状態">
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
                                      ${recentIssues.map(issue => `
                                          <tr>
                                              <td>${issue.number}</td>
                                              <td><a href="${issue.url}" target="_blank">${issue.title}</a></td>
                                              <td>${issue.type}</td>
                                              <td>${issue.priority}</td>
                                          </tr>
                                      `).join('')}
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
                                      ${oldestIssues.map(issue => `
                                          <tr>
                                              <td>${issue.number}</td>
                                              <td><a href="${issue.url}" target="_blank">${issue.title}</a></td>
                                              <td>${issue.createdAt.toLocaleDateString('ja-JP')}</td>
                                              <td>${issue.priority}</td>
                                          </tr>
                                      `).join('')}
                                  </tbody>
                              </table>
                          </div>
                      </div>
                  </div>
              </div>
          </div>
      </div>
      
      <footer class="bg-light text-center py-3 mt-5">
          <p>自動生成されたダッシュボード - <a href="https://github.com/${process.env.GITHUB_REPOSITORY}" target="_blank">${process.env.GITHUB_REPOSITORY}</a></p>
      </footer>
      
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
  </body>
  </html>`;
      
      // UTF-8エンコーディングを明示的に指定
      await fs.writeFile(`${outputDir}/index.html`, html, 'utf8');
      
      // JSONデータとしても保存
      const summary = {
        total_issues: totalIssues,
        open_issues: openIssues,
        closed_issues: closedIssues,
        by_type: stats.typeCount,
        by_priority: stats.priorityCount,
        update_time: new Date().toISOString()
      };
      
      await fs.writeFile(
        `${outputDir}/summary.json`, 
        JSON.stringify(summary, null, 2),
        'utf8'
      );
      
      console.log('完了！ダッシュボードは dashboard/index.html に生成されました');
    } catch (error) {
      console.error('エラーが発生しました:', error);
      process.exit(1);
    }
  }
  
  // スクリプト実行
  main();