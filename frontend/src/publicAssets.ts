import type {Place} from './types';

export function assetUrl(url:string):string {
 return url.startsWith('/')&&!url.startsWith('//')?`${import.meta.env.BASE_URL}${url.slice(1)}`:url;
}
export function displayPlace(place:Place):Place {
 const image=place.image;
 if(import.meta.env.VITE_PUBLIC_DEPLOY==='true'&&(!image?.license||image.rights_status==='permission_required'||!/^(CC BY|CC0|Public domain)/i.test(image.license)))return {...place,image:undefined};
 return image?{...place,image:{...image,url:assetUrl(image.url),source:assetUrl(image.source)}}:place;
}