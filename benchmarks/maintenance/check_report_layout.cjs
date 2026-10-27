// Render local deliverables only; no external site or simulation interaction.
const { chromium } = require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const path = require('path');
(async () => {
  const browser = await chromium.launch({headless: true, channel: 'msedge'});
  const page = await browser.newPage({viewport: {width: 1680, height: 1050}, deviceScaleFactor: 1});
  const root = 'D:/STGPlanner/codex/outputs';
  const findings = [];
  for (const stem of ['Scene4四算法与论文对比汇总', 'Scene4基线算法对比报告', '代码目录说明', 'STGPlanner部署报告']) {
    await page.goto('file:///' + root + '/' + stem + '.html', {waitUntil: 'load'});
    const result = await page.evaluate(() => ({
      title: document.title,
      tables: document.querySelectorAll('table').length,
      firstTableRows: document.querySelector('table').rows.length,
      firstTableRight: document.querySelector('table').getBoundingClientRect().right,
      pageWidth: document.documentElement.clientWidth,
      pageScrollWidth: document.documentElement.scrollWidth,
      brokenImages: [...document.images].filter(i => !i.complete || !i.naturalWidth).length,
      containsStageComplete: document.body.innerText.includes('阶段性完成')
    }));
    if (result.brokenImages || !result.containsStageComplete || result.firstTableRight > result.pageWidth) {
      throw new Error(JSON.stringify({stem, ...result}));
    }
    await page.screenshot({path: path.join(root, stem + '.preview.png'), fullPage: false});
    findings.push({stem, ...result});
  }
  fs.writeFileSync(path.join(root, 'Scene4报告布局核验.json'), JSON.stringify({all_passed: true, findings}, null, 2) + '\n');
  console.log(JSON.stringify(findings));
  await browser.close();
})().catch(error => {console.error(error.message); process.exit(1);});
