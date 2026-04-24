#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const WORKSPACE = process.env.OPENCLAW_WORKSPACE || 'C:\\Users\\BurtClaw\\openclaw_workspace';
const OUTPUT_FILE = path.join(__dirname, 'security-data.json');
const SKILLS_DIR = path.join(WORKSPACE, 'skills');
const SYSTEM_SKILLS_DIR = process.env.OPENCLAW_SYSTEM_SKILLS || 'C:\\Users\\BurtClaw\\AppData\\Roaming\\npm\\node_modules\\openclaw\\skills';

const SEVERITY_LEVELS = {
  CRITICAL: { score: 40, color: '#dc2626' },
  HIGH: { score: 25, color: '#f97316' },
  MEDIUM: { score: 10, color: '#eab308' },
  LOW: { score: 3, color: '#3b82f6' },
  INFO: { score: 0, color: '#6b7280' }
};

const SCAN_RULES = [
  {
    id: 'CRED-001',
    name: 'Hardcoded Credentials',
    severity: 'CRITICAL',
    pattern: /\b(API_KEY|TOKEN|SECRET|PASSWORD|PRIVATE_KEY|ACCESS_KEY)\s*[=:]\s*['"][^'"]{8,}['"]/gi,
    check: (content, file) => !content.includes('process.env') && !content.includes('os.environ')
  },
  {
    id: 'EXEC-001',
    name: 'Dangerous Execution - eval()',
    severity: 'CRITICAL',
    pattern: /\beval\s*\(/gi,
    check: () => true
  },
  {
    id: 'EXEC-002',
    name: 'Dangerous Execution - exec with string',
    severity: 'HIGH',
    pattern: /exec\s*\(\s*['"`][^'"`]+['"`]/gi,
    check: () => true
  },
  {
    id: 'EXEC-003',
    name: 'Dangerous Execution - child_process with shell',
    severity: 'HIGH',
    pattern: /child_process.*shell:\s*true/gi,
    check: () => true
  },
  {
    id: 'ENV-001',
    name: 'Environment Variable Collection',
    severity: 'MEDIUM',
    pattern: /process\.env|os\.environ|getenv/gi,
    check: () => true
  },
  {
    id: 'ENV-002',
    name: 'Broad Env Access Pattern',
    severity: 'LOW',
    pattern: /Object\.keys\s*\(\s*process\.env\s*\)/gi,
    check: () => true
  },
  {
    id: 'WEBHOOK-001',
    name: 'Webhook Without Token Validation',
    severity: 'HIGH',
    pattern: /webhook|hook.*endpoint|webhook.*url/gi,
    check: (content) => !content.includes('verifySignature') && !content.includes('validateToken')
  },
  {
    id: 'BROWSER-001',
    name: 'Browser Automation - No Authentication Check',
    severity: 'MEDIUM',
    pattern: /browser|playwright|selenium|puppeteer/gi,
    check: (content) => !content.includes('authenticate') && !content.includes('login')
  },
  {
    id: 'FILE-001',
    name: 'Unrestricted File Read',
    severity: 'HIGH',
    pattern: /readFileSync|readFile.*without.*path.*validation/gi,
    check: (content, file) => !content.includes('realpathSync') && !content.includes('path.isAbsolute')
  },
  {
    id: 'FILE-002',
    name: 'Path Traversal Risk',
    severity: 'MEDIUM',
    pattern: /path\.join.*user.*input|resolve.*user|__dirname.*\+/gi,
    check: () => true
  },
  {
    id: 'SQL-001',
    name: 'SQL Injection Risk - String Concatenation',
    severity: 'CRITICAL',
    pattern: /execute\s*\([^'"`]*\+[^'"`]*\)|query\s*\([^'"`]*\+[^'"`]*\)/gi,
    check: () => true
  },
  {
    id: 'CRYPTO-001',
    name: 'Weak Cryptography',
    severity: 'HIGH',
    pattern: /md5|sha1|des\(|rc4/i,
    check: () => true
  },
  {
    id: 'AUTH-001',
    name: 'Missing Authentication Check',
    severity: 'HIGH',
    pattern: /route|endpoint|handler/gi,
    check: (content) => !content.includes('authenticate') && !content.includes('requireAuth') && !content.includes('isAuthorized')
  },
  {
    id: 'HTTPS-001',
    name: 'HTTP Instead of HTTPS',
    severity: 'MEDIUM',
    pattern: /['"]http:\/\/[^'"]+['"]/gi,
    check: () => true
  },
  {
    id: 'LOG-001',
    name: 'Sensitive Data in Logs',
    severity: 'MEDIUM',
    pattern: /console\.log\s*\([^)]*\b(password|secret|key|token)\b/gi,
    check: () => true
  }
];

function scanFile(filePath) {
  const findings = [];
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    const ext = path.extname(filePath);
    const relevantRules = SCAN_RULES.filter(rule => {
      if (['.js', '.ts', '.py', '.sh'].includes(ext)) return true;
      if (['.json', '.yaml', '.yml'].includes(ext) && rule.id.startsWith('EXEC')) return false;
      return !rule.id.startsWith('EXEC') && !rule.id.startsWith('SQL');
    });

    for (const rule of relevantRules) {
      const matches = content.match(rule.pattern);
      if (matches && matches.length > 0) {
        if (rule.check && !rule.check(content, filePath)) continue;
        
        const lines = content.split('\n');
        const matchPositions = [];
        for (let i = 0; i < lines.length; i++) {
          for (const match of matches) {
            if (lines[i].includes(match)) {
              matchPositions.push({
                line: i + 1,
                content: lines[i].trim().substring(0, 100)
              });
            }
          }
        }

        findings.push({
          ruleId: rule.id,
          ruleName: rule.name,
          severity: rule.severity,
          file: path.relative(WORKSPACE, filePath),
          matchCount: matches.length,
          lines: matchPositions.slice(0, 3)
        });
      }
    }
  } catch (e) {
    // Skip files that can't be read
  }
  return findings;
}

function scanDirectory(dir, results = []) {
  let entries;
  try {
    entries = fs.readdirSync(dir, { withFileTypes: true });
  } catch {
    return results;
  }

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name === 'node_modules' || entry.name === '.git' || entry.name === 'dist') continue;
      scanDirectory(fullPath, results);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name);
      if (['.js', '.ts', '.py', '.sh', '.json', '.yaml', '.yml', '.env', '.md'].includes(ext)) {
        const findings = scanFile(fullPath);
        if (findings.length > 0) {
          results.push({ file: fullPath, findings });
        }
      }
    }
  }
  return results;
}

function getSkillMetadata(skillPath) {
  const skillFile = path.join(skillPath, 'SKILL.md');
  try {
    const content = fs.readFileSync(skillFile, 'utf8');
    const nameMatch = content.match(/^name:\s*(.+)$/m) || content.match(/^#\s+(.+)/m);
    const descMatch = content.match(/^description:\s*(.+)$/m);
    return {
      name: nameMatch ? nameMatch[1].trim().replace(/^["']|["']$/g, '') : path.basename(skillPath),
      description: descMatch ? descMatch[1].trim().replace(/^["']|["']$/g, '') : ''
    };
  } catch {
    return { name: path.basename(skillPath), description: '' };
  }
}

function getComponentStatus() {
  const checks = [
    { name: 'Gateway', status: 'unknown', url: 'http://127.0.0.1:18789/health' },
    { name: 'WhatsApp', status: 'unknown', url: 'http://127.0.0.1:18789/hooks/whatsapp/status' },
    { name: 'Hooks', status: 'unknown', url: 'http://127.0.0.1:18789/hooks' },
    { name: 'Dashboard', status: 'unknown', url: 'http://127.0.0.1:18791/health' }
  ];

  return new Promise((resolve) => {
    const promises = checks.map(check => {
      return new Promise((res) => {
        try {
          const http = require('http');
          const req = http.get(check.url, { timeout: 2000 }, (response) => {
            check.status = response.statusCode === 200 ? 'healthy' : 'degraded';
            response.resume();
            res();
          });
          req.on('error', () => { check.status = 'offline'; res(); });
          req.on('timeout', () => { req.destroy(); check.status = 'timeout'; res(); });
        } catch {
          check.status = 'offline';
          res();
        }
      });
    });

    Promise.all(promises).then(() => {
      const statusMap = {
        healthy: { value: 'ok', label: 'Healthy', color: '#22c55e' },
        degraded: { value: 'warn', label: 'Degraded', color: '#eab308' },
        offline: { value: 'fail', label: 'Offline', color: '#dc2626' },
        timeout: { value: 'warn', label: 'Timeout', color: '#f97316' },
        unknown: { value: 'unknown', label: 'Unknown', color: '#6b7280' }
      };
      
      const result = {};
      checks.forEach(c => {
        result[c.name] = statusMap[c.status] || statusMap.unknown;
      });
      resolve(result);
    });
  });
}

function getSystemInfo() {
  const os = require('os');
  const envVars = Object.keys(process.env);
  
  return {
    platform: os.platform(),
    arch: os.arch(),
    nodeVersion: process.version,
    openclawVersion: process.env.OPENCLAW_VERSION || 'unknown',
    dashboardVersion: '1.0.0',
    uptime: os.uptime(),
    workspace: WORKSPACE,
    skillsDir: fs.existsSync(SKILLS_DIR) ? 'found' : 'not found',
    systemSkillsDir: fs.existsSync(SYSTEM_SKILLS_DIR) ? 'found' : 'not found',
    envFlags: {
      OPENCLAW_ALLOW_ATTACHMENT_FILEPATH_COPY: process.env.OPENCLAW_ALLOW_ATTACHMENT_FILEPATH_COPY === '1',
      OPENCLAW_ENABLE_MUTATING_OPS: process.env.OPENCLAW_ENABLE_MUTATING_OPS === '1',
      OPENCLAW_LOAD_KEYS_ENV: process.env.OPENCLAW_LOAD_KEYS_ENV === '1',
      OPENCLAW_AUTH_TOKEN: process.env.OPENCLAW_AUTH_TOKEN ? 'set' : 'not set',
      OPENCLAW_HOOK_TOKEN: process.env.OPENCLAW_HOOK_TOKEN ? 'set' : 'not set',
      OPENCLAW_ENABLE_SYSTEMCTL_RESTART: process.env.OPENCLAW_ENABLE_SYSTEMCTL_RESTART === '1'
    },
    totalEnvVars: envVars.length,
    sensitiveEnvVars: envVars.filter(v => 
      /KEY|SECRET|TOKEN|PASSWORD|PRIVATE|ADMIN/i.test(v) && !v.includes('PATH')
    ).length
  };
}

function calculateSecurityScore(findings) {
  let totalPenalty = 0;
  
  for (const finding of findings) {
    for (const issue of finding.findings) {
      const severityInfo = SEVERITY_LEVELS[issue.severity] || SEVERITY_LEVELS.INFO;
      totalPenalty += severityInfo.score;
    }
  }

  const baseScore = 100;
  const finalScore = Math.max(0, baseScore - totalPenalty);
  
  let label, color;
  if (finalScore >= 90) { label = 'Excellent'; color = '#22c55e'; }
  else if (finalScore >= 75) { label = 'Good'; color = '#22c55e'; }
  else if (finalScore >= 60) { label = 'Fair'; color = '#eab308'; }
  else if (finalScore >= 40) { label = 'Poor'; color = '#f97316'; }
  else { label = 'Critical'; color = '#dc2626'; }

  return { value: finalScore, label, color };
}

function categorizeWarnings(findings) {
  const warnings = {
    CRITICAL: [],
    HIGH: [],
    MEDIUM: [],
    LOW: [],
    INFO: []
  };

  for (const finding of findings) {
    for (const issue of finding.findings) {
      const category = issue.severity;
      if (warnings[category]) {
        warnings[category].push({
          ruleId: issue.ruleId,
          ruleName: issue.ruleName,
          file: issue.file,
          matchCount: issue.matchCount,
          lines: issue.lines
        });
      }
    }
  }

  return warnings;
}

async function runAudit() {
  console.log('🔍 OpenClaw Security Audit');
  console.log('==========================\n');

  const results = {
    lastUpdated: new Date().toISOString(),
    securityScore: null,
    activeWarnings: [],
    componentStatus: {},
    systemInfo: {},
    skillsScanned: 0,
    filesScanned: 0,
    issuesFound: 0
  };

  const scanResults = [];
  
  if (fs.existsSync(SKILLS_DIR)) {
    const workspaceEntries = fs.readdirSync(SKILLS_DIR, { withFileTypes: true });
    for (const entry of workspaceEntries) {
      if (entry.isDirectory()) {
        const skillMeta = getSkillMetadata(path.join(SKILLS_DIR, entry.name));
        scanDirectory(path.join(SKILLS_DIR, entry.name), scanResults);
        results.skillsScanned++;
      }
    }
  }

  if (fs.existsSync(SYSTEM_SKILLS_DIR)) {
    const systemEntries = fs.readdirSync(SYSTEM_SKILLS_DIR, { withFileTypes: true });
    for (const entry of systemEntries) {
      if (entry.isDirectory()) {
        const skillMeta = getSkillMetadata(path.join(SYSTEM_SKILLS_DIR, entry.name));
        scanDirectory(path.join(SYSTEM_SKILLS_DIR, entry.name), scanResults);
        results.skillsScanned++;
      }
    }
  }

  results.filesScanned = scanResults.length;
  results.issuesFound = scanResults.reduce((sum, r) => sum + r.findings.length, 0);

  results.securityScore = calculateSecurityScore(scanResults);
  results.activeWarnings = categorizeWarnings(scanResults);

  results.componentStatus = await getComponentStatus();
  results.systemInfo = getSystemInfo();

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(results, null, 2));
  console.log(`✅ Security audit complete`);
  console.log(`   Score: ${results.securityScore.value}/100 (${results.securityScore.label})`);
  console.log(`   Skills scanned: ${results.skillsScanned}`);
  console.log(`   Files scanned: ${results.filesScanned}`);
  console.log(`   Issues found: ${results.issuesFound}`);
  console.log(`   Output: ${OUTPUT_FILE}\n`);

  if (results.issuesFound > 0) {
    console.log('⚠️  Issues by severity:');
    for (const [severity, issues] of Object.entries(results.activeWarnings)) {
      if (issues.length > 0) {
        console.log(`   ${severity}: ${issues.length} issues`);
      }
    }
  }

  return results;
}

if (require.main === module) {
  runAudit().catch(console.error);
}

module.exports = { runAudit, scanFile, scanDirectory, SCAN_RULES };
