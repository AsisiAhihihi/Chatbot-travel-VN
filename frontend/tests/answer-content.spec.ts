import {test,expect} from '@playwright/test';

test('safe Markdown, real source titles and map status stay separate',async({page},info)=>{
 await page.route('**/chat',route=>route.fulfill({json:{
  answer:'**Mang Thít**\n\n- Cảnh lò gạch ven sông.\n- Ký hiệu được escape: \\*\\*.\n\n[Đọc bài về Mang Thít](https://example.org/source?q=a%2Ab)\n<script>alert(1)</script>',
  sources:[{title:'Mang Thít: làng nghề ven sông',url:'https://example.org/source?q=a%2Ab'}],
  places:[],map_action:'keep',map_status:'Chưa có vị trí xác minh; giữ khung nhìn hiện tại.',itinerary:[],route:null
 }}));
 await page.goto('/');
 if(info.project.name==='mobile')await page.getByRole('button',{name:'Trò chuyện cùng Mây',exact:true}).click();
 await page.getByRole('textbox').fill('Mang Thít có gì?');
 await page.getByRole('button',{name:'Gửi câu hỏi'}).click();
 const answer=page.locator('.message.assistant').last();
 await expect(answer.locator('strong')).toHaveText('Mang Thít');
 await expect(answer.locator('li')).toHaveCount(2);
 await expect(answer).not.toContainText('\\*');
 await expect(answer).not.toContainText('Chưa có vị trí');
 await expect(page.locator('.map-advice-status')).toContainText('Chưa có vị trí');
 await expect(answer.locator('script')).toHaveCount(0);
 await expect(answer.getByRole('link',{name:'Đọc bài về Mang Thít'})).toHaveAttribute('href','https://example.org/source?q=a%2Ab');
 await answer.locator('summary').click();
 await expect(answer.getByRole('link',{name:'Mang Thít: làng nghề ven sông'})).toBeVisible();
});

test('live advice covers destinations, region, province, price and followup',async({page},info)=>{
 test.skip(process.env.RAG_LIVE!=='1','Requires the rebuilt index and local API');
 test.setTimeout(240000);
 await page.goto('/');
 if(info.project.name==='mobile')await page.getByRole('button',{name:'Trò chuyện cùng Mây',exact:true}).click();
 for(const question of ['Hạ Long và Tràng An','Gợi ý chuyến đi 3 ngày 2 đêm ở miền Nam','Vĩnh Long có gì?','Mỹ Khê có gì?','Giá đi thuyền Tràng An?','Ở đó chơi gì?','Mang Thít có gì?']){
  if(info.project.name==='mobile'&&!(await page.getByRole('textbox').isVisible()))await page.getByRole('button',{name:'Trò chuyện cùng Mây',exact:true}).click();
  await page.getByRole('textbox').fill(question);
  const response=page.waitForResponse(r=>r.url().endsWith('/chat')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Gửi câu hỏi'}).click();
  const raw=await response;expect(raw.ok()).toBeTruthy();const data=await raw.json();
  await expect(page.locator('.pending')).toHaveCount(0);
  expect(data.answer).not.toMatch(/place_id|content_type|Tên dùng tìm kiếm|giữ nguyên khung nhìn|\\\*/);
  expect(data.sources.every((s:{title:string})=>!s.title.endsWith('.md'))).toBeTruthy();
  if(question==='Hạ Long và Tràng An'){expect(data.answer).toContain('Tràng An');expect(data.answer).not.toContain('Tam Cốc');}
  if(question.includes('3 ngày')){expect(data.answer).toContain('Ngày 3');expect(data.itinerary.length).toBeGreaterThan(0);}
  if(question==='Vĩnh Long có gì?'){expect(data.answer).toContain('Bạn có thể');expect(data.places.length).toBeGreaterThan(2);}
  if(question==='Mỹ Khê có gì?')expect(data.answer).toContain('tỉnh');
  if(question.includes('Giá đi')){expect(data.answer).toContain('tham khảo');expect(data.answer).not.toContain('Tam Cốc');}
  if(question==='Ở đó chơi gì?')expect(data.answer).toContain('Tràng An');
  if(question==='Mang Thít có gì?'){expect(data.map_action).toBe('focus');expect(data.route).toBeNull();}
 }
 await page.screenshot({path:`test-results/${info.project.name}-advice.png`});
});