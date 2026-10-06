import {test,expect} from '@playwright/test';

test('lazy-loaded map fills its exploration area despite provider CSS',async({page})=>{
 await page.goto('/');
 const map=page.getByTestId('map');
 await expect(map.locator('canvas')).toBeAttached();
 // Reproduce the provider rule arriving after the application's stylesheet.
 await page.addStyleTag({content:'.maplibregl-map { position: relative; overflow: hidden; }'});
 for(const path of ['/', '/mien-bac', '/mien-trung', '/mien-nam']){
  if(path!=='/')await page.locator(`nav a[href="${path}"]`).click();
  await expect.poll(()=>map.evaluate(el=>{
   const box=el.getBoundingClientRect(),parent=el.parentElement!.getBoundingClientRect();
   return getComputedStyle(el).position==='absolute'&&box.height>200&&Math.abs(box.height-parent.height)<1;
  })).toBe(true);
 }
 await page.screenshot({path:`test-results/map-visible-${test.info().project.name}.png`});
});

test('catalogue loads independently and retries without losing navigation',async({page})=>{
 let attempts=0;
 await page.route('**/data/places.json',async route=>{
  attempts++;
  if(attempts===1)await route.fulfill({status:503,body:'Unavailable'});
  else await route.continue();
 });
 await page.goto('/mien-nam');
 await expect(page.getByRole('navigation')).toBeVisible();
 await expect(page.getByRole('button',{name:'Thử lại danh mục'})).toBeVisible();
 await page.getByRole('button',{name:'Thử lại danh mục'}).click();
 await expect(page.locator('.destinations button').filter({hasText:'Chợ nổi Cái Răng'})).toBeVisible();
 await expect(page).toHaveURL(/mien-nam$/);
 expect(attempts).toBe(2);
});