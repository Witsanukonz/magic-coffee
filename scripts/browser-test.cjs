/* Real browser tests run against a separate SQLite database and media directory. */
const { chromium, expect } = require('@playwright/test');
const { spawn, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'test-results');
fs.mkdirSync(output, { recursive: true });
const runId = Date.now();
const env = { ...process.env, PYTHONUNBUFFERED: '1', DJANGO_DB_PATH: path.join(output, `browser-${runId}.sqlite3`),
  DJANGO_MEDIA_ROOT: path.join(output, `media-${runId}`) };
const python = path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
for (const command of ['migrate', 'seed_demo']) {
  const result = spawnSync(python, ['manage.py', command, '--no-color'], { cwd: root, env, encoding: 'utf8' });
  if (result.status !== 0) throw new Error(result.stderr || result.stdout);
}
const base = 'http://127.0.0.1:8011';
const server = spawn(python, ['manage.py', 'runserver', '127.0.0.1:8011', '--noreload'], { cwd: root, env, windowsHide: true, stdio: ['ignore','pipe','pipe'] });
const log = fs.createWriteStream(path.join(output, 'browser-server.log'));
server.stdout.pipe(log); server.stderr.pipe(log);
const results = [];
let browser;
let liveCustomerPage;
async function step(name, fn) { await fn(); results.push({ name, passed: true }); console.log(`PASS ${name}`); }
async function login(page, username, password='MagicDemo!2026') {
  await page.goto(`${base}/accounts/login/`);
  await page.getByLabel('Username').fill(username);
  await page.getByLabel(/^\s*Password(?: \*)?\s*$/).fill(password);
  await page.getByRole('button', { name: 'SIGN IN', exact: true }).click();
  await page.waitForURL(url => !url.pathname.includes('/login/'));
}
async function logout(page) {
  const desktopLogout = page.locator('.account-menu');
  if (await desktopLogout.isVisible()) {
    await desktopLogout.locator('summary').click();
    await desktopLogout.getByRole('button', { name: 'Logout' }).click();
  } else if (await page.locator('.sidebar-bottom').isVisible()) {
    await page.locator('.sidebar-bottom').getByRole('button', { name: /Logout/ }).click();
  } else {
    await page.getByRole('button', { name: 'Open navigation' }).click();
    await page.locator('#account-nav').getByRole('button', { name: 'Logout' }).click();
  }
}
async function inspect(page, route, width, screenshotName) {
  await page.setViewportSize({ width, height: 900 });
  const response = await page.goto(base + route);
  expect(response.status()).toBe(200);
  await page.evaluate(async () => {
    document.querySelectorAll('img[loading="lazy"]').forEach(image => { image.loading = 'eager'; });
    await document.fonts.ready;
    await Promise.all([...document.images].map(image => image.decode().catch(() => {})));
  });
  const defects = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth > innerWidth + 1,
    broken: [...document.images].filter(img => !img.hidden && img.getAttribute('src') && (!img.complete || img.naturalWidth === 0)).map(img=>img.src),
  }));
  expect(defects, `${route} at ${width}px`).toEqual({ overflow:false, broken:[] });
  if (screenshotName) await page.screenshot({ path:path.join(output,`${screenshotName}-${width}.png`), fullPage:true });
}
(async () => {
  try {
    for (let i=0;i<50;i++) {
      try { if ((await fetch(base)).ok) break; } catch {}
      await new Promise(resolve => setTimeout(resolve,200));
    }
    const edge = 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe';
    browser = await chromium.launch(fs.existsSync(edge) ? { executablePath:edge, headless:true } : { headless:true });
    const context = await browser.newContext({ viewport: { width:1440, height:1000 } });
    const page = await context.newPage();
    const errors=[];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if(message.type()==='error') errors.push(message.text()); });
    page.on('response', response => { if(response.status()>=500) errors.push(`${response.status()} ${response.url()}`); });
    await step('Public pages, images and responsive layout at 375, 768 and 1440px', async () => {
      for (const width of [375,768,1440]) for (const [route,name] of [['/','home'],['/menu/','menu'],['/menu/cafe-latte/','detail'],['/about/',null],['/cart/',null],['/accounts/register/',null],['/accounts/login/',null]])
        await inspect(page,route,width,name);
    });
    await step('Search, category, price filter, sort and pagination through UI', async () => {
      await page.goto(base+'/menu/');
      await page.locator('[data-quick-open]').first().click();
      await expect(page.locator('.quick-order-dialog[open]')).toBeVisible();
      await page.getByRole('button',{name:'Close'}).click();
      await page.getByRole('searchbox',{name:'Search menu'}).fill('latte');
      await page.getByRole('button',{name:'SEARCH'}).click();
      await expect(page.locator('.menu-card')).toHaveCount(3);
      await page.getByRole('link',{name:'CLEAR FILTERS',exact:true}).click();
      await page.getByRole('navigation',{name:'Pagination'}).getByRole('link',{name:'2',exact:true}).click();
      await expect(page.locator('.menu-card')).toHaveCount(12);
      await page.getByRole('navigation',{name:'Menu categories'}).getByRole('link',{name:'BAKERY',exact:true}).click();
      await expect(page.locator('.menu-card')).toHaveCount(4);
      await page.getByText('More menu filters',{exact:true}).click();
      await page.getByLabel('Max price').fill('75');
      await page.getByLabel('Sort by').selectOption('price_low');
      await page.getByRole('button',{name:'APPLY',exact:true}).click();
      await expect(page.locator('.menu-card')).toHaveCount(2);
      await expect(page.locator('.menu-card').first()).toContainText('Blueberry Muffin');
    });
    await step('Registration, guest cart merge, options, quantity and removal', async () => {
      await page.goto(base+'/menu/cafe-latte/');
      await page.getByLabel(/^\s*Size(?: \*)?\s*$/).selectOption('Large');
      await page.getByLabel(/^\s*Temperature(?: \*)?\s*$/).selectOption('Iced');
      await page.getByLabel(/^\s*Sweetness(?: \*)?\s*$/).selectOption('50');
      await page.getByRole('button',{name:'Increase quantity'}).click();
      await page.getByRole('button',{name:/ADD TO ORDER/}).click();
      await expect(page.locator('.cart-items')).toContainText('Large · Iced · 50% sweet');
      await page.goto(base+'/accounts/register/');
      await page.getByLabel('Username').fill('browser_customer');
      await page.getByLabel('Email').fill('browser@example.com');
      await page.getByLabel('First name').fill('Browser');
      await page.getByLabel('Last name').fill('Customer');
      await page.getByLabel(/^\s*Password(?: \*)?\s*$/).fill('BrowserCoffee!2026');
      await page.getByLabel('Password confirmation').fill('BrowserCoffee!2026');
      await page.getByRole('button',{name:'CREATE ACCOUNT'}).click();
      await page.waitForURL('**/menu/');
      await page.goto(base+'/cart/');
      await expect(page.locator('.cart-item')).toHaveCount(1);
      const quantityUpdate = page.waitForResponse(response => response.url().includes('/cart/update/') && response.request().method() === 'POST');
      await page.getByRole('button',{name:'Increase quantity'}).click();
      await quantityUpdate;
      await expect(page.getByLabel('Quantity for Cafe Latte')).toHaveValue('3');
      await expect(page.locator('[data-order-total]').last()).toContainText('255.00');
      await expect(page.getByRole('button',{name:'UPDATE',exact:true})).toHaveCount(0);
      await page.reload();
      await expect(page.getByLabel('Quantity for Cafe Latte')).toHaveValue('3');
      await expect(page.locator('.summary-total')).toContainText('255.00');
      await page.getByRole('button',{name:'REMOVE',exact:true}).click();
      await expect(page.getByText('Your order is empty.',{exact:false})).toBeVisible();
      await page.goto(base+'/menu/cafe-latte/');
      await page.getByLabel(/^\s*Size(?: \*)?\s*$/).selectOption('Large');
      await page.getByLabel(/^\s*Temperature(?: \*)?\s*$/).selectOption('Iced');
      await page.getByLabel(/^\s*Sweetness(?: \*)?\s*$/).selectOption('50');
      await page.getByRole('button',{name:/ADD TO ORDER/}).click();
    });
    await step('Checkout, order success, order history and profile', async () => {
      await page.getByRole('link',{name:/CONTINUE TO ORDER/}).click();
      await page.getByLabel('Full name').fill('Browser Customer');
      await page.getByLabel('Phone').fill('0812345678');
      await expect(page.getByLabel('FREE COFFEE REWARD')).toBeHidden();
      await page.getByLabel(/^\s*Dine In(?: \*)?\s*$/).check();
      await page.getByLabel(/^\s*Note(?: \*)?\s*$/).fill('Classroom workflow test');
      await page.screenshot({path:path.join(output,'checkout-desktop.png'),fullPage:true});
      await page.getByRole('button',{name:/PLACE ORDER/}).click();
      await expect(page.getByRole('heading',{name:'ORDER IN!'})).toBeVisible();
      await page.getByRole('link',{name:/VIEW ORDER/}).click();
      await expect(page.locator('.badge.pending')).toBeVisible();
      await expect(page.locator('table')).toContainText('Large Iced / 50% sweet');
      await inspect(page,'/orders/',375,'orders');
      await inspect(page,'/orders/1/',375,'order');
      await page.setViewportSize({width:1440,height:1000});
      await page.goto(base+'/accounts/profile/');
      await page.getByLabel('First name').fill('Updated');
      await page.getByRole('button',{name:'SAVE CHANGES'}).click();
      await expect(page.getByLabel('First name')).toHaveValue('Updated');
      await logout(page);
    });
    await step('Admin login, dashboard responsive pages and order status update', async () => {
      await login(page,'demo_admin');
      for(const width of [375,768,1440]) for(const [route,name] of [['/dashboard/','dashboard'],['/dashboard/menu/','dashboard-menu'],['/dashboard/menu/add/','add-menu'],['/dashboard/users/',null],['/dashboard/categories/',null],['/dashboard/orders/',null],['/dashboard/orders/1/',null]])
        await inspect(page,route,width,name);
      await page.setViewportSize({width:375,height:900});
      await page.goto(base+'/dashboard/');
      await page.getByRole('button',{name:'Toggle dashboard navigation'}).click();
      await expect(page.locator('.dashboard-sidebar')).toBeInViewport();
      await page.locator('.dashboard-sidebar').getByRole('link',{name:'Menu',exact:true}).click();
      await page.waitForURL('**/dashboard/menu/');
      await page.setViewportSize({width:1440,height:1000});
      await page.goto(base+'/dashboard/orders/1/');
      for(const status of ['preparing','ready']) {
        await page.getByLabel('New status').selectOption(status);
        await page.getByRole('button',{name:'UPDATE STATUS'}).click();
        await expect(page.locator(`.order-info .badge.${status}`)).toBeVisible();
        if (status === 'preparing') {
          const customerContext = await browser.newContext({ viewport: { width:1440, height:1000 } });
          liveCustomerPage = await customerContext.newPage();
          liveCustomerPage.on('pageerror', error => errors.push(error.message));
          liveCustomerPage.on('console', message => { if(message.type()==='error') errors.push(message.text()); });
          await login(liveCustomerPage,'browser_customer','BrowserCoffee!2026');
          await liveCustomerPage.goto(base+'/orders/1/');
          await expect(liveCustomerPage.locator('.badge.preparing')).toBeVisible();
        }
      }
      await expect(liveCustomerPage.locator('.badge.ready')).toBeVisible({timeout:8000});
    });
    let createdMenuId;
    await step('Menu create with all form controls, image preview and saved upload', async () => {
      await page.goto(base+'/dashboard/menu/add/');
      await page.getByLabel(/^\s*Menu Name(?: \*)?\s*$/).count();
      await page.getByLabel(/^\s*Name(?: \*)?\s*$/).fill('Browser Special');
      await page.getByLabel(/^\s*Category(?: \*)?\s*$/).selectOption({label:'Coffee'});
      await page.getByLabel(/^\s*Description(?: \*)?\s*$/).fill('Created through the actual dashboard form.');
      await page.getByLabel(/^\s*Price(?: \*)?\s*$/).fill('99');
      await page.getByLabel(/^\s*Stock(?: \*)?\s*$/).fill('8');
      await page.getByLabel(/^\s*Menu type(?: \*)?\s*$/).selectOption('coffee');
      await page.getByLabel(/^\s*Both(?: \*)?\s*$/).check();
      await page.getByLabel(/^\s*Large(?: \*)?\s*$/).check();
      await page.getByLabel(/^\s*Is available(?: \*)?\s*$/).check();
      await page.getByLabel(/^\s*Is featured(?: \*)?\s*$/).check();
      await page.getByLabel(/^\s*Available date(?: \*)?\s*$/).fill('2026-01-01');
      await page.getByLabel(/^\s*Image(?: \*)?\s*$/).setInputFiles(path.join(root,'static/images/menu/cafe-latte.jpg'));
      await expect(page.locator('#image-preview')).toBeVisible();
      await expect(page.locator('#image-preview')).toHaveAttribute('src',/^blob:/);
      await page.screenshot({path:path.join(output,'image-preview.png'),fullPage:true});
      await page.getByRole('button',{name:'SAVE MENU ITEM'}).click();
      await page.waitForURL('**/dashboard/menu/');
      const row=page.getByRole('row').filter({hasText:'Browser Special'});
      await expect(row).toContainText('99.00');
      const editHref=await row.getByRole('link',{name:'Edit',exact:true}).getAttribute('href');
      createdMenuId=editHref.match(/menu\/(\d+)/)[1];
      await row.getByRole('link',{name:'View',exact:true}).click();
      await expect(page.locator('.resource-detail img')).toBeVisible();
      await page.getByRole('link',{name:'EDIT MENU ↗'}).click();
      await page.getByLabel(/^\s*Price(?: \*)?\s*$/).fill('109');
      await page.getByLabel(/^\s*Stock(?: \*)?\s*$/).fill('12');
      await page.getByRole('button',{name:'SAVE MENU ITEM'}).click();
      await page.waitForURL('**/dashboard/menu/');
      await page.goto(base+'/menu/browser-special/');
      await expect(page.locator('.detail-price')).toContainText('109 THB');
      await expect(page.locator('.detail-copy>.stock-label')).toContainText('12 LEFT');
    });
    await step('Delete confirmation modal cancels and then deletes menu', async () => {
      await page.goto(base+'/dashboard/menu/');
      let row=page.getByRole('row').filter({hasText:'Browser Special'});
      await row.getByRole('button',{name:'Delete',exact:true}).click();
      await expect(page.getByRole('dialog')).toBeVisible();
      await page.getByRole('button',{name:'Keep item'}).click();
      await expect(row).toBeVisible();
      await row.getByRole('button',{name:'Delete',exact:true}).click();
      await page.getByRole('button',{name:'Yes, delete'}).click();
      await page.waitForURL('**/dashboard/menu/');
      await expect(page.getByRole('row').filter({hasText:'Browser Special'})).toHaveCount(0);
    });
    await step('Category create, read, edit and delete through UI', async () => {
      await page.goto(base+'/dashboard/categories/add/');
      await page.getByLabel(/^\s*Name(?: \*)?\s*$/).fill('Seasonal');
      await page.getByLabel(/^\s*Description(?: \*)?\s*$/).fill('For the season');
      await page.getByRole('button',{name:'SAVE CATEGORY'}).click();
      await page.waitForURL('**/dashboard/categories/');
      await page.getByRole('row').filter({hasText:'Seasonal'}).getByRole('link',{name:'View',exact:true}).click();
      await expect(page.locator('.resource-detail')).toContainText('For the season');
      await page.getByRole('link',{name:'EDIT CATEGORY ↗'}).click();
      await page.getByLabel(/^\s*Name(?: \*)?\s*$/).fill('Seasonal specials');
      await page.getByRole('button',{name:'SAVE CATEGORY'}).click();
      await page.waitForURL('**/dashboard/categories/');
      await page.getByRole('row').filter({hasText:'Seasonal specials'}).getByRole('button',{name:'Delete'}).click();
      await page.getByRole('button',{name:'Yes, delete'}).click();
      await page.waitForURL('**/dashboard/categories/');
      await expect(page.getByRole('row').filter({hasText:'Seasonal specials'})).toHaveCount(0);
    });
    await step('User create, read, edit without changing password, disable, enable and delete', async () => {
      await page.goto(base+'/dashboard/users/add/');
      await page.getByLabel('Username').fill('ui_user');
      await page.getByLabel('Email').fill('ui_user@example.com');
      await page.getByLabel('First name').fill('UI');
      await page.getByLabel('Last name').fill('Test');
      await page.getByLabel(/^\s*Role(?: \*)?\s*$/).selectOption('customer');
      await page.getByLabel(/^\s*New password(?: \*)?\s*$/).fill('UserCoffee!2026');
      await page.getByLabel(/^\s*Confirm password(?: \*)?\s*$/).fill('UserCoffee!2026');
      await page.getByRole('button',{name:'SAVE USER'}).click();
      await page.waitForURL('**/dashboard/users/');
      await page.getByRole('row').filter({hasText:'ui_user@example.com'}).getByRole('link',{name:'View',exact:true}).click();
      await expect(page.locator('.resource-detail')).toContainText('ui_user@example.com');
      await page.getByRole('link',{name:'EDIT USER ↗'}).click();
      await expect(page.getByLabel(/^\s*New password(?: \*)?\s*$/)).toBeEmpty();
      await page.getByLabel('First name').fill('Edited');
      await page.getByRole('button',{name:'SAVE USER'}).click();
      await page.waitForURL('**/dashboard/users/');
      let row=page.getByRole('row').filter({hasText:'ui_user@example.com'});
      await expect(row).toContainText('Edited');
      await row.getByRole('button',{name:'Disable',exact:true}).click();
      await expect(row).toContainText('Inactive');
      await row.getByRole('button',{name:'Enable',exact:true}).click();
      await expect(row).toContainText('Active');
      await row.getByRole('button',{name:'Delete',exact:true}).click();
      await page.getByRole('button',{name:'Yes, delete'}).click();
      await page.waitForURL('**/dashboard/users/');
      await expect(row).toHaveCount(0);
    });
    await step('Customer sees Ready and server denies dashboard access', async () => {
      await logout(page);
      await login(page,'browser_customer','BrowserCoffee!2026');
      await page.goto(base+'/orders/1/');
      await expect(page.locator('.badge.ready')).toBeVisible();
      // Use the context request client so the intentional 403 is not a browser console error.
      expect((await context.request.get(base+'/dashboard/')).status()).toBe(403);
      await page.goto(base+'/accounts/password-reset/');
      await page.getByLabel('Email').fill('browser@example.com');
      await page.getByRole('button',{name:'RESET PASSWORD'}).click();
      await expect(page.getByRole('heading',{name:'Check the server terminal.'})).toBeVisible();
      const logText=fs.readFileSync(path.join(output,'browser-server.log'),'utf8');
      expect(logText).toContain('/accounts/reset/');
    });
    await step('No JavaScript errors, browser console errors or server errors', async () => { expect(errors).toEqual([]); });
    fs.writeFileSync(path.join(output,'browser-results.json'),JSON.stringify({passed:true,checks:results},null,2));
    console.log(`All ${results.length} browser checks passed.`);
  } catch(error) {
    if(browser) for(const context of browser.contexts()) for(const page of context.pages()) {
      await page.screenshot({path:path.join(output,'failure.png'),fullPage:true}).catch(()=>{});
      fs.writeFileSync(path.join(output,'failure.html'),await page.content());
    }
    console.error(error);
    fs.writeFileSync(path.join(output,'browser-results.json'),JSON.stringify({passed:false,checks:results,error:String(error)},null,2));
    process.exitCode=1;
  } finally {
    if(browser) await browser.close();
    server.kill();
    log.end();
  }
})();
