import fs from 'fs';
const S='https://woddiinstitute.com', SB='https://hghezktzbepikpjzlxwe.supabase.co';
const ANON='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhnaGV6a3R6YmVwaWtwanpseHdlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY0NjAxNzUsImV4cCI6MjA5MjAzNjE3NX0.wi15a4p_5v6Rd8T3csP4U5BuNUm7VrHvxmo28_wH1uo';
const out={}; fs.mkdirSync('res',{recursive:true});
const auth=await (await fetch(SB+'/auth/v1/token?grant_type=password',{method:'POST',headers:{apikey:ANON,'Content-Type':'application/json'},body:JSON.stringify({email:'qa-mentor-v180@woddi.invalid',password:'gKKP6iq54K4DVSXR2hDYK9-J'})})).json();
const tok=auth.access_token; out.signin=!!tok; if(!tok){out.err=auth; fs.writeFileSync('res/results.json',JSON.stringify(out,null,1)); process.exit(0);}
async function post(fn,body){const t=Date.now(); const r=await fetch(S+'/.netlify/functions/'+fn,{method:'POST',headers:{Authorization:'Bearer '+tok,'Content-Type':'application/json'},body:JSON.stringify(body)}); let j; const tx=await r.text(); try{j=JSON.parse(tx)}catch(e){j={raw:tx.slice(0,300)}} return {status:r.status,ms:Date.now()-t,j};}
const EN='Craig, start with what you already sell. Write down your three best customers this week and ask each one what they would pay more for.';
const Q={en:'How can I save money when my income is small and irregular?',fr:'Comment puis-je économiser quand mon revenu est faible et irrégulier ?',pt:'Como posso poupar dinheiro quando o meu rendimento é pequeno e irregular?',ar:'كيف أدخر المال عندما يكون دخلي قليلاً وغير منتظم؟',sw:'Ninawezaje kuweka akiba wakati kipato changu ni kidogo na si cha kawaida?',ha:'Ta yaya zan iya ajiye kuɗi idan kuɗin shigata kaɗan ne kuma ba na yau da kullum ba?',yo:'Báwo ni mo ṣe lè fi owó pamọ́ nígbà tí owó tí mo ń wọlé kò pọ̀?',ig:'Kedu ka m ga-esi chekwaa ego mgbe ego m na-enweta dị ntakịrị?'};
let thread=null;
for(const L of Object.keys(Q)){
  const o=out[L]={};
  if(L!=='en'){const tr=await post('mentor-chat',{action:'translate',texts:[EN],language:L}); o.translate={status:tr.status,ms:tr.ms,text:(tr.j.translations||[])[0],err:tr.j.error,tried:tr.j.tried};}
  const c=await post('mentor-chat',{message:Q[L],language:L,mode:'voice'}); o.chat={status:c.status,ms:c.ms,reply:c.j.reply,engine:c.j.engine,model:c.j.model,err:c.j.error};
  const text=(c.j.reply||o.translate&&o.translate.text||EN).replace(/[*#_]/g,'').slice(0,230);
  const v=await post('mentor-voice',{action:'speak',text,language:L}); o.voice={status:v.status,ms:v.ms,engine:v.j.engine,model:v.j.model,mime:v.j.mime,err:v.j.error,tried:v.j.tried,text};
  if(v.j.audio) fs.writeFileSync('res/live_'+L+'.mp3',Buffer.from(v.j.audio,'base64'));
}
fs.writeFileSync('res/results.json',JSON.stringify(out,null,1));
