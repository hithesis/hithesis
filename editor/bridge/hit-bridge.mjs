#!/usr/bin/env node
// HιT webapp 本机桥：在你自己的电脑上开一个只听本机的小服务，网页里的 Agent 通过它读写你指定的文件夹、运行命令。
// 用法：node hit-bridge.mjs --dir ~/thesis [--port 7711] [--origin https://schrodingerblume.github.io]
// 零依赖，Node 18 起。令牌第一次运行时生成并存在 ~/.hit-bridge/token，之后不变；网页设置里填一次就行。
import http from 'node:http';
import { spawn } from 'node:child_process';
import { promises as fs, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import crypto from 'node:crypto';

const args = Object.fromEntries(process.argv.slice(2).map((a, i, all) => (a.startsWith('--') ? [a.slice(2), all[i + 1]?.startsWith('--') || all[i + 1] === undefined ? true : all[i + 1]] : [])).filter((x) => x.length));
if (args.help || args.h) {
  console.log(`用法：node hit-bridge.mjs --dir <文件夹> [--port 7711] [--origin <网页地址>] [--token <令牌>] [--any-origin]
  --dir      Agent 能读写的文件夹（必填；命令也在这里面跑）
  --port     端口，默认 7711
  --origin   允许哪个网页连（默认 https://schrodingerblume.github.io 与本机的 localhost 开发地址）
  --token    自定义令牌；不给就用 ~/.hit-bridge/token（第一次自动生成）`);
  process.exit(0);
}
const ROOT = path.resolve(String(args.dir || process.cwd()));
const PORT = Number(args.port) || 7711;
const ORIGINS = [args.origin, 'https://schrodingerblume.github.io', /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/].filter(Boolean);
const tokenFile = path.join(os.homedir(), '.hit-bridge', 'token');
let TOKEN = typeof args.token === 'string' ? args.token : '';
if (!TOKEN) {
  if (!existsSync(tokenFile)) { mkdirSync(path.dirname(tokenFile), { recursive: true }); writeFileSync(tokenFile, crypto.randomBytes(18).toString('base64url'), { mode: 0o600 }); }
  TOKEN = readFileSync(tokenFile, 'utf8').trim();
}
const MAX_OUT = 200 * 1024;
const MAX_FILE = 20 * 1024 * 1024;

const inside = (p) => { const abs = path.resolve(ROOT, p || '.'); if (abs !== ROOT && !abs.startsWith(ROOT + path.sep)) throw Object.assign(new Error(`路径越出了 ${ROOT}`), { status: 403 }); return abs; };
const isText = (buf) => { const n = Math.min(buf.length, 4096); for (let i = 0; i < n; i++) if (buf[i] === 0) return false; return true; };
const which = (cmd) => new Promise((r) => { const p = spawn(process.platform === 'win32' ? 'where' : 'which', [cmd]); p.on('close', (c) => r(c === 0)); p.on('error', () => r(false)); });

async function run(body) {
  const cwd = inside(body.cwd || '.');
  const timeout = Math.min(Math.max(Number(body.timeout) || 120, 1), 1800) * 1000;
  return new Promise((resolve) => {
    const sh = process.platform === 'win32' ? ['cmd.exe', ['/d', '/s', '/c', body.cmd]] : ['/bin/sh', ['-c', body.cmd]];
    const p = spawn(sh[0], sh[1], { cwd, env: { ...process.env, TERM: 'dumb', NO_COLOR: '1' } });
    let out = '', err = '', killed = false;
    const timer = setTimeout(() => { killed = true; p.kill('SIGKILL'); }, timeout);
    p.stdout.on('data', (d) => { if (out.length < MAX_OUT) out += d.toString('utf8'); });
    p.stderr.on('data', (d) => { if (err.length < MAX_OUT) err += d.toString('utf8'); });
    if (body.stdin) p.stdin.end(String(body.stdin)); else p.stdin.end();
    p.on('error', (e) => { clearTimeout(timer); resolve({ code: -1, stdout: out, stderr: String(e.message) }); });
    p.on('close', (code) => { clearTimeout(timer); resolve({ code: killed ? -9 : code, stdout: out.slice(0, MAX_OUT), stderr: err.slice(0, MAX_OUT), timedOut: killed }); });
  });
}

async function handle(req, res, url, body) {
  if (url.pathname === '/ping') return { ok: true, dir: ROOT, node: process.version, platform: process.platform, tools: { typst: await which('typst'), python: await which('python3') || await which('python'), git: await which('git') } };
  if (url.pathname === '/ls') {
    const dir = inside(url.searchParams.get('path') || '.');
    const ents = await fs.readdir(dir, { withFileTypes: true });
    const rows = [];
    for (const e of ents) { if (e.name.startsWith('.')) continue; const st = await fs.stat(path.join(dir, e.name)).catch(() => null); rows.push({ name: e.name, dir: e.isDirectory(), size: st?.size ?? 0, mtime: st?.mtimeMs ?? 0 }); }
    return { path: path.relative(ROOT, dir) || '.', entries: rows.sort((a, b) => Number(b.dir) - Number(a.dir) || a.name.localeCompare(b.name)) };
  }
  if (url.pathname === '/read') {
    const p = inside(url.searchParams.get('path'));
    const st = await fs.stat(p);
    if (st.size > MAX_FILE) throw Object.assign(new Error('文件超过 20 MB'), { status: 413 });
    const buf = await fs.readFile(p);
    return isText(buf) && !url.searchParams.get('b64') ? { path: path.relative(ROOT, p), text: buf.toString('utf8'), size: st.size } : { path: path.relative(ROOT, p), b64: buf.toString('base64'), size: st.size };
  }
  if (url.pathname === '/write' && req.method === 'POST') {
    const p = inside(body.path);
    await fs.mkdir(path.dirname(p), { recursive: true });
    await fs.writeFile(p, body.b64 !== undefined ? Buffer.from(String(body.b64), 'base64') : String(body.text ?? ''));
    return { ok: true, path: path.relative(ROOT, p) };
  }
  if (url.pathname === '/run' && req.method === 'POST') { if (!body.cmd) throw Object.assign(new Error('缺 cmd'), { status: 400 }); return run(body); }
  throw Object.assign(new Error('没有这个接口'), { status: 404 });
}

http.createServer(async (req, res) => {
  const origin = req.headers.origin || '';
  const allowed = ORIGINS.some((o) => (o instanceof RegExp ? o.test(origin) : o === origin)) || args['any-origin'] === true;
  const cors = { 'Access-Control-Allow-Origin': allowed ? origin : 'null', 'Access-Control-Allow-Headers': 'authorization, content-type', 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', 'Access-Control-Max-Age': '600', Vary: 'Origin' };
  if (req.method === 'OPTIONS') { res.writeHead(204, cors); return res.end(); }
  const send = (status, obj) => { res.writeHead(status, { ...cors, 'Content-Type': 'application/json; charset=utf-8' }); res.end(JSON.stringify(obj)); };
  if (origin && !allowed) return send(403, { error: `不接受来自 ${origin} 的请求（启动时加 --origin ${origin}）` });
  if ((req.headers.authorization || '') !== `Bearer ${TOKEN}`) return send(401, { error: '令牌不对' });
  let raw = ''; req.on('data', (c) => { raw += c; if (raw.length > 64 * 1024 * 1024) req.destroy(); });
  req.on('end', async () => {
    try {
      const body = raw ? JSON.parse(raw) : {};
      const url = new URL(req.url, 'http://x');
      send(200, await handle(req, res, url, body));
    } catch (e) { send(e.status || 500, { error: e.message }); }
  });
}).listen(PORT, '127.0.0.1', () => {
  console.log(`HιT 本机桥已启动
  文件夹：${ROOT}
  地址：  http://127.0.0.1:${PORT}
  令牌：  ${TOKEN}
把地址和令牌填进网页的 Agent 设置 › 沙盒 › 本机桥，点「试连」。只听本机、只认这个令牌、只碰这个文件夹；关掉这个窗口就断开。`);
});
