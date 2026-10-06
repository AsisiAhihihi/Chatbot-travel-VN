import {useState} from 'react';
import type {Place} from './types';

// Parent keys this component by destination and URL, so errors never leak to another popup.
export function PlaceImage({place}:{place:Place}) {
 const [failed,setFailed]=useState(false),[attempt,setAttempt]=useState(0);
 if(!place.image?.url)return <div className="image-fallback" role="status">Chưa có ảnh cho địa điểm này</div>;
 if(failed)return <div className="image-fallback" role="status">Không tải được ảnh địa điểm. <button onClick={()=>{setFailed(false);setAttempt(n=>n+1);}}>Thử tải lại ảnh</button></div>;
  return <img key={attempt} src={place.image.url} alt={place.image.caption||place.name} loading="lazy" decoding="async" onError={()=>setFailed(true)}/>;
}