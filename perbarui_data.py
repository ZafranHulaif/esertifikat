#!/usr/bin/env python3
# Bangun ulang data.json untuk situs verifikasi e-Sertifikat.
#
# Membaca entri dari API Apps Script publik (JSON per nomor), lalu menulis
# data.json yang di-serve GitHub Pages sebagai jalur cepat verifikasi.
# Jalankan dari folder repo:
#   python perbarui_data.py              -> probe nomor 001..20 (bulan/tahun hari ini)
#   python perbarui_data.py --max 40     -> probe nomor 001..40
#   python perbarui_data.py 001 005 009  -> nomor eksplisit
# Setelah selesai: git commit data.json lalu push agar Pages membangun ulang.

import datetime
import json
import subprocess
import sys
import time

API = ("https://script.google.com/macros/s/"
       "AKfycbxdoe2tSGeX76ReDkHJK8EKu94DjE01KdNJPxOg4EOCBTwVvoe-L4IxRR-7mDRdNdHA2w/exec")
ROMAWI = ["I", "II", "III", "IV", "V", "VI",
          "VII", "VIII", "IX", "X", "XI", "XII"]


def ambil(nomor):
    url = API + "?json=1&no=" + nomor.replace(" ", "%20").replace(":", "%3A")
    for coba in range(5):
        p = subprocess.run(["curl", "-sL", "--max-time", "30", url],
                           capture_output=True, text=True)
        out = p.stdout.strip()
        if out.startswith("{"):
            try:
                return json.loads(out)
            except ValueError:
                pass
        time.sleep(2)
    return None


def main():
    hari = datetime.date.today()
    akhiran = "/%s/%d" % (ROMAWI[hari.month - 1], hari.year)

    args = sys.argv[1:]
    if args and args[0] == "--max":
        maks = int(args[1]) if len(args) > 1 else 20
        urutan = ["%03d" % i for i in range(1, maks + 1)]
    elif args:
        urutan = [a.zfill(3) for a in args]
    else:
        urutan = ["%03d" % i for i in range(1, 21)]

    baris = []
    meleset = 0
    probe = not args or args[0] == "--max"
    for urut in urutan:
        nomor = "NO : WEB/" + urut + akhiran
        d = ambil(nomor)
        if not d or not d.get("ok"):
            # API kadang menjawab tidak ditemukan padahal barisnya ada;
            # konfirmasi ulang sekali sebelum dianggap benar-benar absen.
            ulang = ambil(nomor)
            if ulang and ulang.get("ok"):
                d = ulang
        if not d or not d.get("ok"):
            meleset += 1
            print(nomor, "-> tidak ada")
            if meleset >= 3 and probe:
                print("3 miss berturut-turut, probe dihentikan")
                break
            continue
        meleset = 0
        baris.append({
            "no": d.get("no", nomor),
            "nama": d.get("nama", ""),
            "sek": d.get("sek", ""),
            "peran": d.get("peran", ""),
            "tgl": d.get("tgl", ""),
            "pdf": d.get("pdf", ""),
        })
        print(nomor, "->", d.get("nama", "?"))

    kini = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))
    data = {
        "generated_at": kini.isoformat(timespec="seconds"),
        "rows": baris,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("data.json: %d baris, generated_at %s" % (len(baris), data["generated_at"]))


if __name__ == "__main__":
    main()
