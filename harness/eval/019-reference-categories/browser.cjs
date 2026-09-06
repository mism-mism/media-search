// Run against an isolated local app, with Playwright available on NODE_PATH.
// Only category management uses the real server. Search replies are controlled
// to reproduce a pre-mutation result arriving late. No AI calls are made.
const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const base = process.env.CATEGORY_TEST_URL || 'http://127.0.0.1:8019';
(async () => {
  const browser = await chromium.launch(process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH, headless: true} : {headless:true});
  try {
    for (const mutation of ['create','delete']) for (const late of [false,true]) {
      const page = await browser.newPage();
      const errors = []; page.on('pageerror',e=>errors.push(e.message));
      const catalog = await (await page.request.get(base+'/api/library/categories')).json();
      for(const c of catalog.categories) await page.request.delete(base+'/api/library/categories/'+c.category_id);
      const created = await page.request.post(base+'/api/library/categories', {multipart: {
        name:'既存カテゴリ', criteria:'対象が見える', references:{name:'reference.png', mimeType:'image/png', buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64')}
      }});
      assert.equal(created.status(),201);
      let release;
      let requested = false;
      const gate = new Promise(resolve=>release=resolve);
      await page.route('**/api/search?*', async route=> {
        requested = true;
        if(late) await gate;
        await route.fulfill({json:{results:[{asset_id:'fixture.png',display_name:'変更前の検索結果',media_type:'image',tags:[],score:1,thumbnail_url:'/unused.png',category_report:{decisions:[{name:'古い該当タグ',outcome:'match',reason:'変更前の判定'}]}}]}});
      });
      await page.goto(base);
      await page.locator('#q').fill('古い該当タグ');
      await page.locator('#go').click();
      while(!requested) await page.waitForTimeout(10);
      if(!late) await page.getByText('変更前の検索結果',{exact:true}).waitFor();
      await page.locator('#categoriesTab').click();
      await page.locator('#categories h3').waitFor();
      if(mutation==='delete') {
        page.once('dialog',d=>d.accept());
        await page.getByRole('button',{name:'カテゴリを削除',exact:true}).click();
        await page.waitForFunction(()=>document.getElementById('status').textContent.startsWith('カテゴリを削除しました'));
      } else {
        await page.locator('#categoryName').fill('追加カテゴリ');
        await page.locator('#categoryCriteria').fill('別の対象が見える');
        await page.locator('#categoryReferences').setInputFiles({name:'reference.png',mimeType:'image/png',buffer:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64')});
        await page.locator('#saveCategory').click();
        await page.waitForFunction(()=>document.getElementById('status').textContent.startsWith('見本カテゴリを登録しました'));
      }
      const responseDone = late ? page.waitForResponse(r=>r.url().includes('/api/search?')) : null;
      release();
      if(responseDone) await responseDone;
      await page.waitForTimeout(100);
      await page.locator('#searchTab').click();
      assert.equal(await page.locator('#out').getByText('変更前の検索結果',{exact:true}).count(),0,'stale search result after catalog mutation');
      assert.equal(await page.locator('#searchCount').textContent(),'');
      assert.match(await page.locator('#out').textContent(),/もう一度検索/);
      assert.equal(await page.locator('#out').getAttribute('aria-busy'),null);
      assert.deepEqual(errors,[]);
      console.log(JSON.stringify({mutation,late,searchInvalidation:'PASS',errors}));
      const finalCatalog = await (await page.request.get(base+'/api/library/categories')).json();
      for(const c of finalCatalog.categories) await page.request.delete(base+'/api/library/categories/'+c.category_id);
      await page.close();
    }
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
