import type {Place} from './types';
import {displayPlace} from './publicAssets';
// Travel regions are not administrative divisions; Tây Nguyên belongs to Central.
// Shared coordinates always use [longitude, latitude].
let cached:Place[]|undefined;
export async function loadPlaces(signal?:AbortSignal):Promise<Place[]>{
 if(cached)return cached;
 const response=await fetch(`${import.meta.env.BASE_URL}data/places.json`,{signal});
 if(!response.ok)throw new Error('Không tải được danh mục địa điểm.');
 const data=await response.json();
 if(!Array.isArray(data)||data.some(p=>typeof p.id!=='string'||typeof p.name!=='string'||!Array.isArray(p.aliases)))throw new Error('Danh mục địa điểm không hợp lệ.');
 cached=data.map(displayPlace);
 return cached!;
}
