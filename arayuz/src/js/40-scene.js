// ===== scene: three.js 3D sahne (arazi, ufuk silueti, Güneş, Dünya, araç, kameralar) =====
// Eksenler: veri x=doğu, y=kuzey, z=yukarı  →  three X=doğu, Y=yukarı, Z=−kuzey.
const Scene = (() => {
  const SKY_D = 250000;   // gök cisimlerinin çizildiği uzaklık (m); kamerayla birlikte taşınır
  const RING_R = 30000;   // ufuk silueti halkasının yarıçapı (m)
  const EYE = 2;          // astronot gözü yüksekliği (m), ufuk profiliyle aynı
  const SUN_I = 4.4;      // tam görünen Güneş'in ışık şiddeti
  const FLAT_Y = 0.0006;  // düz ufuk modunda arazinin düşey ölçeği

  let ok = false, renderer, scene, camera, canvas, host;
  let sunLight, earthLight, fillLight, bounce, ambient, sky, sunDisc, sunGlow, earth, earthMat, starMat, trace = null;
  let terrain = null, terrainMat, regoTex = null, flatDisc, ring = null, ringMat, context = null, contextMat;
  let lander, dishPivot, panelPivot, panelMat, beamUp, beamCut, beacon, shadowStrip, sunStreak;
  let tween = null, clock = 0;
  const SH_SEG = 24;
  let grid = null, siteEarthAz = 0;
  let V = null; // geçici vektörler
  const mk = {};
  const st = { sunFrac: 1, sunAlt: 0, earthAlt: 0, illum: 1, linkUp: true, margin: 5, blockKm: 30, flat: 0, flatGoal: 0, shadowDirty: true };
  const cam = { mode: 'orbit', az: 0.6, pol: 1.2, dist: 2600, yaw: 0, pitch: 0.06, fov: 55, cine: null };
  const quality = { acc: 0, frames: 0, lowered: false };
  const api = { onLost: null };

  const dirTo = (altDeg, azDeg, out) => {
    const a = altDeg * D2R, z = azDeg * D2R, c = Math.cos(a);
    return out.set(c * Math.sin(z), Math.sin(a), -c * Math.cos(z));
  };

  // ---------- kurulum ----------
  function init(cv, hostEl) {
    if (typeof THREE === 'undefined') return false;
    canvas = cv; host = hostEl;
    try {
      renderer = new THREE.WebGLRenderer({ canvas: cv, antialias: true, powerPreference: 'high-performance' });
    } catch (e) {
      console.warn('WebGL açılamadı:', e);
      return false;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0x000000, 1);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.0;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.shadowMap.autoUpdate = false;

    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(55, 1, 0.5, 900000);
    V = { sun: new THREE.Vector3(0, 0.02, -1), earth: new THREE.Vector3(0, 0.05, -1), lastSun: new THREE.Vector3(), a: new THREE.Vector3(), b: new THREE.Vector3(),
      c: new THREE.Vector3(), lander: new THREE.Vector3(), dish: new THREE.Vector3(), target: new THREE.Vector3() };

    // hafif dolgu ışığı: tam karanlıkta da arazi seçilsin (Dünya ışığı gibi soğuk)
    ambient = new THREE.AmbientLight(0x93a7c9, 0.14);
    scene.add(ambient);
    // Dünya ışığı: Dünya ufkun üstündeyken araziyi hafifçe aydınlatır (görünürlük için abartılı)
    earthLight = new THREE.DirectionalLight(0x9db8e8, 0);
    scene.add(earthLight, earthLight.target);
    // yapay dolgu ışığı: Güneş yokken kabartma okunabilsin (gerçekte zifiri karanlık); soğuk ve soluk
    fillLight = new THREE.DirectionalLight(0x7f95c0, 0.06);
    fillLight.position.set(30000, 22000, 18000);
    scene.add(fillLight, fillLight.target);
    // zeminden yansıyan ışık: Güneş alçakken aracın gölgede kalan yüzleri simsiyah olmasın
    bounce = new THREE.HemisphereLight(0x000000, 0xb9b0a0, 0);
    scene.add(bounce);
    sunLight = new THREE.DirectionalLight(0xfff7ea, SUN_I);
    sunLight.castShadow = true;
    const ms = Math.min(4096, renderer.capabilities.maxTextureSize);
    sunLight.shadow.mapSize.set(ms, ms);
    sunLight.shadow.bias = -0.0005;
    sunLight.shadow.normalBias = 10;
    scene.add(sunLight, sunLight.target);

    buildSky(); buildLander(); buildBeam(); buildFlatDisc(); buildShadowStrip();
    ['Lander', 'Sun', 'Earth'].forEach((k) => { mk[k] = $('mk' + k); });
    bindControls();
    canvas.addEventListener('webglcontextlost', (e) => { e.preventDefault(); ok = false; if (api.onLost) api.onLost(); });
    new ResizeObserver(resize).observe(host);
    resize();
    ok = true;
    return true;
  }

  function resize() {
    if (!renderer) return;
    const w = Math.max(1, host.clientWidth), h = Math.max(1, host.clientHeight);
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }

  function buildSky() {
    sky = new THREE.Group();
    scene.add(sky);
    const rs = SKY_D * Math.tan(Sim.SUN_R * D2R);
    sunDisc = new THREE.Mesh(new THREE.CircleGeometry(rs, 48), new THREE.MeshBasicMaterial({ color: 0xfff4dc, toneMapped: false }));
    sky.add(sunDisc);
    const g = document.createElement('canvas'); g.width = g.height = 256;
    const gc = g.getContext('2d'), grad = gc.createRadialGradient(128, 128, 0, 128, 128, 128);
    grad.addColorStop(0, 'rgba(255,238,200,1)'); grad.addColorStop(0.06, 'rgba(255,226,170,0.75)');
    grad.addColorStop(0.2, 'rgba(255,200,120,0.16)'); grad.addColorStop(0.55, 'rgba(255,180,90,0.04)'); grad.addColorStop(1, 'rgba(255,170,80,0)');
    gc.fillStyle = grad; gc.fillRect(0, 0, 256, 256);
    sunGlow = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(g), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, toneMapped: false }));
    sunGlow.scale.set(rs * 30, rs * 30, 1);
    sky.add(sunGlow);
    // ince yatay parlama çizgisi (çok hafif)
    const s2 = document.createElement('canvas'); s2.width = 256; s2.height = 32;
    const c2 = s2.getContext('2d'), g2 = c2.createLinearGradient(0, 0, 256, 0);
    g2.addColorStop(0, 'rgba(255,220,160,0)'); g2.addColorStop(0.5, 'rgba(255,234,196,0.5)'); g2.addColorStop(1, 'rgba(255,220,160,0)');
    c2.fillStyle = g2; c2.fillRect(0, 0, 256, 32);
    const g3 = c2.createLinearGradient(0, 0, 0, 32);
    g3.addColorStop(0, 'rgba(0,0,0,1)'); g3.addColorStop(0.5, 'rgba(0,0,0,0)'); g3.addColorStop(1, 'rgba(0,0,0,1)');
    c2.globalCompositeOperation = 'destination-out'; c2.fillStyle = g3; c2.fillRect(0, 0, 256, 32);
    sunStreak = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(s2), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, toneMapped: false }));
    sunStreak.scale.set(rs * 110, rs * 5, 1);
    sky.add(sunStreak);

    // Dünya: Güneş'le aynı yönden aydınlanan küre; evre kendiliğinden çıkar. Bulut/kara deseni temsilidir.
    earthMat = new THREE.ShaderMaterial({
      uniforms: { sunDir: { value: new THREE.Vector3(1, 0, 0) } },
      vertexShader: `varying vec3 vN; varying vec3 vP;
        void main(){ vN = normalize(mat3(modelMatrix) * normal); vec4 wp = modelMatrix * vec4(position,1.0); vP = wp.xyz; gl_Position = projectionMatrix * viewMatrix * wp; }`,
      fragmentShader: `uniform vec3 sunDir; varying vec3 vN; varying vec3 vP;
        float hash(vec3 p){ p = fract(p*0.3183099 + .1); p *= 17.0; return fract(p.x*p.y*p.z*(p.x+p.y+p.z)); }
        float noise(vec3 x){ vec3 i = floor(x), f = fract(x); f = f*f*(3.0-2.0*f);
          return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x), mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x), f.y),
                     mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x), mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x), f.y), f.z); }
        float fbm(vec3 p){ float a = 0.5, s = 0.0; for(int i=0;i<5;i++){ s += a*noise(p); p *= 2.03; a *= 0.5; } return s; }
        void main(){
          vec3 n = normalize(vN);
          float day = smoothstep(-0.06, 0.22, dot(n, sunDir));
          float land = smoothstep(0.5, 0.58, fbm(n*1.7 + vec3(9.1, 2.0, 4.0)));
          float cloud = smoothstep(0.48, 0.72, fbm(n*3.2 + vec3(1.7)));
          vec3 col = mix(vec3(0.02,0.12,0.40), vec3(0.10,0.20,0.10), land*0.7);
          col = mix(col, vec3(0.92), cloud*0.85);
          vec3 v = normalize(cameraPosition - vP);
          float rim = pow(1.0 - max(dot(n, v), 0.0), 2.5);
          col += vec3(0.20, 0.45, 1.0) * rim * 0.7;
          col = col * day * 1.9 + vec3(0.001, 0.002, 0.006);
          gl_FragColor = vec4(col, 1.0);
          #include <tonemapping_fragment>
          #include <colorspace_fragment>
        }`,
    });
    earth = new THREE.Mesh(new THREE.SphereGeometry(SKY_D * Math.tan(Sim.EARTH_R * D2R), 48, 32), earthMat);
    sky.add(earth);

    // çok soluk yıldızlar; Güneş görünürken daha da söner
    const N = 520, pos = new Float32Array(N * 3);
    let seed = 7;
    const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    for (let i = 0; i < N; i++) {
      const u = rnd() * 2 - 1, a = rnd() * Math.PI * 2, r = Math.sqrt(1 - u * u);
      pos.set([r * Math.cos(a) * SKY_D * 1.6, u * SKY_D * 1.6, r * Math.sin(a) * SKY_D * 1.6], i * 3);
    }
    const sg = new THREE.BufferGeometry();
    sg.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    starMat = new THREE.PointsMaterial({ color: 0xc9d2e6, size: 1.5, sizeAttenuation: false, transparent: true, opacity: 0.4, depthWrite: false });
    const stars = new THREE.Points(sg, starMat);
    stars.frustumCulled = false;
    sky.add(stars);
  }

  function strut(a, b, r, mat, parent) {
    const va = new THREE.Vector3(...a), vb = new THREE.Vector3(...b), d = vb.clone().sub(va);
    const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, d.length(), 6), mat);
    m.position.copy(va).addScaledVector(d, 0.5);
    m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize());
    m.receiveShadow = true;
    parent.add(m);
  }

  // sembolik iniş aracı: gövde, 4 bacak, dikey güneş paneli (Güneş'i izler), çanak anten (Dünya'yı izler)
  function buildLander() {
    lander = new THREE.Group();
    const white = new THREE.MeshLambertMaterial({ color: 0xd9d6cc });
    const foil = new THREE.MeshLambertMaterial({ color: 0xa48648 });
    const dark = new THREE.MeshLambertMaterial({ color: 0x2a2c2f });
    const add = (geo, mat, x, y, z, parent = lander) => { const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.receiveShadow = true; parent.add(m); return m; };
    add(new THREE.CylinderGeometry(1.25, 1.4, 1.0, 8), white, 0, 1.55, 0);
    add(new THREE.CylinderGeometry(1.55, 1.55, 0.22, 8), foil, 0, 0.95, 0);
    add(new THREE.CylinderGeometry(0.28, 0.55, 0.55, 12), dark, 0, 0.56, 0);
    for (let i = 0; i < 4; i++) {
      const a = Math.PI / 4 + (i * Math.PI) / 2, cx = Math.cos(a), cz = Math.sin(a);
      strut([cx * 1.3, 1.0, cz * 1.3], [cx * 2.35, 0.1, cz * 2.35], 0.055, white, lander);
      strut([cx * 1.2, 1.8, cz * 1.2], [cx * 2.35, 0.1, cz * 2.35], 0.04, white, lander);
      add(new THREE.CylinderGeometry(0.32, 0.32, 0.07, 12), foil, cx * 2.35, 0.04, cz * 2.35);
    }
    add(new THREE.CylinderGeometry(0.06, 0.06, 1.9, 8), white, -0.7, 3.0, 0);
    panelPivot = new THREE.Group();
    panelPivot.position.set(-0.7, 3.15, 0);
    lander.add(panelPivot);
    panelMat = new THREE.MeshLambertMaterial({ color: 0x131c33, emissive: 0xffb21e, emissiveIntensity: 0 });
    add(new THREE.BoxGeometry(2.4, 1.7, 0.05), white, 0, 0, 0, panelPivot);
    add(new THREE.PlaneGeometry(2.24, 1.54), panelMat, 0, 0, 0.03, panelPivot);
    add(new THREE.CylinderGeometry(0.05, 0.05, 0.75, 8), white, 0.8, 2.42, 0);
    dishPivot = new THREE.Group();
    dishPivot.position.set(0.8, 2.85, 0);
    lander.add(dishPivot);
    const pts = [];
    for (let i = 0; i <= 10; i++) { const r = (0.55 * i) / 10; pts.push(new THREE.Vector2(r, 0.6 * r * r)); }
    const dishGeo = new THREE.LatheGeometry(pts, 28);
    dishGeo.rotateX(Math.PI / 2); // çanağın ağzı +Z'ye baksın (lookAt +Z'yi hedefe çevirir)
    add(dishGeo, new THREE.MeshLambertMaterial({ color: 0xe6e3da, side: THREE.DoubleSide }), 0, 0, 0, dishPivot);
    const feed = new THREE.CylinderGeometry(0.02, 0.02, 0.4, 6);
    feed.rotateX(Math.PI / 2);
    add(feed, dark, 0, 0, 0.2, dishPivot);
    // yanıp sönen işaret ışığı: araç uzaktan ve karanlıkta da bulunabilsin
    const bc = document.createElement('canvas'); bc.width = bc.height = 32;
    const bx = bc.getContext('2d'), bg = bx.createRadialGradient(16, 16, 0, 16, 16, 16);
    bg.addColorStop(0, 'rgba(255,255,255,1)'); bg.addColorStop(0.35, 'rgba(255,255,255,0.5)'); bg.addColorStop(1, 'rgba(255,255,255,0)');
    bx.fillStyle = bg; bx.fillRect(0, 0, 32, 32);
    beacon = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(bc), sizeAttenuation: false, transparent: true, depthWrite: false, toneMapped: false }));
    beacon.position.set(-0.7, 4.25, 0);
    beacon.scale.set(0.011, 0.011, 1);
    lander.add(beacon);
    lander.visible = false;
    scene.add(lander);
  }

  // aracın yere düşen gölgesi: 20 km'lik gölge haritası bu ölçeği çözemediği için ayrı, temsili bir şerit
  function buildShadowStrip() {
    const g = new THREE.BufferGeometry(), idx = [];
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array((SH_SEG + 1) * 6), 3));
    g.setAttribute('color', new THREE.BufferAttribute(new Float32Array((SH_SEG + 1) * 8), 4));
    for (let i = 0; i < SH_SEG; i++) { const a = i * 2; idx.push(a, a + 1, a + 2, a + 2, a + 1, a + 3); }
    g.setIndex(idx);
    shadowStrip = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ vertexColors: true, transparent: true, depthWrite: false, side: THREE.DoubleSide,
      polygonOffset: true, polygonOffsetFactor: -4, polygonOffsetUnits: -4, toneMapped: false }));
    shadowStrip.frustumCulled = false; shadowStrip.visible = false;
    scene.add(shadowStrip);
  }
  function updateShadowStrip() {
    const show = st.sunFrac > 0.03 && st.sunAlt > 0.3;
    shadowStrip.visible = show;
    if (!show) return;
    const len = Math.min(4.2 / Math.tan(st.sunAlt * D2R), 450), ys = terrain.scale.y;
    const hl = Math.hypot(V.sun.x, V.sun.z) || 1, dx = -V.sun.x / hl, dz = -V.sun.z / hl;
    const pa = shadowStrip.geometry.attributes.position, ca = shadowStrip.geometry.attributes.color;
    for (let i = 0; i <= SH_SEG; i++) {
      const s = i / SH_SEG, d = 1.0 + s * len, w = lerp(1.45, 0.55, s), a = 0.82 * st.sunFrac * Math.pow(1 - s, 0.7);
      for (let k = 0; k < 2; k++) {
        const sg = k ? 1 : -1, x = V.lander.x + dx * d + dz * w * sg, z = V.lander.z + dz * d - dx * w * sg;
        pa.setXYZ(i * 2 + k, x, groundY(x, z) * ys + 0.1, z);
        ca.setXYZW(i * 2 + k, 0, 0, 0, a);
      }
    }
    pa.needsUpdate = true; ca.needsUpdate = true;
  }

  function buildBeam() {
    const mkLine = (mat) => {
      const g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(6), 3));
      const l = new THREE.Line(g, mat);
      l.frustumCulled = false; l.visible = false;
      scene.add(l);
      return l;
    };
    beamUp = mkLine(new THREE.LineBasicMaterial({ color: 0x6fb2ff, transparent: true, opacity: 0.95, toneMapped: false }));
    beamCut = mkLine(new THREE.LineDashedMaterial({ color: 0xff3d6e, dashSize: 4, gapSize: 3, toneMapped: false }));
  }

  function buildFlatDisc() {
    const g = new THREE.CircleGeometry(220000, 96);
    g.rotateX(-Math.PI / 2);
    flatDisc = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ color: 0x8f897e }));
    flatDisc.position.y = -6;
    flatDisc.visible = false;
    scene.add(flatDisc);
  }

  // ---------- regolit dokusu (yordamsal): albedo + normal ----------
  function regolith() {
    if (regoTex) return regoTex;
    const N = 512, h = new Float32Array(N * N);
    let seed = 13;
    const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    // yalnız kısa dalga boyları: uzaktan bakınca döşeme tekrarı görünmesin
    for (const [cells, amp] of [[22, 0.55], [46, 0.42], [96, 0.26], [190, 0.13]]) {
      const lat = new Float32Array(cells * cells).map(rnd);
      for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
        const fx = (x / N) * cells, fy = (y / N) * cells, x0 = Math.floor(fx), y0 = Math.floor(fy);
        let tx = fx - x0, ty = fy - y0; tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty);
        const x1 = (x0 + 1) % cells, y1 = (y0 + 1) % cells;
        const v = lerp(lerp(lat[y0 * cells + x0], lat[y0 * cells + x1], tx), lerp(lat[y1 * cells + x0], lat[y1 * cells + x1], tx), ty);
        h[y * N + x] += (v - 0.5) * amp;
      }
    }
    // küçük kraterler: çanak + kenar kabartısı (yakın planda yüzey okunur olsun)
    for (let k = 0; k < 120; k++) {
      const cx0 = Math.round(rnd() * N), cy0 = Math.round(rnd() * N), r = 2 + Math.pow(rnd(), 2.6) * 13, dep = r * 0.085, R = Math.ceil(r * 1.7);
      for (let yy = -R; yy <= R; yy++) for (let xx = -R; xx <= R; xx++) {
        const q = Math.hypot(xx, yy) / r;
        if (q > 1.7) continue;
        const v = q < 1 ? -dep * (1 - q * q) + dep * 0.22 * q * q : dep * 0.22 * Math.exp(-((q - 1) * (q - 1)) / 0.05);
        h[((((cy0 + yy) % N) + N) % N) * N + ((((cx0 + xx) % N) + N) % N)] += v;
      }
    }
    const mkCanvas = (fn) => {
      const c = document.createElement('canvas'); c.width = c.height = N;
      const cx = c.getContext('2d'), im = cx.createImageData(N, N);
      for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) { const o = (y * N + x) * 4; fn(x, y, im.data, o); im.data[o + 3] = 255; }
      cx.putImageData(im, 0, 0);
      return c;
    };
    const at = (x, y) => h[((y + N) % N) * N + ((x + N) % N)];
    const albedo = mkCanvas((x, y, d, o) => { const v = clamp(236 + clamp(at(x, y), -0.7, 0.7) * 30, 0, 255); d[o] = d[o + 1] = d[o + 2] = v; });
    const normal = mkCanvas((x, y, d, o) => {
      const dx = (at(x + 1, y) - at(x - 1, y)) * 1.6, dy = (at(x, y + 1) - at(x, y - 1)) * 1.6, l = Math.hypot(dx, dy, 1);
      d[o] = (-dx / l) * 127 + 128; d[o + 1] = (-dy / l) * 127 + 128; d[o + 2] = (1 / l) * 127 + 128;
    });
    const tex = (c, srgb) => {
      const tx = new THREE.CanvasTexture(c);
      tx.wrapS = tx.wrapT = THREE.RepeatWrapping;
      tx.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
      if (srgb) tx.colorSpace = THREE.SRGBColorSpace;
      return tx;
    };
    regoTex = { map: tex(albedo, true), normalMap: tex(normal, false) };
    return regoTex;
  }

  // ---------- bölgeye özel nesneler ----------
  // NaN boşlukları komşu ortalamasıyla doldur; derinliği (kaç geçişte dolduğu) sakla
  function fillGaps(z, W, H) {
    const out = Float32Array.from(z), depth = new Uint16Array(W * H);
    let pending = [];
    for (let i = 0; i < out.length; i++) if (Number.isNaN(out[i])) pending.push(i);
    let pass = 0;
    while (pending.length && pass < 600) {
      pass++;
      const upd = [], next = [];
      for (const i of pending) {
        const r = (i / W) | 0, c = i % W;
        let s = 0, k = 0;
        if (c > 0 && !Number.isNaN(out[i - 1])) { s += out[i - 1]; k++; }
        if (c < W - 1 && !Number.isNaN(out[i + 1])) { s += out[i + 1]; k++; }
        if (r > 0 && !Number.isNaN(out[i - W])) { s += out[i - W]; k++; }
        if (r < H - 1 && !Number.isNaN(out[i + W])) { s += out[i + W]; k++; }
        if (k) upd.push(i, s / k); else next.push(i);
      }
      for (let j = 0; j < upd.length; j += 2) { out[upd[j]] = upd[j + 1]; depth[upd[j]] = pass; }
      pending = next;
    }
    for (const i of pending) { out[i] = 0; depth[i] = 999; }
    return { out, depth };
  }

  function groundY(x, z) {
    if (!grid) return 0;
    const fc = clamp(x / grid.sp + (grid.W - 1) / 2, 0, grid.W - 1.001), fr = clamp(z / grid.sp + (grid.H - 1) / 2, 0, grid.H - 1.001);
    const c = Math.floor(fc), r = Math.floor(fr), tx = fc - c, ty = fr - r, i = r * grid.W + c;
    return lerp(lerp(grid.z[i], grid.z[i + 1], tx), lerp(grid.z[i + grid.W], grid.z[i + grid.W + 1], tx), ty);
  }

  function buildTerrain(tr) {
    const W = tr.meta.width, H = tr.meta.height, sp = tr.meta.spacing_m;
    const { out, depth } = fillGaps(tr.z, W, H);
    let min = Infinity, max = -Infinity;
    const pos = new Float32Array(W * H * 3), uv = new Float32Array(W * H * 2), REP = (W * sp) / 170;
    for (let r = 0; r < H; r++) for (let c = 0; c < W; c++) {
      const i = r * W + c, y = out[i];
      if (depth[i] <= 3) { if (y < min) min = y; if (y > max) max = y; }
      pos[i * 3] = (c - (W - 1) / 2) * sp; pos[i * 3 + 1] = y; pos[i * 3 + 2] = (r - (H - 1) / 2) * sp;
      uv[i * 2] = (c / (W - 1)) * REP; uv[i * 2 + 1] = (r / (H - 1)) * REP;
    }
    // büyük veri boşlukları (köşeler) çizilmez: uydurma arazi göstermeyelim
    const idx = new Uint32Array((W - 1) * (H - 1) * 6);
    let k = 0;
    for (let r = 0; r < H - 1; r++) for (let c = 0; c < W - 1; c++) {
      const a = r * W + c, b = a + 1, d = a + W, e = d + 1;
      if (depth[a] > 3 || depth[b] > 3 || depth[d] > 3 || depth[e] > 3) continue;
      idx[k++] = a; idx[k++] = d; idx[k++] = b; idx[k++] = b; idx[k++] = d; idx[k++] = e;
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    geo.setIndex(new THREE.BufferAttribute(idx.subarray(0, k), 1));
    geo.computeVertexNormals();
    grid = { z: out, W, H, sp, min, max, half: ((W - 1) * sp) / 2 };

    if (!terrainMat) {
      const rg = regolith();
      terrainMat = new THREE.MeshLambertMaterial({ color: 0x97938c, map: rg.map, normalMap: rg.normalMap, normalScale: new THREE.Vector2(0.24, 0.24) });
      // Ay regoliti Lambert gibi davranmaz: sığ açıda Lommel-Seeliger'e yakındır. Karışım kullan.
      terrainMat.onBeforeCompile = (sh) => {
        const chunk = THREE.ShaderChunk.lights_lambert_pars_fragment;
        const patched = chunk.replace(
          /float dotNL = saturate\( dot\( (\w+), directLight\.direction \) \);/,
          'float dotNLr = saturate( dot( $1, directLight.direction ) ); float dotNVr = saturate( dot( $1, geometryViewDir ) ); float dotNL = mix( dotNLr, min( 2.0 * dotNLr / ( dotNLr + dotNVr + 0.02 ), 1.2 ), 0.55 ); dotNL *= smoothstep( -0.07, 0.03, dot( normalize( vNormal ), directLight.direction ) );');
        if (patched !== chunk && chunk.includes('geometryViewDir')) sh.fragmentShader = sh.fragmentShader.replace('#include <lights_lambert_pars_fragment>', patched);
      };
      flatDisc.material = new THREE.MeshLambertMaterial({ color: 0x97938c });
    }
    terrain = new THREE.Mesh(geo, terrainMat);
    terrain.castShadow = true; terrain.receiveShadow = true;
    scene.add(terrain);
  }

  // 360° ufuk profilinden siluet halkası: gözlemciden bakınca gerçek ufku verir
  function buildRing(hz) {
    const n = hz.elev.length, pos = new Float32Array((n + 1) * 6), idx = new Uint32Array(n * 6);
    const bottom = -RING_R * Math.tan(14 * D2R);
    for (let i = 0; i <= n; i++) {
      const j = i % n, az = j * hz.step * D2R;
      let el = hz.elev[j];
      if (hz.dist[j] < 9.5) el -= 0.05; // yakın ufku arazi ağı çiziyor; halka onun hemen ardında kalsın
      const x = Math.sin(az) * RING_R, z = -Math.cos(az) * RING_R, top = EYE + RING_R * Math.tan(el * D2R);
      pos.set([x, top, z, x, Math.min(bottom, top - 100), z], i * 6);
      if (i < n) idx.set([i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 2, i * 2 + 1, i * 2 + 3], i * 6);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setIndex(new THREE.BufferAttribute(idx, 1));
    if (!ringMat) {
      ringMat = new THREE.ShaderMaterial({
        side: THREE.DoubleSide, transparent: true,
        uniforms: { sunDir: { value: new THREE.Vector3() }, lit: { value: 1 }, alpha: { value: 1 }, base: { value: new THREE.Color(0x97938c) } },
        vertexShader: `varying vec3 vIn; void main(){ vIn = normalize(vec3(-position.x, 0.0, -position.z)); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
        fragmentShader: `uniform vec3 sunDir; uniform float lit; uniform float alpha; uniform vec3 base; varying vec3 vIn;
          void main(){ float d = max(dot(normalize(vIn), normalize(vec3(sunDir.x, 0.0, sunDir.z))), 0.0);
            vec3 col = base * (0.015 + lit * d * 0.5);
            gl_FragColor = vec4(col, alpha);
            #include <tonemapping_fragment>
            #include <colorspace_fragment>
          }`,
      });
    }
    ring = new THREE.Mesh(geo, ringMat);
    ring.frustumCulled = false;
    scene.add(ring);
  }

  // Dünya'nın yıl boyunca gökte çizdiği iz (librasyon)
  function buildTrace(se) {
    const pts = [], v = new THREE.Vector3();
    for (let i = 0; i < se.n; i += 3) { dirTo(se.earthAlt[i], se.earthAz[i], v); pts.push(v.x * SKY_D * 1.002, v.y * SKY_D * 1.002, v.z * SKY_D * 1.002); }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(pts), 3));
    trace = new THREE.Line(g, new THREE.LineBasicMaterial({ color: 0x5aa5ff, transparent: true, opacity: 0.16, depthWrite: false, toneMapped: false }));
    trace.frustumCulled = false;
    sky.add(trace);
  }

  // yüksekten bakınca bağlam: kutup haritası (soluk) ve bölge sınırı. Alçakta gizlenir.
  function buildContext(o) {
    const b = o.map.bounds, S = 2048, c = document.createElement('canvas');
    c.width = c.height = S;
    const cx = c.getContext('2d');
    cx.fillStyle = '#1a1d1c'; cx.fillRect(0, 0, S, S);
    if (o.map.image) cx.drawImage(o.map.image, 0, 0, S, S);
    const px = (x) => ((x - b[0]) / (b[2] - b[0])) * S, py = (y) => ((b[3] - y) / (b[3] - b[1])) * S;
    const regionId = o.site.regionId || o.site.id; // aday noktada da kendi bölgesi vurgulansın
    for (const s of o.sites) {
      cx.beginPath();
      s.reg.polygon_ps_km.forEach(([x, y], i) => (i ? cx.lineTo(px(x), py(y)) : cx.moveTo(px(x), py(y))));
      cx.closePath();
      cx.lineWidth = s.id === regionId ? 2.5 : 1.5; cx.strokeStyle = s.id === regionId ? '#ffffff' : 'rgba(220,228,224,0.7)';
      cx.stroke();
    }
    const tx = new THREE.CanvasTexture(c);
    tx.colorSpace = THREE.SRGBColorSpace;
    tx.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
    const size = (b[2] - b[0]) * 1000, g = new THREE.PlaneGeometry(size, size);
    g.rotateX(-Math.PI / 2);
    contextMat = new THREE.MeshBasicMaterial({ map: tx, transparent: true, opacity: 0, depthWrite: false, color: 0x777b79 });
    context = new THREE.Mesh(g, contextMat);
    // harita düzleminde: x̂ → (cosλ, 0, −sinλ), ŷ → (−sinλ, 0, −cosλ); nokta (0,0,0)'a gelsin
    const lam = o.site.lon * D2R, sxk = o.site.ps_km[0], syk = o.site.ps_km[1];
    context.rotation.y = lam;
    const ex = sxk * Math.cos(lam) - syk * Math.sin(lam), nn = sxk * Math.sin(lam) + syk * Math.cos(lam);
    context.position.set(-ex * 1000, grid.min - 300, nn * 1000);
    context.renderOrder = -1;
    context.visible = false;
    scene.add(context);
  }

  function disposeSite() {
    for (const obj of [terrain, ring, context]) if (obj) { scene.remove(obj); obj.geometry.dispose(); }
    if (context) { contextMat.map.dispose(); contextMat.dispose(); }
    if (trace) { sky.remove(trace); trace.geometry.dispose(); trace.material.dispose(); }
    terrain = ring = context = trace = null;
  }

  function circMean(arr) {
    let s = 0, c = 0;
    for (let i = 0; i < arr.length; i += 24) { s += Math.sin(arr[i] * D2R); c += Math.cos(arr[i] * D2R); }
    return (Math.atan2(s, c) / D2R + 360) % 360;
  }

  // o: { site, sites, map, horizon, series, terrain }
  function setSite(o) {
    if (!ok) return;
    disposeSite();
    buildTerrain(o.terrain); buildRing(o.horizon); buildTrace(o.series); buildContext(o);
    siteEarthAz = circMean(o.series.earthAz);
    const az = (siteEarthAz + 35) * D2R, lx = Math.sin(az) * 14, lz = -Math.cos(az) * 14;
    V.lander.set(lx, groundY(lx, lz), lz);
    lander.position.copy(V.lander);
    lander.visible = true;
    st.flat = st.flatGoal; applyFlat();
    resetOrbit();
    cam.yaw = siteEarthAz * D2R; cam.pitch = 0.07; cam.fov = 55;
    st.shadowDirty = true;
  }

  function resetOrbit() {
    cam.az = Math.PI - (siteEarthAz + 205) * D2R; cam.pol = 1.2; cam.dist = 2600;
  }

  // ---------- kamera ve kontroller ----------
  function zoomBy(f) {
    if (cam.mode === 'astro') cam.fov = clamp(cam.fov * f, 2.5, 75);
    else cam.dist = clamp(cam.dist * f, 18, 60000);
  }
  function bindControls() {
    const pts = new Map();
    let pinch = 0;
    canvas.addEventListener('pointerdown', (e) => { tween = null; canvas.setPointerCapture(e.pointerId); pts.set(e.pointerId, [e.clientX, e.clientY]); });
    canvas.addEventListener('pointermove', (e) => {
      const p = pts.get(e.pointerId);
      if (!p || cam.cine) return;
      const dx = e.clientX - p[0], dy = e.clientY - p[1];
      p[0] = e.clientX; p[1] = e.clientY;
      if (pts.size === 2) {
        const [a, b] = [...pts.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]);
        if (pinch) zoomBy(pinch / d);
        pinch = d;
        return;
      }
      if (cam.mode === 'astro') {
        const k = (cam.fov * D2R) / Math.max(1, canvas.clientHeight);
        cam.yaw -= dx * k; cam.pitch = clamp(cam.pitch + dy * k, -0.6, 1.3);
      } else {
        cam.az -= dx * 0.005; cam.pol = clamp(cam.pol - dy * 0.005, 0.06, 1.56);
      }
    });
    const up = (e) => { pts.delete(e.pointerId); pinch = 0; };
    canvas.addEventListener('pointerup', up);
    canvas.addEventListener('pointercancel', up);
    canvas.addEventListener('wheel', (e) => { e.preventDefault(); if (!cam.cine) { tween = null; zoomBy(Math.exp(e.deltaY * 0.0012)); } }, { passive: false });
  }

  function updateCamera(dt) {
    if (cam.cine) cam.cine(dt);
    else if (tween) {
      tween.t += dt;
      const k = easeInOut(Math.min(1, tween.t / tween.dur));
      for (const key in tween.to) cam[key] = key === 'dist' ? tween.from.dist * Math.pow(tween.to.dist / tween.from.dist, k) : lerp(tween.from[key], tween.to[key], k);
      if (tween.t >= tween.dur) tween = null;
    }
    if (cam.mode === 'astro' && !cam.cine) {
      camera.position.set(0, EYE * (st.flat > 0.5 ? 1 : 1), 0);
      camera.rotation.set(cam.pitch, -cam.yaw, 0, 'YXZ');
      camera.fov = cam.fov; camera.near = 0.3;
    } else {
      const ys = terrain.scale.y;
      V.target.set(V.lander.x, V.lander.y * ys + 1.6, V.lander.z);
      const sp = Math.sin(cam.pol), cp = Math.cos(cam.pol);
      camera.position.set(V.target.x + cam.dist * sp * Math.sin(cam.az), V.target.y + cam.dist * cp, V.target.z + cam.dist * sp * Math.cos(cam.az));
      const gy = groundY(camera.position.x, camera.position.z) * ys + 2.5;
      if (Math.abs(camera.position.x) < grid.half && Math.abs(camera.position.z) < grid.half && camera.position.y < gy) camera.position.y = gy;
      camera.up.set(0, 1, 0);
      camera.lookAt(V.target);
      camera.fov = 50; camera.near = Math.max(0.5, cam.dist * 0.02);
    }
    camera.updateProjectionMatrix();
  }

  function setView(mode) {
    tween = null;
    cam.mode = mode === 'astro' ? 'astro' : 'orbit';
  }
  // yumuşak kamera geçişi (otomatik tur için); kullanıcı sahneye dokununca iptal olur
  function startTween(to, sec) {
    if (!ok || !terrain) return;
    const from = {};
    for (const key in to) from[key] = cam[key];
    if ('yaw' in to) { const d = to.yaw - cam.yaw; to.yaw = cam.yaw + Math.atan2(Math.sin(d), Math.cos(d)); }
    if ('pol' in to) to.pol = clamp(to.pol, 0.06, 1.56);
    tween = { from, to, t: 0, dur: Math.max(0.05, sec) };
  }
  function tweenLook(azDeg, altDeg, fov, sec) {
    startTween({ yaw: azDeg * D2R, pitch: clamp((altDeg - fov * 0.06) * D2R, -0.4, 1.2), fov }, sec);
  }
  function lookAt(azDeg, altDeg) {
    // hedef, panellerin örtmediği alanın ortasına gelsin diye biraz aşağıya bak
    if (cam.mode === 'astro') { cam.yaw = azDeg * D2R; cam.pitch = clamp((altDeg - cam.fov * 0.06) * D2R, -0.4, 1.2); }
  }
  function lookLander() {
    if (cam.mode === 'astro') { cam.yaw = Math.atan2(V.lander.x, -V.lander.z); cam.pitch = 0.1; cam.fov = 55; } else resetOrbit();
  }

  // iniş sekansı: yörünge yüksekliğinden araca doğru alçalan kamera (yörünge parametreleri canlandırılır)
  function startDescent(dur, onAlt, onDone) {
    if (!ok || !terrain) { onDone(); return; }
    cam.mode = 'orbit';
    resetOrbit();
    const azEnd = cam.az, dEnd = 62, polEnd = 1.36, d0 = 120000;
    let tt = 0, done = false;
    cam.cine = (dt) => {
      tt = Math.min(dur, tt + dt);
      const p = tt / dur, e = 1 - Math.pow(1 - p, 1.3);
      cam.dist = dEnd * Math.pow(d0 / dEnd, 1 - e);
      cam.pol = lerp(0.03, polEnd, smooth(0.3, 1, p));
      cam.az = azEnd - (1 - e) * 2.2;
      onAlt(Math.max(0, cam.dist * Math.cos(cam.pol)));
      if (p >= 1 && !done) { done = true; cam.cine = null; onDone(); }
    };
    return { skip() { tt = dur; } };
  }

  // ---------- kare başına güncelleme ----------
  function setFlat(on, instant) { st.flatGoal = on ? 1 : 0; if (instant) { st.flat = st.flatGoal; if (terrain) applyFlat(); } }
  function applyFlat() {
    const k = easeInOut(st.flat);
    terrain.scale.y = lerp(1, FLAT_Y, k);
    flatDisc.visible = st.flat > 0.02;
    lander.position.y = V.lander.y * terrain.scale.y;
    st.shadowDirty = true;
  }

  function update(s) {
    if (!ok) return;
    dirTo(s.sunAlt, s.sunAz, V.sun); dirTo(s.earthAlt, s.earthAz, V.earth);
    st.sunFrac = s.sunFrac; st.sunAlt = s.sunAlt; st.earthAlt = s.earthAlt; st.linkUp = s.linkUp; st.margin = s.margin; st.blockKm = s.blockKm; st.illum = s.illum;
  }

  function fitShadow() {
    const ys = terrain.scale.y, yLo = grid.min * ys - 5, yHi = Math.max(grid.max * ys, 0) + 12, cy = (yLo + yHi) / 2;
    sunLight.target.position.set(0, cy, 0);
    sunLight.position.set(V.sun.x * 40000, cy + V.sun.y * 40000, V.sun.z * 40000);
    sunLight.target.updateMatrixWorld();
    const f = V.a.copy(V.sun).negate(), r = V.b.set(0, 1, 0).cross(f).negate().normalize(), u = V.c.copy(r).cross(f);
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity, z0 = Infinity, z1 = -Infinity;
    const p = sunLight.position, h = grid.half;
    for (const X of [-h, h]) for (const Y of [yLo, yHi]) for (const Z of [-h, h]) {
      const dx = X - p.x, dy = Y - p.y, dz = Z - p.z;
      const a = dx * r.x + dy * r.y + dz * r.z, b = dx * u.x + dy * u.y + dz * u.z, c = dx * f.x + dy * f.y + dz * f.z;
      x0 = Math.min(x0, a); x1 = Math.max(x1, a); y0 = Math.min(y0, b); y1 = Math.max(y1, b); z0 = Math.min(z0, c); z1 = Math.max(z1, c);
    }
    const sc = sunLight.shadow.camera;
    sc.left = x0; sc.right = x1; sc.bottom = y0; sc.top = y1; sc.near = Math.max(1, z0 - 200); sc.far = z1 + 200;
    sc.updateProjectionMatrix();
    sunLight.shadow.needsUpdate = true;
    V.lastSun.copy(V.sun);
    st.shadowDirty = false;
  }

  function place(el, world, show, text) {
    if (!show) { el.hidden = true; return; }
    V.a.copy(world).project(camera);
    if (V.a.z > 1 || Math.abs(V.a.x) > 1.05 || Math.abs(V.a.y) > 1.05) { el.hidden = true; return; }
    el.hidden = false;
    el.style.transform = `translate(${((V.a.x * 0.5 + 0.5) * host.clientWidth).toFixed(1)}px, ${((-V.a.y * 0.5 + 0.5) * host.clientHeight).toFixed(1)}px)`;
    if (text != null) setText(el.lastElementChild, text);
  }

  function render(dt) {
    if (!ok || !terrain) return;
    if (st.flat !== st.flatGoal) {
      st.flat = st.flatGoal > st.flat ? Math.min(1, st.flat + dt / 0.8) : Math.max(0, st.flat - dt / 0.8);
      applyFlat();
    }
    updateCamera(dt);

    // Işığın doğruluğu: şiddet hesap verisinden (Güneş diskinin görünen oranı) gelir
    sunLight.intensity = SUN_I * st.sunFrac;
    earthLight.position.copy(V.earth).multiplyScalar(40000);
    earthLight.intensity = 0.3 * st.illum * smooth(-0.5, 1.5, st.margin);
    fillLight.intensity = 0.05 + 0.42 * (1 - st.sunFrac);
    bounce.intensity = 0.9 * st.sunFrac * smooth(-1, 3, st.sunAlt);
    if (st.sunFrac > 0 && (st.shadowDirty || V.sun.distanceToSquared(V.lastSun) > 2e-8)) fitShadow();

    const astro = cam.mode === 'astro' && !cam.cine, real = st.flat < 0.5;
    sky.position.copy(camera.position);
    sunDisc.position.copy(V.sun).multiplyScalar(SKY_D);
    sunDisc.lookAt(camera.position);
    sunGlow.position.copy(sunDisc.position);
    sunStreak.position.copy(sunDisc.position);
    sunGlow.material.opacity = 0.3 + 0.7 * st.sunFrac;
    sunStreak.material.opacity = 0.55 * st.sunFrac;
    // astronot gözünde HUD ile sahne çelişmesin: veri "hiç görünmüyor" diyorsa disk çizilmez
    const sunShown = !(astro && real && st.sunFrac <= 0.001);
    sunDisc.visible = sunGlow.visible = sunStreak.visible = sunShown;
    earth.position.copy(V.earth).multiplyScalar(SKY_D);
    earth.visible = !(astro && real && st.margin < -Sim.EARTH_R);
    earthMat.uniforms.sunDir.value.copy(V.sun);
    starMat.opacity = 0.42 * (1 - 0.8 * st.sunFrac);

    const hgt = camera.position.y - EYE;
    const ra = (1 - smooth(350, 3200, hgt)) * (1 - st.flat);
    ring.visible = ra > 0.01;
    ringMat.uniforms.alpha.value = ra;
    ringMat.transparent = ra < 0.995;
    ringMat.uniforms.sunDir.value.copy(V.sun);
    ringMat.uniforms.lit.value = smooth(-1.6, 0.4, st.sunAlt);
    contextMat.opacity = 0.62 * smooth(5000, 24000, hgt);
    context.visible = contextMat.opacity > 0.01;

    // araç: panel Güneş'in azimutunu, çanak Dünya'yı izler
    panelPivot.rotation.y = Math.atan2(V.sun.x, V.sun.z);
    panelMat.emissiveIntensity = 0.85 * st.sunFrac;
    clock += dt;
    beacon.material.opacity = clock % 1.8 < 0.16 ? 1 : 0.1;
    updateShadowStrip();
    dishPivot.getWorldPosition(V.dish);
    dishPivot.lookAt(V.a.copy(V.dish).add(V.earth));
    const up = st.linkUp;
    beamUp.visible = up; beamCut.visible = !up;
    const line = up ? beamUp : beamCut, len = up ? SKY_D * 0.98 : Math.max(30, Math.min(st.blockKm, 30) * 1000);
    const pa = line.geometry.attributes.position;
    pa.setXYZ(0, V.dish.x, V.dish.y, V.dish.z);
    pa.setXYZ(1, V.dish.x + V.earth.x * len, V.dish.y + V.earth.y * len, V.dish.z + V.earth.z * len);
    pa.needsUpdate = true;
    if (!up) {
      const dd = Math.max(1.5, camera.position.distanceTo(V.dish) * 0.012);
      beamCut.material.dashSize = dd; beamCut.material.gapSize = dd * 0.8;
      line.computeLineDistances();
    }

    renderer.render(scene, camera);

    place(mk.Lander, V.b.copy(lander.position).setY(lander.position.y + 2), !astro && !cam.cine && cam.dist > 140);
    place(mk.Sun, sunDisc.getWorldPosition(V.b), astro && sunShown, t('scene.sunTag', { v: Fmt.deg(st.sunAlt, 1) }));
    place(mk.Earth, earth.getWorldPosition(V.b), astro && earth.visible, t('scene.earthTag', { v: Fmt.deg(st.earthAlt, 1) }));

    // düşük donanım: kare süresi uzunsa gölge çözünürlüğünü ve piksel oranını düşür
    if (dt < 0.25) { quality.acc += dt; quality.frames++; }
    if (quality.frames >= 90) {
      if (!quality.lowered && quality.acc / quality.frames > 1 / 26) {
        quality.lowered = true;
        renderer.setPixelRatio(1); resize();
        sunLight.shadow.mapSize.set(2048, 2048);
        if (sunLight.shadow.map) { sunLight.shadow.map.dispose(); sunLight.shadow.map = null; }
        st.shadowDirty = true;
      }
      quality.acc = 0; quality.frames = 0;
    }
  }

  function hideMarkers() { for (const k in mk) if (mk[k]) mk[k].hidden = true; }

  return Object.assign(api, {
    init, setSite, setView, setFlat, update, render, startDescent, lookAt, lookLander, hideMarkers, resize,
    setOrbit(az, pol, dist) { tween = null; cam.az = az; cam.pol = pol; cam.dist = dist; },
    tween: startTween, tweenLook,
    get cam() { return cam; },
    setFov(v) { cam.fov = clamp(v, 2.5, 75); },
    get ok() { return ok; },
    get hasSite() { return !!terrain; },
    get view() { return { mode: cam.mode, yaw: (cam.yaw / D2R % 360 + 360) % 360, fov: cam.fov, aspect: camera ? camera.aspect : 1 }; },
  });
})();
