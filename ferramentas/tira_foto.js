// Fotografa a tela do editor de MOD, para mudança visual ser VISTA e não descrita.
//
// Carrega o index.html de verdade com a biblioteca de verdade, navega até o MOD pedido e
// recorta a seção GAMA. Sem isto eu descreveria a cor em palavras e o Daniel teria de
// gravar, abrir no celular e julgar — três passos para uma coisa que uma imagem resolve.
//
// uso: node tira_foto.js <index.html> <biblioteca.json> <jogo> <mod 1-based> <saida.png>
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const [APP, LIB, JOGO, MOD, SAI] = process.argv.slice(2);
  if (!SAI) { console.error('uso: node tira_foto.js app lib jogo mod saida.png'); process.exit(2); }

  const html = fs.readFileSync(APP, 'utf8');
  const lib = fs.readFileSync(LIB, 'utf8');

  const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const pag = await browser.newPage({ viewport: { width: 460, height: 1400 },
                                      deviceScaleFactor: 2 });
  // A biblioteca entra ANTES de qualquer script da página rodar, senão o app abre vazio.
  // setContent roda em about:blank, que e origem OPACA: o localStorage lanca, o try/catch
  // do app engole o erro e ele abre vazio. Interceptar uma URL real resolve a origem.
  const URL_FALSA = 'https://cdanv.github.io/D-Sig/';
  await pag.route(URL_FALSA, r => r.fulfill({ contentType: 'text/html; charset=utf-8', body: html }));
  await pag.goto(URL_FALSA, { waitUntil: 'domcontentloaded' });
  await pag.evaluate(lb => { localStorage.setItem('dsig', lb); }, lib);
  await pag.reload({ waitUntil: 'load' });

  const achou = await pag.evaluate(([nome, md]) => {
    const i = window.D.jogos.findIndex(j => j.nome === nome);
    if (i < 0) return null;
    window.tela = Number(md) > 0 ? 'mod' : 'jogo';
    window.jg = i; window.md = Math.max(0, Number(md) - 1);
    window.render();
    return Number(md) > 0 ? (window.D.jogos[i].mods[Number(md)-1].nota || '(sem nota)') : 'tela do jogo';
  }, [JOGO, MOD]);
  if (achou === null) { console.error('jogo nao encontrado: ' + JOGO); await browser.close(); process.exit(1); }

  // Acha a <section> cujo <h2> diz GAMA e fotografa só ela.
  const SEC = process.env.SECAO || 'GAMA';
  const alvo = await pag.evaluateHandle((sec) => {
    const ss = [...document.querySelectorAll('section')];
    return ss.find(s => s.querySelector('h2') && s.querySelector('h2').textContent.trim() === sec) || null;
  }, SEC);
  const el = alvo.asElement();
  if (!el) { console.error('secao GAMA nao encontrada na tela'); await browser.close(); process.exit(1); }
  await el.screenshot({ path: SAI });
  console.log(`${path.basename(SAI)}: ${JOGO} MOD_${String(MOD).padStart(2, '0')} "${achou}"`);
  await browser.close();
})();
