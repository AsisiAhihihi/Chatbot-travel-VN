import {loadPlaces} from './data';
import type {Reply,Place} from './types';
import {displayPlace} from './publicAssets';
const apiBase=(import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/,'');
export const demo=!apiBase;
const normalize=(s:string)=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase();
export function mockReply(question:string,places:Place[]):Reply {
 const q=normalize(question); const base:Reply={answer:'',sources:[],places:[],map_action:'keep',itinerary:[],route:null};
 if(q.includes('an binh')) return {...base,answer:'Bạn đang hỏi An Bình ở tỉnh hoặc thành phố nào? Mình cần làm rõ trước khi đổi bản đồ.'};
 let found=places.filter(p=>[normalize(p.name),...p.aliases].some(a=>q.includes(a)));
 if(!found.length) {const r=q.includes('mien bac')?'bac':q.includes('mien trung')?'trung':q.includes('mien nam')?'nam':null;if(r)found=places.filter(p=>p.region===r);}
 if(!found.length)return {...base,answer:'Bản demo chưa có dữ liệu đáng tin cậy cho địa điểm này nên chưa xác định được vị trí trên bản đồ. Bạn có thể thử Hội An, Tràng An hoặc Phú Quốc.'};
  const itinerary=q.includes('lich trinh')||q.includes('hanh trinh');
  const mapped=found.filter(p=>p.coordinates);
  return {answer:(itinerary?'Mình gợi ý danh mục tham quan dưới đây.':`Bạn có thể tìm hiểu ${found.map(p=>p.name).join(', ')}. ${found[0].description}`)+(mapped.length!==found.length?' Một số điểm chưa có tọa độ kiểm chứng nên chưa hiển thị trên bản đồ.':'')+' Đây là nội dung mẫu, chưa phải câu trả lời từ RAG.',places:found,sources:found.map(p=>({title:p.name,url:p.source})),map_action:mapped.length===1?'focus':mapped.length?'fit':'keep',itinerary:itinerary?found.map(p=>p.id):[],route:itinerary&&found.length>1&&mapped.length===found.length?{kind:'illustrative',coordinates:mapped.map(p=>p.coordinates!)}:null};
}
export async function ask(question:string,signal:AbortSignal,history:{role:string;text:string}[]):Promise<Reply>{
  if(demo){const places=await loadPlaces(signal);await new Promise<void>((resolve,reject)=>{if(signal.aborted){reject(new DOMException('Cancelled','AbortError'));return;}const cancel=()=>{clearTimeout(t);reject(new DOMException('Cancelled','AbortError'));};const t=setTimeout(()=>{signal.removeEventListener('abort',cancel);resolve();},650);signal.addEventListener('abort',cancel,{once:true});});return mockReply(question,places);}
  const res=await fetch(`${apiBase}/chat`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question,history:history.slice(-20).map(m=>({role:m.role,text:m.text.slice(0,12000)}))}),signal});
  if(!res.ok){const error=await res.json().catch(()=>null);throw new Error(typeof error?.detail==='string'?error.detail:'Không kết nối được trợ lý. Vui lòng thử lại.');}
 const data=await res.json() as Reply;
  if(!Array.isArray(data.places)||!Array.isArray(data.sources)||!Array.isArray(data.itinerary)||typeof data.answer!=='string'||!['keep','focus','fit'].includes(data.map_action))throw new Error('Phản hồi không hợp lệ.');
  data.sources=data.sources.filter(s=>s.url.startsWith('/sources/')||/^https?:\/\//.test(s.url)).map(s=>({...s,url:s.url.startsWith('/sources/')?`${apiBase}${s.url}`:s.url}));
 data.places=data.places.map(p=>({...p,coordinates:p.coordinates&&p.coordinates.length===2&&p.coordinates.every(Number.isFinite)&&Math.abs(p.coordinates[0])<=180&&Math.abs(p.coordinates[1])<=90?p.coordinates:null}));
  data.places=data.places.map(displayPlace);
  return data;
}