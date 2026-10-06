// Confere NOME ACESSIVEL e ALVO DE TOQUE no app renderizado no Chromium.
//
// POR QUE NO NAVEGADOR E NAO NO FONTE: nome acessivel nao e o texto do rotulo, e o que a
// arvore de acessibilidade calcula — aria-label vence aria-labelledby, que vence o texto,
// e controle dentro de <div> pode nao herdar rotulo nenhum. Era exatamente o caso do
// <select> da cor do LED: o rotulo ia para o grupo e o leitor anunciava so o valor.
//
// O ALVO DE TOQUE e medido em 24x24, que e o minimo da WCAG 2.5.8 (AA). Os 44 px da
// 2.5.5 (AAA) e das diretrizes de plataforma sao a META, aplicada onde custa pouco: o
// botao de voltar e as setas de reordenar. Grade densa de 17 botoes nao vale reflow.
//
// uso: node testa_a11y.js <index.html> <biblioteca.json>
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [APP, LIB] = process.argv.slice(2);
  const html = fs.readFileSync(APP,'utf8'), lib = fs.readFileSync(LIB,'utf8');
  const b = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined });
  const p = await b.newPage({ viewport:{width:412,height:900} });
  const U='https://cdanv.github.io/D-Sig/';
  await p.route(U, r=>r.fulfill({contentType:'text/html; charset=utf-8', body:html}));
  await p.goto(U,{waitUntil:'domcontentloaded'});
  await p.evaluate(l=>localStorage.setItem('dsig',l), lib);
  await p.reload({waitUntil:'load'});
  let ok = true;
  const diz=(n,b2,d)=>{ if(!b2) ok=false; console.log(`  [${b2?'ok ':'FALHOU'}] ${n}${d?'   '+d:''}`) };

  async function varre(rot){
    return await p.evaluate(() => {
      const sem=[], peq=[];
      document.querySelectorAll('select,input,textarea,button').forEach(e=>{
        if(e.offsetParent===null) return;                 // invisivel nao conta
        const al=e.getAttribute('aria-label');
        const lb=e.getAttribute('aria-labelledby');
        // O textContent de um <select> sao as opcoes, e de um <input> e vazio: nenhum
        // dos dois e nome acessivel. Texto proprio so conta para <button>.
        const txt=(e.tagName==='BUTTON'?(e.textContent||''):'').trim();
        const nome = al || (lb && (document.getElementById(lb)||{}).textContent) || txt;
        if(!nome || !nome.trim()) sem.push(e.tagName+'.'+(e.className||'')+' "'+txt.slice(0,12)+'"');
        const r=e.getBoundingClientRect();
        if(r.width<24 || r.height<24) peq.push(`${e.tagName}${e.className?'.'+e.className:''} ${Math.round(r.width)}x${Math.round(r.height)} "${txt.slice(0,10)}"`);
      });
      return {sem, peq};
    });
  }

  // tela de jogos
  let r = await varre('cat');
  diz('lista de jogos: todo controle tem nome acessivel', r.sem.length===0, r.sem.join(' | ')||'');
  diz('lista de jogos: alvos de toque >= 24x24 (minimo AA)', r.peq.length===0, r.peq.join(' | ')||'');

  // tela do jogo
  //
  // O JOGO E O MOD SAO ESCOLHIDOS PELO CONTEUDO, nao por nome nem por indice. Antes isto
  // era findIndex(x=>x.nome==='Mad Max') e md=6: o teste estava amarrado ao molde que
  // veio da biblioteca pessoal do Daniel, e trocar o molde o derrubava com
  // "Cannot read properties of undefined". Teste que depende do NOME do dado nao testa o
  // app, testa o dado. Agora pega o primeiro jogo e, dentro dele, o MOD com mais campos
  // de GAMA preenchidos — que e o que esta tela precisa para ter o que varrer.
  const alvo = await p.evaluate(()=>{
    window.tela='jogo'; window.jg=0; window.render();
    const ms=window.D.jogos[0].mods;
    let melhor=0, pontos=-1;
    ms.forEach((m,i)=>{
      const n=(m.g2clk?1:0)+(m.gTog?1:0)+(m.gHold?1:0)+(m.gAfter?1:0)+(m.gBlok?1:0);
      if(n>pontos){pontos=n;melhor=i}
    });
    return {jogo:window.D.jogos[0].nome, mod:melhor+1, gama:pontos};
  });
  r = await varre('jogo');
  diz('tela do jogo: todo controle tem nome acessivel', r.sem.length===0, r.sem.join(' | ')||'');
  diz('tela do jogo: alvos de toque >= 24x24 (minimo AA)', r.peq.length===0, r.peq.join(' | ')||'');
  if(alvo.gama < 2){
    diz('o molde tem um MOD com GAMA cheio para varrer', false,
        `o melhor tem ${alvo.gama} campo(s) de GAMA; a tela do MOD nao prova nada assim`);
  }

  // tela do MOD com GAMA cheio
  await p.evaluate(i=>{ window.tela='mod'; window.md=i; window.render() }, alvo.mod-1);
  r = await varre('mod');
  diz('tela do MOD: todo controle tem nome acessivel', r.sem.length===0, r.sem.join(' | ')||'');
  diz('tela do MOD: alvos de toque >= 24x24 (minimo AA)', r.peq.length===0, r.peq.join(' | ')||'');

  // os sub-campos do GAMA dizem de quem sao
  const subs = await p.evaluate(()=>{
    const out=[];
    document.querySelectorAll('.gg').forEach(g=>{
      const fs=[...g.querySelectorAll('.fld')];
      fs.slice(1).forEach(f=>{
        const c=f.querySelector('select,input,button');
        out.push({rot:f.querySelector('label').textContent.trim(), acc:c?c.getAttribute('aria-label'):null});
      });
    });
    return out;
  });
  const semPai = subs.filter(x=>!x.acc || !/^(2CLK|TOGGLE|HOLD|AFTER|BLOK)/.test(x.acc));
  diz(`os ${subs.length} sub-campos do GAMA dizem a que alternativa pertencem`,
      semPai.length===0, semPai.length?JSON.stringify(semPai.slice(0,3)):subs.slice(0,2).map(x=>`"${x.acc}"`).join(', '));

  // tela de dados
  await p.evaluate(()=>{ window.tela='dados'; window.render() });
  r = await varre('dados');
  diz('tela de dados: todo controle tem nome acessivel', r.sem.length===0, r.sem.join(' | ')||'');

  await b.close();
  process.exit(ok?0:1);
})();
