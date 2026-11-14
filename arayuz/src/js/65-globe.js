// ===== globe: açılış ekranı — dönen, sürüklenebilir Ay; güney kutbunda 9 Artemis III bölgesi =====
// Ay kendi ekseninde yavaşça döner (Güneş sabit: dönüş = hızlandırılmış Ay günü, ışık o tarihe göredir).
// Fare kameranın Ay çevresindeki yerini değiştirir (Ay'ın aydınlık evresi de böylece döner).
// Küre dokusu: genel görünüm için three.js örnek dokusu; 80°G'nin güneyi kendi LOLA kabartma haritamız
// (polar_map.png) ve USGS bölge sınırları, aynı stereografik izdüşümle.
// Bir noktaya tıklanınca kamera yavaşça o noktanın ~130 km üstüne iner; ardından kokpitin iniş sekansı sürer.
const Globe = (() => {
  const R_KM = 1737.4, PS_HALF = 304;
  const SYNODIC_D = 29.530588853, NEW_MOON_MS = Date.UTC(2000, 0, 6, 18, 14); // ışık yönü için yaklaşık evre
  const SUN_LON_W = 90;            // Güneş'in dünya çerçevesindeki boylamı: (1, 0, 0) yönü
  const SPIN_H_PER_S = 12;         // hızlandırılmış zaman: 1 sn = 12 saat → bir Ay günü ≈ 59 sn
  // poz: kamera yönü (az, el) ve merkeze uzaklığı; bakılan nokta (tx, ty, tz)
  const OVERVIEW = { az: 205, el: -46, dist: 4.9, tx: 0, ty: 0, tz: 0, fov: 30 };
  const POLE = { az: 205, el: -80, dist: 1.4, tx: 0, ty: -0.97, tz: 0, fov: 30 };
  const END_ALT = 0.075;           // inişin bittiği yükseklik (R biriminde) ≈ 130 km
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;

  let ok = false, cv, renderer, scene, camera, moon, mat, stars;
  const pose = Object.assign({}, OVERVIEW);
  let lightH = 0, spinK = reduced ? 0 : 1, spinGoal = spinK, paused = false;
  let tween = null, path = null, saved = null, flying = false, hold = false;
  const vel = { az: 0, el: 0 };
  let W = 1, H = 1, shift = 0, shiftGoal = 0, touched = false; // shift: sunumda Ay'ı sağa kaydırır (metne yer açılır)
  const cb = {};
  const _v = new THREE.Vector3(), _w = new THREE.Vector3();

  // ---------- küre ----------
  const VS = `varying vec3 vP;
void main(){ vP = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;
  const FS = `precision highp float;
uniform sampler2D uMap, uPolar, uOver, uNorm;
uniform vec3 uSun, uCam;
uniform float uHasMap, uHasPolar, uBump, uOverK, uShine, uCapK, uHasNorm, uNormK;
varying vec3 vP;
const float PI = 3.141592653589793;
const float RK = ${R_KM.toFixed(1)};
float lum(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }
void main(){
  vec3 n = normalize(vP);
  float lat = asin(clamp(n.y, -1.0, 1.0));
  float lon = atan(n.x, n.z);
  vec2 uv = vec2(0.5 + lon / (2.0 * PI), 0.5 + lat / PI);
  // 180. boylamdaki dikiş: iki uv'nin türevlerinden küçüğünü kullan
  vec2 uvB = vec2(fract(uv.x + 0.5), uv.y);
  vec2 dxA = dFdx(uv), dyA = dFdy(uv), dxB = dFdx(uvB), dyB = dFdy(uvB);
  // genel dokunun kutba yakın satırları gerilmiş (çizgili): 66°G'nin güneyinde yumuşat, kabartmayı söndür
  float polarBlur = smoothstep(-1.15, -1.45, lat);
  float blurK = uHasNorm > 0.5 ? 1.5 : 7.0; // NASA haritası kutba yakın daha temiz: az yumuşatma yeter
  vec2 dx = (abs(dxA.x) <= abs(dxB.x) ? dxA : dxB) * (1.0 + blurK * polarBlur);
  vec2 dy = (abs(dyA.x) <= abs(dyB.x) ? dyA : dyB) * (1.0 + blurK * polarBlur);
  vec3 base = uHasMap > 0.5 ? textureGrad(uMap, uv, dx, dy).rgb : vec3(0.52);
  vec2 du = vec2(1.0 / 1024.0, 0.0), dv = vec2(0.0, 1.0 / 512.0);
  float hE = lum(textureGrad(uMap, uv + du, dx, dy).rgb) - lum(textureGrad(uMap, uv - du, dx, dy).rgb);
  float hN = lum(textureGrad(uMap, uv + dv, dx, dy).rgb) - lum(textureGrad(uMap, uv - dv, dx, dy).rgb);
  // güney kutbu: stereografik izdüşüm (x = r sin λ, y = r cos λ; km), LOLA kabartma haritası ±304 km
  float r = 2.0 * RK * tan((PI * 0.5 + lat) * 0.5);
  vec2 xy = vec2(r * sin(lon), r * cos(lon));
  vec2 puv = clamp(xy / ${(2 * PS_HALF).toFixed(1)} + 0.5, 0.0, 1.0);
  float inCap = 1.0 - step(0.0, lat);
  float edge = max(abs(xy.x), abs(xy.y));
  float w = uHasPolar * inCap * (1.0 - smoothstep(236.0, 300.0, edge));
  float pg = texture(uPolar, puv).r;
  vec3 pcol = vec3(0.10 + 0.86 * pg);
  vec3 alb = mix(base, pcol, w);
  float bump = uBump * (1.0 - w) * uHasMap * (1.0 - polarBlur);
  vec3 east = vec3(cos(lon), 0.0, -sin(lon));
  vec3 north = vec3(-sin(lat) * sin(lon), cos(lat), -sin(lat) * cos(lon));
  vec3 nb = normalize(n - bump * (hE * east + hN * north));
  if (uHasNorm > 0.5) {
    // NASA LOLA yükseklik haritasından üretilmiş kabartma (doğu, kuzey, yukarı)
    vec3 tn = textureGrad(uNorm, uv, dx, dy).rgb * 2.0 - 1.0;
    tn.xy *= uNormK * (1.0 - w);
    nb = normalize(east * tn.x + north * tn.y + n * tn.z);
  }
  // aydınlatma: Lambert + Lommel–Seeliger karışımı (Ay diski kenara doğru kararmaz)
  float g = dot(n, uSun);
  float mu0 = max(dot(nb, uSun), 0.0);
  float mu = max(dot(n, normalize(uCam - vP)), 0.0);
  float ls = 2.0 * mu0 / (mu0 + mu + 1e-3);
  float shade = (0.32 * mu0 + 0.68 * ls) * smoothstep(-0.012, 0.045, g);
  // Kutupta Güneş hep ufukta olduğu için düz bir kürede kutup kapağı karanlık kalır; gerçek arazideki tepeleri
  // ise küre bilmez. Yaklaştıkça kapak harita gibi okunur: LOLA kabartması, Güneş tarafı daha aydınlık.
  float capLight = 0.40 + 0.62 * smoothstep(-0.14, 0.14, g);
  shade = mix(shade, capLight, uCapK * max(w, smoothstep(-1.25, -1.43, lat)));
  vec3 col = alb * (1.18 * shade) + alb * uShine * vec3(0.72, 0.82, 1.0);
  // bölge sınırları ve enlem halkaları (ışıktan bağımsız; ince çizgi, yaklaştıkça belirir)
  vec4 ov = texture(uOver, puv) * inCap * (1.0 - smoothstep(292.0, 304.0, edge));
  col = mix(col, ov.rgb, ov.a * uOverK);
  gl_FragColor = vec4(pow(col, vec3(0.92)), 1.0);
}`;

  // bölge poligonları + 84°/86°/88° G halkaları, kutup haritasıyla aynı izdüşümde (2048² saydam doku)
  function overlayCanvas(index) {
    const N = 2048, c = document.createElement('canvas');
    c.width = c.height = N;
    const g = c.getContext('2d');
    const px = (x) => ((x + PS_HALF) / (2 * PS_HALF)) * N, py = (y) => ((PS_HALF - y) / (2 * PS_HALF)) * N;
    const latR = (lat) => 2 * R_KM * Math.tan(((90 - Math.abs(lat)) / 2) * D2R);
    g.lineWidth = 2; g.strokeStyle = 'rgba(201,210,205,0.35)'; g.setLineDash([10, 12]);
    for (const lat of [84, 86, 88]) { g.beginPath(); g.arc(px(0), py(0), (latR(lat) / (2 * PS_HALF)) * N, 0, Math.PI * 2); g.stroke(); }
    g.setLineDash([]);
    g.beginPath(); g.moveTo(px(-6), py(0)); g.lineTo(px(6), py(0)); g.moveTo(px(0), py(-6)); g.lineTo(px(0), py(6)); g.stroke();
    g.lineWidth = 2.6; g.strokeStyle = 'rgba(238,242,238,0.88)'; g.lineJoin = 'round';
    for (const s of index.sites) {
      const poly = s.reg && s.reg.polygon_ps_km;
      if (!poly) continue;
      g.beginPath();
      poly.forEach(([x, y], i) => (i ? g.lineTo(px(x), py(y)) : g.moveTo(px(x), py(y))));
      g.closePath(); g.stroke();
    }
    return c;
  }

  function makeStars() {
    const n = 2200, pos = new Float32Array(n * 3), col = new Float32Array(n * 3);
    let seed = 7;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    for (let i = 0; i < n; i++) {
      const u = rnd() * 2 - 1, a = rnd() * Math.PI * 2, s = Math.sqrt(1 - u * u);
      pos.set([90 * s * Math.cos(a), 90 * u, 90 * s * Math.sin(a)], i * 3);
      const b = 0.18 + 0.82 * Math.pow(rnd(), 3.2);
      col.set([b * 0.96, b * 0.98, b], i * 3);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    return new THREE.Points(geo, new THREE.PointsMaterial({ size: 1.5, sizeAttenuation: false, vertexColors: true, depthWrite: false }));
  }

  function init(canvas, index, callbacks) {
    cv = canvas; Object.assign(cb, callbacks || {});
    if (typeof THREE === 'undefined') return false;
    try {
      renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, powerPreference: 'high-performance' });
    } catch (e) { console.warn('küre: WebGL yok', e); return false; }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0x000000, 1);
    renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(OVERVIEW.fov, 1, 0.002, 400);

    const blank = new THREE.DataTexture(new Uint8Array([133, 133, 133, 255]), 1, 1); blank.needsUpdate = true;
    const over = new THREE.CanvasTexture(overlayCanvas(index));
    over.anisotropy = 4;
    let polar = blank;
    if (index.map && index.map.image) { polar = new THREE.Texture(index.map.image); polar.needsUpdate = true; polar.anisotropy = 4; }
    mat = new THREE.ShaderMaterial({
      vertexShader: VS, fragmentShader: renderer.capabilities.isWebGL2 ? FS : '#define textureGrad(s, u, a, b) texture2D(s, u)\n' + FS,
      uniforms: {
        uMap: { value: blank }, uPolar: { value: polar }, uOver: { value: over },
        uSun: { value: new THREE.Vector3(1, 0, 0) }, uCam: { value: new THREE.Vector3() },
        uNorm: { value: blank }, uHasNorm: { value: 0 }, uNormK: { value: 1.0 },
        uHasMap: { value: 0 }, uHasPolar: { value: polar === blank ? 0 : 1 }, uBump: { value: 0.55 }, uOverK: { value: 0.85 }, uShine: { value: 0.016 }, uCapK: { value: 0 },
      },
    });
    mat.extensions = { derivatives: true };
    // Doku: NASA SVS CGI Moon Kit (LROC renk + LOLA yükseklik, 4096×2048); yoksa küçük yedek doku
    const loader = new THREE.TextureLoader(), maxTex = renderer.capabilities.maxTextureSize;
    const useMap = (tx) => { tx.anisotropy = 8; tx.wrapS = THREE.RepeatWrapping; mat.uniforms.uMap.value = tx; mat.uniforms.uHasMap.value = 1; };
    const fallback = () => loader.load('vendor/moon_1024.jpg', useMap, undefined, () => console.warn('küre: Ay dokusu yüklenemedi; düz gri kullanılıyor'));
    if (maxTex >= 4096) {
      loader.load('vendor/moon_4k.jpg', useMap, undefined, fallback);
      loader.load('vendor/moon_normal_4k.jpg', (tx) => {
        tx.anisotropy = 8; tx.wrapS = THREE.RepeatWrapping;
        mat.uniforms.uNorm.value = tx; mat.uniforms.uHasNorm.value = 1;
      }, undefined, () => console.warn('küre: kabartma haritası yok (vendor/moon_normal_4k.jpg)'));
    } else fallback();
    moon = new THREE.Mesh(new THREE.SphereGeometry(1, 256, 160), mat);
    scene.add(moon);
    stars = makeStars();
    scene.add(stars);
    bindInput();
    new ResizeObserver(resize).observe(cv);
    resize();
    ok = true;
    return true;
  }

  function resize() {
    if (!renderer) return;
    const r = cv.getBoundingClientRect();
    W = Math.max(1, r.width); H = Math.max(1, r.height);
    renderer.setSize(W, H, false);
    camera.aspect = W / H;
    camera.updateProjectionMatrix();
    // dikey ekranda (telefon) Ay'ın tamamı sığsın: kamera uzaklaşır
    const a = W / H;
    OVERVIEW.dist = a < 1 ? 1 + (3.9 / Math.max(0.42, a)) * 0.92 : 4.9;
    POLE.dist = a < 1 ? 1 + 0.4 / Math.max(0.42, a) : 1.4;
    if (!touched) pose.dist = OVERVIEW.dist;
  }

  // ---------- zaman ve ışık ----------
  const subsolarLon = (ms) => { const f = ((((ms - NEW_MOON_MS) / 86400e3 / SYNODIC_D) % 1) + 1) % 1; return 180 - 360 * f; };
  function applyLight() {
    const ls = subsolarLon(Fmt.hourToDate(lightH).getTime());
    moon.rotation.y = (SUN_LON_W - ls) * D2R; // Güneş dünya çerçevesinde sabit; Ay döner
  }
  function setLightHour(h) { lightH = h; if (ok) applyLight(); }

  // ---------- kamera ----------
  const dirOf = (az, el) => _w.set(Math.cos(el * D2R) * Math.sin(az * D2R), Math.sin(el * D2R), Math.cos(el * D2R) * Math.cos(az * D2R));
  function camOf(p) {
    const pos = dirOf(p.az, p.el).clone().multiplyScalar(p.dist);
    return { pos, target: new THREE.Vector3(p.tx || 0, p.ty, p.tz || 0), up: new THREE.Vector3(0, 1, 0), fov: p.fov };
  }
  function place(c) {
    camera.position.copy(c.pos);
    camera.up.copy(c.up);
    camera.lookAt(c.target);
    if (Math.abs(camera.fov - c.fov) > 1e-3) { camera.fov = c.fov; camera.updateProjectionMatrix(); }
  }
  const wrapAz = (d) => ((d + 540) % 360) - 180;

  function flyTo(to, ms = 1600) {
    if (!ok) return Promise.resolve();
    path = null; touched = true;
    const from = Object.assign({}, pose);
    return new Promise((res) => { tween = { from, to: Object.assign({}, pose, to), t0: performance.now(), ms: reduced ? Math.min(ms, 400) : ms, res }; });
  }
  // bir noktanın üstünden ona bakan poz (sunum için): kamera noktanın biraz ekvator yanında, dist yüksekliğinde
  function poseAbove(site, dist = 1.25, tilt = 6) {
    const P = moon.localToWorld(vecOf(site).clone());
    const el = Math.asin(clamp(P.y, -1, 1)) / D2R, az = Math.atan2(P.x, P.z) / D2R;
    return { az, el: clamp(el + tilt, -86, 86), dist, tx: P.x, ty: P.y, tz: P.z, fov: 30 };
  }

  // ---------- noktalar ----------
  const vecCache = new Map();
  function vecOf(site) {
    if (!vecCache.has(site.id)) {
      const la = site.lat * D2R, lo = site.lon * D2R;
      vecCache.set(site.id, new THREE.Vector3(Math.cos(la) * Math.sin(lo), Math.sin(la), Math.cos(la) * Math.cos(lo)));
    }
    return vecCache.get(site.id);
  }
  const POLE_V = new THREE.Vector3(0, -1, 0);
  // nesne çerçevesindeki bir yüzey noktasının ekrandaki yeri; front: kameraya bakan yüzde mi
  function project(v) {
    _v.copy(v).multiplyScalar(1.0008);
    moon.localToWorld(_v);
    _w.copy(_v).normalize();
    const facing = _w.dot(_v.clone().sub(camera.position).negate().normalize());
    _v.project(camera);
    return { x: (_v.x * 0.5 + 0.5) * W, y: (-_v.y * 0.5 + 0.5) * H, front: facing > 0.02 && _v.z < 1, facing };
  }
  const projectSite = (site) => project(vecOf(site));
  const projectPole = () => project(POLE_V);
  // dünya çerçevesindeki bir yönün ekrandaki yeri (Güneş ve Dünya yön işaretleri için)
  function projectDir(dir) {
    _v.copy(camera.position).addScaledVector(dir, 60).project(camera);
    const behind = _v.z > 1;
    let x = _v.x, y = _v.y;
    if (behind) { x = -x; y = -y; }
    return { x: (x * 0.5 + 0.5) * W, y: (-y * 0.5 + 0.5) * H, inside: !behind && Math.abs(x) < 1 && Math.abs(y) < 1 };
  }
  const SUN_W = new THREE.Vector3(1, 0, 0);
  const sunScreen = () => projectDir(SUN_W);
  // Dünya: Ay'ın yakın yüzünün merkezi (0°, 0°) yönünde (librasyon yok sayıldı)
  const earthScreen = () => projectDir(new THREE.Vector3(0, 0, 1).applyQuaternion(moon.quaternion));
  // kameranın Ay yüzeyinden yüksekliği (km) ve görüş açısına göre ekrandaki km/px
  const altitudeKm = () => (camera.position.length() - 1) * R_KM;

  // ---------- giriş ----------
  function bindInput() {
    let drag = null;
    cv.addEventListener('pointerdown', (e) => {
      if (flying || e.button > 0) return;
      cv.setPointerCapture(e.pointerId);
      drag = { x: e.clientX, y: e.clientY, t: performance.now() };
      vel.az = vel.el = 0;
      tween = null; touched = true;
      cv.classList.add('dragging');
    });
    cv.addEventListener('pointermove', (e) => {
      if (!drag) return;
      const dx = e.clientX - drag.x, dy = e.clientY - drag.y, now = performance.now(), dt = Math.max(1, now - drag.t);
      drag.x = e.clientX; drag.y = e.clientY; drag.t = now;
      const k = (camera.fov / H) * Math.max(0.12, Math.min(1, (pose.dist - 1) / 2.4)) * 1.6; // yakındayken yavaş
      pose.az -= dx * k; pose.el = clamp(pose.el + dy * k, -86, 86);
      vel.az = (-dx * k) / dt * 16; vel.el = (dy * k) / dt * 16;
      if (cb.onUser) cb.onUser();
    });
    const end = () => { drag = null; cv.classList.remove('dragging'); };
    cv.addEventListener('pointerup', end); cv.addEventListener('pointercancel', end);
    cv.addEventListener('wheel', (e) => {
      e.preventDefault();
      if (flying) return;
      tween = null; touched = true;
      pose.dist = clamp(1 + (pose.dist - 1) * Math.exp(e.deltaY * 0.0012), 1.12, 6.5);
      // yaklaştıkça bakış kutba kayar (kutup ekranın ortasına gelsin)
      pose.ty = lerp(pose.ty, smooth(3.2, 1.5, pose.dist) * -0.95, 0.25);
      pose.tx = lerp(pose.tx || 0, 0, 0.25); pose.tz = lerp(pose.tz || 0, 0, 0.25);
      if (cb.onUser) cb.onUser();
    }, { passive: false });
  }

  // ---------- iniş yaklaşması ----------
  // kamera noktanın ~130 km üstüne, biraz kuzeyinden noktaya bakarak iner; Ay bu sırada durur
  function approach(site, ms = 6200) {
    if (!ok) return Promise.resolve();
    tween = null; vel.az = vel.el = 0;
    spinGoal = 0;
    saved = Object.assign({}, pose);
    const v = vecOf(site), la = site.lat * D2R, lo = site.lon * D2R;
    const P = moon.localToWorld(v.clone());
    const radial = P.clone().normalize();
    const north = new THREE.Vector3(-Math.sin(la) * Math.sin(lo), Math.cos(la), -Math.sin(la) * Math.cos(lo)).applyQuaternion(moon.quaternion);
    const c0 = camOf(pose);
    const r0 = c0.pos.length(), d0 = c0.pos.clone().normalize();
    const endPos = P.clone().multiplyScalar(1 + END_ALT).addScaledVector(north, 0.05);
    const rE = endPos.length(), dE = endPos.clone().normalize();
    const omega = Math.acos(clamp(d0.dot(dE), -1, 1));
    const slerp = (a) => {
      if (omega < 1e-4) return dE.clone();
      const s = Math.sin(omega);
      return d0.clone().multiplyScalar(Math.sin((1 - a) * omega) / s).addScaledVector(dE, Math.sin(a * omega) / s);
    };
    const fn = (k) => {
      const a = easeInOut(smooth(0, 0.82, k)), b = easeInOut(smooth(0.12, 1, k));
      const pos = slerp(a).multiplyScalar(lerp(r0, rE, b));
      const target = c0.target.clone().lerp(P, easeInOut(smooth(0.05, 0.75, k)));
      const up = c0.up.clone().lerp(radial, smooth(0.45, 1, k)).normalize();
      return { pos, target, up, fov: lerp(c0.fov, 42, smooth(0.5, 1, k)) };
    };
    flying = true; hold = false;
    return new Promise((res) => {
      path = { fn, t0: performance.now(), ms: reduced ? 1200 : ms, res: () => { hold = true; res(true); }, abort: () => res(false) };
    });
  }

  // kokpitten dönüş: inişin bittiği yerden önceki görünüme geri çık
  function depart(ms = 2600) {
    if (!ok || !saved) return Promise.resolve();
    const last = path && path.last;
    const to = camOf(saved);
    const from = last || { pos: to.pos.clone().multiplyScalar(0.3).setLength(1 + END_ALT), target: new THREE.Vector3(), up: new THREE.Vector3(0, 1, 0), fov: 42 };
    const r0 = from.pos.length(), d0 = from.pos.clone().normalize(), rE = to.pos.length(), dE = to.pos.clone().normalize();
    const omega = Math.acos(clamp(d0.dot(dE), -1, 1));
    const fn = (k) => {
      const a = easeInOut(k), s = Math.sin(omega);
      const dir = omega < 1e-4 ? dE.clone() : d0.clone().multiplyScalar(Math.sin((1 - a) * omega) / s).addScaledVector(dE, Math.sin(a * omega) / s);
      return { pos: dir.multiplyScalar(lerp(r0, rE, easeInOut(smooth(0, 0.8, k)))), target: from.target.clone().lerp(to.target, a), up: from.up.clone().lerp(to.up, a).normalize(), fov: lerp(from.fov, to.fov, a) };
    };
    flying = true; hold = false;
    const back = saved;
    return new Promise((res) => {
      path = { fn, t0: performance.now(), ms: reduced ? 500 : ms, res: () => { Object.assign(pose, back); saved = null; if (!paused) spinGoal = 1; res(); } };
    });
  }

  // yaklaşma sürerken vazgeç: olduğu yerden geri çık (approach sözü false ile çözülür)
  function cancel() {
    if (!path || !path.fn || !saved || !path.abort) return Promise.resolve();
    const abort = path.abort, cur = path.last;
    path = { last: cur }; flying = false;
    abort();
    return depart(1500);
  }

  // ---------- her kare ----------
  function render(dt) {
    if (!ok) return;
    // hızlandırılmış Ay günü
    spinK += clamp(spinGoal - spinK, -dt * 1.2, dt * 1.2);
    // yaklaştıkça dönüş durur: kutup görünümünde işaretler yerinde kalsın, tıklamak kolay olsun
    const near = camera ? smooth(1.7, 3.4, camera.position.length()) : 1;
    if (spinK * near > 0.001) { lightH += dt * SPIN_H_PER_S * spinK * near; applyLight(); if (cb.onLight) cb.onLight(lightH); }
    let c;
    if (path && path.fn) {
      const k = clamp((performance.now() - path.t0) / path.ms, 0, 1);
      c = path.fn(k);
      path.last = c;
      if (k >= 1) { const r = path.res; flying = false; path = { last: c }; if (r) r(); }
    } else {
      if (tween) {
        const k = clamp((performance.now() - tween.t0) / tween.ms, 0, 1), e = easeInOut(k), a = tween.from, b = tween.to;
        pose.az = a.az + wrapAz(b.az - a.az) * e; pose.el = lerp(a.el, b.el, e); pose.dist = lerp(a.dist, b.dist, e);
        pose.tx = lerp(a.tx || 0, b.tx || 0, e); pose.ty = lerp(a.ty, b.ty, e); pose.tz = lerp(a.tz || 0, b.tz || 0, e); pose.fov = lerp(a.fov, b.fov, e);
        if (k >= 1) { const r = tween.res; tween = null; r(); }
      } else if (Math.abs(vel.az) + Math.abs(vel.el) > 1e-4) {
        pose.az += vel.az; pose.el = clamp(pose.el + vel.el, -86, 86);
        const f = Math.exp(-dt * 3.2); vel.az *= f; vel.el *= f;
      }
      c = hold && path && path.last ? path.last : camOf(pose);
    }
    shift += (shiftGoal - shift) * Math.min(1, dt * 3);
    if (Math.abs(shift) > 1e-4) camera.setViewOffset(W, H, -shift * W, 0, W, H); else if (camera.view && camera.view.enabled) camera.clearViewOffset();
    place(c);
    mat.uniforms.uCam.value.copy(moon.worldToLocal(camera.position.clone()));
    mat.uniforms.uSun.value.copy(SUN_W).applyQuaternion(moon.quaternion.clone().invert());
    // sınır çizgileri uzaktan gürültü olmasın: yaklaştıkça belirir
    const cd = camera.position.length();
    mat.uniforms.uOverK.value = 0.25 + 0.65 * smooth(3.6, 1.8, cd);
    mat.uniforms.uCapK.value = smooth(3.0, 1.7, cd);
    stars.position.copy(camera.position);
    renderer.render(scene, camera);
  }

  function setShift(f) { shiftGoal = f; }
  function setSpin(on) { paused = !on; if (!flying && !saved) spinGoal = on ? 1 : 0; }

  return {
    init, render, flyTo, approach, depart, cancel, setLightHour, setSpin, setShift, project, projectSite, projectPole,
    sunScreen, earthScreen, altitudeKm, poseAbove, resize, OVERVIEW, POLE,
    get ok() { return ok; }, get flying() { return flying; }, get lightH() { return lightH; }, get paused() { return paused; },
    get dist() { return camera ? camera.position.length() : 4; }, get pose() { return pose; }, get landedFrom() { return saved; },
  };
})();
