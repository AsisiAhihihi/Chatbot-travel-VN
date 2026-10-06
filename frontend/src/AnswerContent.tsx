import type {ReactNode} from 'react';
import type {Place} from './types';

// Small, safe Markdown subset using React text nodes only: no HTML injection.
// Decode Markdown escapes at tokenization, NOT with replacements on the payload.
function inline(text:string,places:Place[],onSelect:(place:Place)=>void):ReactNode[]{
 const nodes:ReactNode[]=[];let plain='';
 const flush=()=>{if(plain){nodes.push(plain);plain='';}};
 for(let i=0;i<text.length;){
  if(text[i]==='\\'&&i+1<text.length&&/[\\*_[\]`#]/.test(text[i+1])){plain+=text[i+1];i+=2;continue;}
  if(text.startsWith('**',i)){const end=text.indexOf('**',i+2);if(end>i+2){flush();nodes.push(<strong key={`bold-${i}`}>{inline(text.slice(i+2,end),places,onSelect)}</strong>);i=end+2;continue;}}
  if(text[i]==='['){const match=text.slice(i).match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/);if(match){flush();nodes.push(<a key={`link-${i}`} href={match[2]} target="_blank" rel="noreferrer">{match[1]}</a>);i+=match[0].length;continue;}}
  if(text[i]==='`'){const end=text.indexOf('`',i+1);if(end>i+1){flush();nodes.push(<code key={`code-${i}`}>{text.slice(i+1,end)}</code>);i=end+1;continue;}}
  const place=[...places].sort((a,b)=>b.name.length-a.name.length).find(p=>text.startsWith(p.name,i));
  if(place){flush();nodes.push(<button className="inline-place" key={`place-${i}`} onClick={()=>onSelect(place)}>{place.name}</button>);i+=place.name.length;continue;}
  plain+=text[i++];
 }
 flush();return nodes;
}

export function AnswerContent({text,places=[],onSelect}:{text:string;places?:Place[];onSelect:(place:Place)=>void}){
 const blocks:ReactNode[]=[];const lines=text.split('\n');let paragraph:string[]=[];let list:string[]=[];
 const flushParagraph=()=>{if(paragraph.length){blocks.push(<p key={`p-${blocks.length}`}>{inline(paragraph.join('\n'),places,onSelect)}</p>);paragraph=[];}};
 const flushList=()=>{if(list.length){blocks.push(<ul key={`ul-${blocks.length}`}>{list.map((line,index)=><li key={index}>{inline(line,places,onSelect)}</li>)}</ul>);list=[];}};
 for(const line of lines){
  if(!line.trim()){flushParagraph();flushList();continue;}
  const bullet=line.match(/^\s*(?:[-*]|\d+\.)\s+(.+)$/);
  if(bullet){flushParagraph();list.push(bullet[1]);continue;}
  flushList();const heading=line.match(/^#{1,3}\s+(.+)$/);
  if(heading){flushParagraph();blocks.push(<p key={`h-${blocks.length}`}><strong>{inline(heading[1],places,onSelect)}</strong></p>);}
  else paragraph.push(line);
 }
 flushParagraph();flushList();return <div className="answer-content">{blocks}</div>;
}