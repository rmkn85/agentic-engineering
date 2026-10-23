// Optional own-process browser regression. No installed browser is required by make check.
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PROJECT_WORK_BROWSER_MODULE);
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1280,height:900}});
    await page.goto(process.argv[2]);
    await page.waitForFunction(() => document.querySelectorAll('article').length === 5);
    assert.equal(await page.locator('#active article').count(), 2);
    assert.equal(await page.locator('#next article').count(), 1);
    assert.equal(await page.locator('#recent article').count(), 2);
    assert.equal(await page.locator('#other-section').isVisible(), false);
    const keys = await page.locator('article button').evaluateAll(nodes => nodes.map(n=>n.dataset.key));
    assert.equal(new Set(keys).size, keys.length, 'each task must occur once');
    assert.equal(await page.locator('#issues > p.issue').count(), 1);
    assert.match(await page.locator('#issues > p.issue').textContent(), /unresolved local task MISSING-001/);
    assert.equal(await page.locator('#issues details').count(), 1);
    assert.match(await page.locator('#issues summary').textContent(), /2 dependency warnings/);
    assert.equal(await page.locator('#issues details').getAttribute('open'), null);
    await page.locator('#issues summary').click();
    assert.equal(await page.locator('#issues li').count(), 2);
    assert.match(await page.locator('#active').textContent(), /Current obstruction/);
    await page.locator('#scope').selectOption('all');
    await page.waitForFunction(() => document.querySelectorAll('#other article').length === 1);
    assert.match(await page.locator('#other').textContent(), /Outside current queue/);
    assert.equal(await page.locator('article').count(), 6);
    let release;
    const responseGate = new Promise(resolve=>release=resolve);
    await page.route('**/api/overview?**', async route => {await responseGate;await route.continue();});
    await page.locator('#repo').selectOption('sample/two');
    await page.waitForFunction(() => document.querySelector('#live').textContent === 'Loading selected filters…');
    release();
    await page.waitForFunction(() => document.querySelector('#live').textContent.includes('1 matching tasks'));
    assert.equal(await page.locator('article').count(), 1);
    assert.match(await page.locator('article').textContent(), /sample\/two/);
    assert.equal(await page.locator('#issues details').count(), 0, 'warnings follow repository filter');
    assert.equal(await page.locator('#issues > p.issue').count(), 1, 'selected repository errors stay visible');
    console.log('PASS own headless UI: exclusive groups, retained blockers, collapsed warnings, all-records opt-in, loading/filter completion');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
