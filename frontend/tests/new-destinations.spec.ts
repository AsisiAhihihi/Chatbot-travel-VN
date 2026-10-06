import {test,expect} from '@playwright/test';

test('new sourced destination opens popup and focuses map',async({page},info)=>{
 await page.goto('/mien-nam');
 await page.locator('.destinations button').filter({hasText:'Chợ nổi Cái Răng'}).click();
 await expect(page.getByRole('dialog',{name:'Chợ nổi Cái Răng'})).toBeVisible();
 await expect(page.getByRole('dialog')).toContainText('Vị trí tham chiếu');
 await expect.poll(()=>page.evaluate(()=>{
  const map=(document.querySelector('[data-testid="map"]') as HTMLElement & {mapInstance?:any}).mapInstance;
  return map?Math.abs(map.getCenter().lng-105.746):999;
 })).toBeLessThan(0.01);
 await page.screenshot({path:`test-results/${info.project.name}-new-destination.png`});
 await page.getByRole('button',{name:'Toàn Việt Nam'}).click();
 await expect(page.getByRole('dialog')).toHaveCount(0);
});