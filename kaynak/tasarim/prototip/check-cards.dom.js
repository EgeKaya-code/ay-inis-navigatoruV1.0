// check-cards.mjs için: brifing açıkken tarayıcıda çalışır, dört sıralamada kartlarda yazan metni toplar.
(() => {
  const out = {};
  for (const b of [...document.querySelectorAll('#sortBar button')]) {
    document.querySelector(`#sortBar button[data-v="${b.dataset.v}"]`).click();
    out[b.dataset.v] = [...document.querySelectorAll('#cards .card')].map((c) => {
      const pair = (cls) => ['best', 'med'].map((f) => { const el = c.querySelector(`.${cls} [data-f="${f}"]`); return el ? el.textContent.trim() : null; });
      return { id: c.dataset.id, sun: pair('met-sun'), earth: pair('met-earth'), dark: pair('met-dark') };
    });
  }
  document.querySelector('#sortBar button[data-v="power"]').click();
  return JSON.stringify(out);
})()
