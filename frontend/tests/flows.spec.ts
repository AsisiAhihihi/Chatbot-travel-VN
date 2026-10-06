import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
const catalogue=JSON.parse(readFileSync(new URL('../../src/rag/catalogue.json',import.meta.url),'utf8')) as {id:string;name:string;aliases:string[];region:string;coordinates:number[]}[];
const normalize=(s:string)=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase();
test.beforeEach(async({page})=>{
 await page.route('**/chat',async route=>{
  const {question}=route.request().postDataJSON();
  const q=normalize(question),itinerary=q.includes('lich trinh');
  const places=catalogue.filter(p=>p.coordinates&&([normalize(p.name),...p.aliases].some(n=>q.includes(n))||(q.includes('mien trung')&&p.region==='trung')));
  await route.fulfill({json:{answer:q.includes('an binh')?'Bạn đang hỏi tỉnh hoặc thành phố nào?':places.length?'Gợi ý từ API: '+places.map(p=>p.name).join(', '):'Tài liệu chưa có dữ liệu.',sources:[],places,map_action:places.length===1?'focus':places.length?'fit':'keep',itinerary:itinerary?places.map(p=>p.id):[],route:itinerary?{kind:'illustrative',coordinates:places.map(p=>p.coordinates)}:null}});
 });
});
test('navigation, destination, itinerary and reset',async({page},info)=>{
 await page.goto('/');
 for(const [label,path] of [['Miền Bắc','/mien-bac'],['Miền Trung','/mien-trung'],['Miền Nam','/mien-nam'],['Việt Nam','/']]){await page.getByRole('navigation').getByRole('link',{name:label,exact:true}).click();await expect(page).toHaveURL(new RegExp(`${path}$`));}
 if(info.project.name==='mobile')await page.getByRole('button',{name:'Trò chuyện cùng Mây',exact:true}).click();
 await page.getByRole('button',{name:'Hội An có gì?',exact:true}).click();await expect(page.getByRole('dialog',{name:'Hội An'})).toBeVisible();await expect(page).toHaveURL(/mien-trung$/);
 await page.getByRole('button',{name:'Đóng thông tin địa điểm'}).click();
 if(info.project.name==='mobile')await page.getByRole('button',{name:'Trò chuyện cùng Mây',exact:true}).click();
 await page.getByRole('button',{name:'Lịch trình miền Trung',exact:true}).click();await expect(page.locator('.route-label')).toContainText('Tuyến minh họa');
 await page.getByRole('button',{name:'Toàn Việt Nam'}).click();await expect(page.locator('.route-label')).toHaveCount(0);await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.screenshot({path:`test-results/${info.project.name}-overview.png`});
 if(info.project.name==='mobile')await page.getByRole('button',{name:'Trò chuyện cùng Mây',exact:true}).click();
 await page.locator('.chat-places button').filter({hasText:'Hội An'}).first().click();await expect(page.getByRole('dialog',{name:'Hội An'})).toBeVisible();
 await page.screenshot({path:`test-results/${info.project.name}-place.png`});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
});
test('multiple places, ambiguity and no results',async({page},info)=>{
 await page.goto('/');if(info.project.name==='mobile')await page.getByRole('button',{name:'Trò chuyện cùng Mây',exact:true}).click();
 await page.getByRole('button',{name:'Hạ Long và Tràng An',exact:true}).click();await expect(page).toHaveURL(/mien-bac$/);await expect(page.getByRole('dialog')).toHaveCount(0);
 if(info.project.name==='mobile')await page.getByRole('button',{name:'Trò chuyện cùng Mây',exact:true}).click();
 await page.getByRole('textbox').fill('An Bình');await page.getByRole('button',{name:'Gửi câu hỏi'}).click();await expect(page.locator('.message').last()).toContainText('tỉnh hoặc thành phố nào');await expect(page).toHaveURL(/mien-bac$/);
 await page.getByRole('textbox').fill('Một nơi chưa biết');await page.getByRole('button',{name:'Gửi câu hỏi'}).click();await expect(page.locator('.message').last()).toContainText('chưa có dữ liệu');
});