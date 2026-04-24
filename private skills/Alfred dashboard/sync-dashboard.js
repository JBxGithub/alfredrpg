/**
 * Alfred Dashboard Sync - 簡化版 v3.0
 * 將安全數據同步到 GitHub Pages
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

// 配置
const CONFIG = {
  MAX_RETRIES: 3,
  RETRY_DELAY: 5000,
  LOCAL_DASHBOARD_URL: 'http://127.0.0.1:18791',
  GITHUB_REPO: 'JBxGithub/alfredrpg',
  GITHUB_FILE: 'dashboard.html'
};

// 日誌
function log(level, message) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] ${level}: ${message}`);
}

// 獲取本地儀表板數據
async function fetchLocalData() {
  return new Promise((resolve) => {
    const req = http.get(CONFIG.LOCAL_DASHBOARD_URL, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ success: true, data }));
    });
    req.on('error', () => resolve({ success: false, error: 'Connection failed' }));
    req.setTimeout(10000, () => {
      req.destroy();
      resolve({ success: false, error: 'Timeout' });
    });
  });
}

// 讀取本地 dashboard.html
function readLocalDashboard() {
  const dashboardPath = path.join(__dirname, 'dashboard.html');
  try {
    return fs.readFileSync(dashboardPath, 'utf8');
  } catch (error) {
    log('ERROR', `無法讀取 dashboard.html: ${error.message}`);
    return null;
  }
}

// 獲取 GitHub 文件 SHA
async function getFileSha() {
  return new Promise((resolve) => {
    const options = {
      hostname: 'api.github.com',
      path: `/repos/${CONFIG.GITHUB_REPO}/contents/${CONFIG.GITHUB_FILE}`,
      method: 'GET',
      headers: {
        'User-Agent': 'Alfred-Dashboard-Sync',
        'Authorization': `token ${process.env.GITHUB_TOKEN}`,
        'Accept': 'application/vnd.github.v3+json'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve(json.sha || null);
        } catch {
          resolve(null);
        }
      });
    });

    req.on('error', () => resolve(null));
    req.setTimeout(10000, () => {
      req.destroy();
      resolve(null);
    });
    req.end();
  });
}

// 上傳到 GitHub
async function uploadToGitHub(content, sha) {
  return new Promise((resolve) => {
    const body = JSON.stringify({
      message: `Alfred Dashboard Sync - ${new Date().toISOString()}`,
      content: Buffer.from(content).toString('base64'),
      sha: sha
    });

    const options = {
      hostname: 'api.github.com',
      path: `/repos/${CONFIG.GITHUB_REPO}/contents/${CONFIG.GITHUB_FILE}`,
      method: 'PUT',
      headers: {
        'User-Agent': 'Alfred-Dashboard-Sync',
        'Authorization': `token ${process.env.GITHUB_TOKEN}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        'Accept': 'application/vnd.github.v3+json'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const json = JSON.parse(data);
          resolve({ success: res.statusCode === 200 || res.statusCode === 201, data: json });
        } catch {
          resolve({ success: false, error: 'Invalid response' });
        }
      });
    });

    req.on('error', (err) => resolve({ success: false, error: err.message }));
    req.setTimeout(30000, () => {
      req.destroy();
      resolve({ success: false, error: 'Timeout' });
    });
    req.write(body);
    req.end();
  });
}

// 主函數
async function main() {
  log('INFO', '🔄 Alfred Dashboard Sync v3.0 啟動');

  // 檢查 GITHUB_TOKEN
  if (!process.env.GITHUB_TOKEN) {
    log('ERROR', '❌ GITHUB_TOKEN 環境變數未設置');
    process.exit(1);
  }

  // 讀取本地儀表板
  const content = readLocalDashboard();
  if (!content) {
    log('ERROR', '❌ 無法讀取 dashboard.html');
    process.exit(1);
  }

  log('INFO', `📄 讀取 dashboard.html (${content.length} bytes)`);

  // 獲取文件 SHA
  log('INFO', '🔍 獲取 GitHub 文件資訊...');
  const sha = await getFileSha();
  if (sha) {
    log('INFO', `📝 現有文件 SHA: ${sha.substring(0, 8)}...`);
  } else {
    log('INFO', '📝 創建新文件');
  }

  // 重試機制
  for (let attempt = 1; attempt <= CONFIG.MAX_RETRIES; attempt++) {
    log('INFO', `📤 上傳嘗試 ${attempt}/${CONFIG.MAX_RETRIES}...`);
    
    const result = await uploadToGitHub(content, sha);
    
    if (result.success) {
      log('SUCCESS', '✅ 同步成功！');
      log('INFO', `🌐 儀表板: https://${CONFIG.GITHUB_REPO.split('/')[0]}.github.io/${CONFIG.GITHUB_REPO.split('/')[1]}/dashboard.html`);
      process.exit(0);
    }

    log('WARN', `⚠️ 嘗試 ${attempt} 失敗: ${result.error || 'Unknown error'}`);
    
    if (attempt < CONFIG.MAX_RETRIES) {
      log('INFO', `⏳ ${CONFIG.RETRY_DELAY/1000}秒後重試...`);
      await new Promise(r => setTimeout(r, CONFIG.RETRY_DELAY));
    }
  }

  log('ERROR', '❌ 同步失敗 (重試次數耗盡)');
  process.exit(1);
}

main();
