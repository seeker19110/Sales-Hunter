// Browser acceptance uses Node 22's built-in WebSocket: no npm dependencies.
import { spawn } from 'node:child_process';
import { readFile } from 'node:fs/promises';

const [chromePath, profilePath, casesPath] = process.argv.slice(2);
const cases = JSON.parse(await readFile(casesPath, 'utf8'));
const chrome = spawn(chromePath, [
  '--headless', '--no-sandbox', '--disable-dev-shm-usage',
  '--disable-background-networking', '--disable-component-update',
  '--disable-default-apps', '--disable-extensions', '--disable-sync',
  '--no-first-run', '--no-default-browser-check', '--enable-automation',
  '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=0',
  `--user-data-dir=${profilePath}`, 'about:blank',
], { stdio: ['ignore', 'ignore', 'pipe'] });
let socket;
const deadline = setTimeout(() => {
  console.error('Browser acceptance exceeded its 60-second deadline');
  chrome.kill('SIGKILL');
  process.exitCode = 1;
  socket?.close();
}, 60000);
try {
  const endpoint = await new Promise((resolve, reject) => {
    let logs = '';
    chrome.on('error', reject);
    chrome.on('exit', (code) => reject(new Error(`Chrome exited before readiness: ${code}`)));
    chrome.stderr.on('data', (data) => {
      logs = (logs + data.toString()).slice(-8192);
      const match = logs.match(/DevTools listening on (ws:\/\/127\.0\.0\.1:\d+\/[^\s]+)/);
      if (match) resolve(match[1]);
    });
  });
  socket = new WebSocket(endpoint);
  const pending = new Map();
  let sequence = 0;
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(String(event.data));
    if (!pending.has(message.id)) return;
    const { resolve, reject, timer } = pending.get(message.id);
    clearTimeout(timer);
    pending.delete(message.id);
    if (message.error) reject(new Error(JSON.stringify(message.error)));
    else resolve(message.result);
  });
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true });
    socket.addEventListener('error', reject, { once: true });
  });
  function call(method, params = {}, sessionId) {
    return new Promise((resolve, reject) => {
      const id = ++sequence;
      const timer = setTimeout(() => {
        pending.delete(id);
        reject(new Error(`CDP timeout: ${method}`));
      }, 10000);
      pending.set(id, { resolve, reject, timer });
      socket.send(JSON.stringify({ id, method, params, sessionId }));
    });
  }
  console.log(JSON.stringify(await call('Browser.getVersion')));
  for (const item of cases) {
    const { targetId } = await call('Target.createTarget', { url: 'about:blank' });
    const { sessionId } = await call('Target.attachToTarget', { targetId, flatten: true });
    await call('Emulation.setDeviceMetricsOverride', {
      width: 390, height: 844, deviceScaleFactor: 1, mobile: true,
    }, sessionId);
    const navigation = await call('Page.navigate', { url: item.url }, sessionId);
    if (navigation.errorText) throw new Error(navigation.errorText);
    const selector = item.row_id ? `[data-publication-id="${item.row_id}"]` : "body";
    let rendered;
    for (let attempt = 0; attempt < 100; attempt++) {
      rendered = await call('Runtime.evaluate', {
        expression: `JSON.stringify({ready:document.readyState, href:location.href,
          text:document.querySelector(${JSON.stringify(selector)})?.innerText, scripts:document.scripts.length,
          width:innerWidth, scroll:document.documentElement.scrollWidth})`,
        returnByValue: true,
      }, sessionId);
      rendered = JSON.parse(rendered.result.value);
      if (rendered.ready === 'complete' && rendered.href === item.url) break;
      await new Promise((resolve) => setTimeout(resolve, 50));
    }
    if (rendered.ready !== 'complete' || rendered.href !== item.url) {
      throw new Error(`Page did not load: ${item.url}`);
    }
    for (const expected of item.expected) {
      if (!rendered.text.includes(expected)) throw new Error(`Missing ${expected}: ${item.url}`);
    }
    if (rendered.scripts !== 0) throw new Error(`Unescaped script: ${item.url}`);
    if (rendered.scroll > rendered.width) throw new Error(`Viewport overflow: ${item.url}`);
    console.log(`PASS ${item.url} mobile=${rendered.width} no executable source script`);
    await call('Target.closeTarget', { targetId });
  }
  console.log(`${cases.length} real browser pages passed`);
} finally {
  clearTimeout(deadline);
  socket?.close();
  chrome.kill('SIGTERM');
}
