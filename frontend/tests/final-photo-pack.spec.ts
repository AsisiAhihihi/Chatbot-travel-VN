import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('all 17 supplied photos decode and show honest source credits',async({page})=>{
 test.setTimeout(120000);
 const rows=JSON.parse(readFileSync('../anh_17_dia_diem_kem_nguon/anh_17_dia_diem/image_sources.json','utf8'));
 await page.goto('/');
 const places=await (await page.request.get('/data/places.json')).json();
 expect(places.filter((p:any)=>p.image?.url)).toHaveLength(209);
 for(const row of rows){
  const place=places.find((p:any)=>p.id===row.id);
  expect(place.image.source).toBe(row.source_page_url);
  expect(place.image.rights_status).toBe('permission_required');
  expect(place.image.license).toBeUndefined();
  const response=await page.request.get(place.image.url);expect(response.ok()).toBeTruthy();
  const size=await page.evaluate(async(url:string)=>{
   const image=new Image();image.src=url;await image.decode();return [image.naturalWidth,image.naturalHeight];
  },place.image.url);
  expect(size).toEqual([row.width,row.height]);
  await page.locator(`nav a[href="/mien-${place.region}"]`).click();
  const matches=places.filter((p:any)=>p.coordinates&&p.region===place.region&&p.name.includes(row.name));
  await page.locator('.destinations button').filter({hasText:row.name}).nth(matches.findIndex((p:any)=>p.id===row.id)).click();
  const popup=page.getByRole('dialog');
  await expect(popup.locator('img')).toHaveAttribute('alt',row.caption);
  await expect.poll(()=>popup.locator('img').evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBe(true);
  await expect(popup).toContainText('chưa xác nhận quyền dùng lại');
  await expect(popup).not.toContainText('undefined');
  await expect(popup.getByRole('link').first()).toHaveAttribute('href',row.source_page_url);
  await page.getByRole('button',{name:'Đóng thông tin địa điểm'}).click();
 }
});