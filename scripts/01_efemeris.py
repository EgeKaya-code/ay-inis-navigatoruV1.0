"""Saatlik Güneş ve Dünya konum tablosunu üretir.

Çıktı: data/islenmis/efemeris.npz
  zaman_unix  : int64, saniye (UTC)
  gunes_km    : float64 [n,3] Ay merkezinden, MOON_ME
  dunya_km    : float64 [n,3]
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aynav.config import islenmis_klasoru, varsayimlar  # noqa: E402
from aynav.efemeris import kernelleri_yukle, konumlar, saatlik_zamanlar  # noqa: E402


def main():
    kernelleri_yukle()
    z = saatlik_zamanlar()
    g, d = konumlar(z)
    zaman = np.array([int(t.timestamp()) for t in z], dtype=np.int64)
    cikti = islenmis_klasoru() / "efemeris.npz"
    np.savez_compressed(cikti, zaman_unix=zaman, gunes_km=g, dunya_km=d)
    e = varsayimlar()["efemeris"]
    print(f"{len(z)} saat ({e['baslangic']} – {e['bitis']}), çerçeve {e['cerceve']} -> {cikti}")


if __name__ == "__main__":
    main()
