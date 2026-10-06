import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
const images=JSON.parse(readFileSync(new URL('../../src/rag/catalogue_images.json',import.meta.url),'utf8')) as {id:string;image:{url:string;author:string;license:string}}[];
test('reviewed local photos load and show credit in popup',async({page,request})=>{
 for(const record of images){
  const response=await request.get(record.image.url);
  expect(response.ok()).toBeTruthy();
  expect(response.headers()['content-type']).toMatch(/image\//);
 }
 await page.goto('/');
 await page.locator('.destinations button').filter({hasText:'Thác Bản Giốc'}).click();
 const popup=page.getByRole('dialog',{name:'Thác Bản Giốc'});
 await expect.poll(()=>popup.locator('img').evaluate((img:HTMLImageElement)=>img.naturalWidth)).toBeGreaterThan(0);
 await expect(popup).toContainText('CC BY 2.0');
 await page.screenshot({path:`test-results/local-photos-${test.info().project.name}.png`});
});

test('four user-supplied destination photos display in their own popups',async({page})=>{
 await page.goto('/');
 for(const name of ['Hồ Cấm Sơn','Hồ Pá Khoang','Mộ cự thạch Hàng Gòn','Cồn Vành']){
  await page.getByRole('button',{name:'Toàn Việt Nam'}).click();
  await page.locator('.destinations button').filter({hasText:name}).click();
  const popup=page.getByRole('dialog',{name,exact:true});
  await expect.poll(()=>popup.locator('img').evaluate((img:HTMLImageElement)=>img.naturalWidth)).toBeGreaterThan(0);
  await expect(popup).toContainText('Người dùng cung cấp');
 }
});