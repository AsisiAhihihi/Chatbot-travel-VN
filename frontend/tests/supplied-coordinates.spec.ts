import {test,expect} from '@playwright/test';

test('supplied coordinates show resolved names; zoom-only points have no marker',async({page})=>{
 await page.goto('/mien-bac');
 await page.locator('.destinations button').filter({hasText:'Đồi chè Long Cốc'}).click();
 await expect(page.getByRole('dialog')).toContainText('Long Cốc — điểm tham chiếu làng Long Cốc');
 await expect(page.getByRole('dialog')).toContainText('không đặt marker');
 await page.waitForFunction(()=>{
  const m=(document.querySelector('[data-testid="map"]') as HTMLElement & {mapInstance?:any})?.mapInstance;
  return !!m?.getSource('places');
 });
 const ids=await page.getByTestId('map').evaluate(async el=>{
  const source=(el as HTMLElement & {mapInstance?:any}).mapInstance.getSource('places');
  const data=await source.getData();return data.features.map((f:any)=>f.properties.id);
 });
 expect(ids).not.toContain('phu_tho_poi_02');
 expect(ids).not.toContain('tay_ninh_poi_04');
 expect(ids).not.toContain('tay_ninh_poi_05');
 expect(ids).toContain('vinh_long_poi_02');
 await page.getByRole('button',{name:'Đóng thông tin địa điểm'}).click();
 await page.locator('.destinations button').filter({hasText:'Hội Lim'}).click();
 await expect(page.getByRole('dialog')).toContainText('chùa Hồng Ân, đồi Lim');
});