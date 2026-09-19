// Service worker do SigRouter.
// Guarda os arquivos na primeira visita para o app abrir offline depois.
// A versao no nome do cache dispara a atualizacao: ao publicar, incremente o numero.
// IMPORTANTE: incremente SEMPRE que o index.html mudar — inclusive quando so o
// template do script embutido mudar. Sem isso, quem tem o app instalado continua
// gerando .gpc de uma versao antiga.
const CACHE = 'sigrouter-v30';

// Separados de proposito: sem o index e o manifest o app nao abre; sem os icones ele
// abre normalmente. Um icone faltando nao pode impedir a instalacao inteira, que era
// o que acontecia com um addAll unico — ele falha em bloco se QUALQUER item falhar.
const CRITICOS = ['./index.html', './manifest.json'];
const OPCIONAIS = ['./icone-192.png', './icone-512.png', './icone-maskable.png'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(async c => {
      await c.addAll(CRITICOS);
      await Promise.all(OPCIONAIS.map(u => c.add(u).catch(() => {})));
    }).then(() => self.skipWaiting())
  );
});

// Sem isto, um service worker novo fica em espera ate TODAS as abas do app fecharem —
// e no PWA instalado isso pode nunca acontecer. O botao Atualizar manda esta mensagem.
self.addEventListener('message', e => {
  if (e.data === 'assumir') self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Rede primeiro, cache como reserva: uma versao nova chega assim que houver internet,
// e a falta dela nunca impede de abrir.
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith((async () => {
    try {
      const r = await fetch(e.request);
      // So guarda o que e NOSSO e veio bem. Sem a checagem de origem, qualquer recurso
      // de terceiros entraria no cache e ele cresceria sem controle; sem o r.ok, um 404
      // momentaneo viraria a pagina que o app serve offline.
      const url = new URL(e.request.url);
      if (url.origin === self.location.origin && r && r.ok) {
        const cache = await caches.open(CACHE);
        await cache.put(e.request, r.clone());
      }
      return r;
    } catch (err) {
      const achou = await caches.match(e.request);
      if (achou) return achou;
      // Só devolve o index para uma NAVEGACAO. Para um recurso que falta, devolver a
      // pagina inteira mascara o problema e confunde o diagnostico.
      if (e.request.mode === 'navigate') return await caches.match('./index.html');
      return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
    }
  })());
});
