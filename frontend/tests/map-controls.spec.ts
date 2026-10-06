import {test,expect} from '@playwright/test';

test('popup leaves both zoom buttons visible and clickable',async({page})=>{
 await page.goto('/mien-trung');
 await page.locator('.destinations button').filter({hasText:'Hội An'}).first().click();
 const popup=page.getByRole('dialog',{name:'Hội An'});
 await expect(popup).toBeVisible();
 for(const label of ['Phóng to','Thu nhỏ']){
  const zoom=page.getByRole('button',{name:label,exact:true});
  const a=await popup.boundingBox(),b=await zoom.boundingBox();
  expect(a&&b).toBeTruthy();
  expect(a!.x+a!.width<=b!.x||b!.x+b!.width<=a!.x||a!.y+a!.height<=b!.y||b!.y+b!.height<=a!.y).toBeTruthy();
  await zoom.click();
 }
 await expect(popup).toBeVisible();
 await page.screenshot({path:`test-results/${test.info().project.name}-zoom-popup.png`});
});

test('itinerary shows straight-line distance and reset clears it',async({page},info)=>{
 await page.route('**/chat',route=>route.fulfill({json:{answer:'Lịch trình sơ bộ',sources:[],places:[],map_action:'keep',itinerary:['a','b'],route:{kind:'illustrative',coordinates:[[105,10],[105,11]],distance_m:111195}}}));
 await page.goto('/');
 if(info.project.name==='mobile')await page.getByRole('button',{name:'Trò chuyện cùng Mây',exact:true}).click();
 await page.getByRole('textbox').fill('Lịch trình 2 ngày');
 await page.getByRole('button',{name:'Gửi câu hỏi'}).click();
 await expect(page.locator('.route-label')).toContainText('111,2 km');
 await expect(page.locator('.route-label')).toContainText('Không phải quãng đường đi thực tế');
 await page.getByRole('button',{name:'Toàn Việt Nam'}).click();
 await expect(page.locator('.route-label')).toHaveCount(0);
});