#!/usr/bin/env python3
# renumer.py — renomme les vidéos d'un dossier en N, N+1, N+2...
# trié par date de modification (mtime) ou de création (ctime)
#
# Usage:
#   python3 renumer.py DOSSIER                    # aperçu
#   python3 renumer.py DOSSIER --apply            # applique
#   python3 renumer.py DOSSIER --apply --start 10 # commence à 10
#   python3 renumer.py DOSSIER --sort ctime       # tri par date de création
#   python3 renumer.py DOSSIER --ext mp4,mov      # filtre d'extensions
#   python3 renumer.py DOSSIER --recursive        # sous-dossiers inclus

import os, argparse, datetime

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v",
              ".flv", ".mpg", ".mpeg", ".wmv", ".mts", ".ts", ".m2ts"}

def collect(folder, exts, recursive):
    out = []
    if recursive:
        for root, _, files in os.walk(folder):
            for f in files:
                if os.path.splitext(f)[1].lower() in exts:
                    out.append(os.path.join(root, f))
    else:
        for f in os.listdir(folder):
            p = os.path.join(folder, f)
            if os.path.isfile(p) and os.path.splitext(f)[1].lower() in exts:
                out.append(p)
    return out

def get_time(path, mode):
    st = os.stat(path)
    return st.st_ctime if mode == "ctime" else st.st_mtime

def main():
    p = argparse.ArgumentParser()
    p.add_argument("folder")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--sort", choices=["mtime", "ctime"], default="mtime")
    p.add_argument("--ext", default=None, help="ex: mp4,mov")
    p.add_argument("--recursive", action="store_true")
    p.add_argument("--start", type=int, default=1,
                   help="numéro du premier fichier (défaut: 1)")
    p.add_argument("--pad", type=int, default=0,
                   help="zéros devant le numéro, ex: --pad 3 -> 010.mp4")
    p.add_argument("--precise", action="store_true",
                   help="affiche les fractions de seconde")
    a = p.parse_args()

    exts = VIDEO_EXTS
    if a.ext:
        exts = {"." + e.strip().lower().lstrip(".") for e in a.ext.split(",")}

    files = collect(a.folder, exts, a.recursive)
    if not files:
        print("Aucune vidéo trouvée.")
        return

    files.sort(key=lambda x: (get_time(x, a.sort), os.path.basename(x).lower()))

    def label(i):
        return f"{i:0{a.pad}d}" if a.pad else str(i)

    label_txt = "création" if a.sort == "ctime" else "modification"
    print(f"{len(files)} vidéo(s) — tri par date de {label_txt}")
    print(f"Numérotation de {a.start} à {a.start + len(files) - 1}")
    print("-" * 62)

    if not a.apply:
        for i, src in enumerate(files, a.start):
            ts = datetime.datetime.fromtimestamp(get_time(src, a.sort))
            fmt = "%Y-%m-%d %H:%M:%S.%f" if a.precise else "%Y-%m-%d %H:%M"
            print(f"{label(i):>5}. {ts:{fmt}}  {os.path.basename(src)}")
        print("-" * 62)
        print("APERÇU : rien n'a été modifié. Relance avec --apply.")
        return

    # APPLIQUER : renommage en 2 temps pour éviter les collisions
    tmp = []
    for i, src in enumerate(files, a.start):
        d = os.path.dirname(src)
        ext = os.path.splitext(src)[1]
        t = os.path.join(d, f"__tmp_renumer_{i}{ext}")
        os.rename(src, t)
        tmp.append((t, os.path.join(d, f"{label(i)}{ext}"), os.path.basename(src)))

    for src, dst, old in tmp:
        os.rename(src, dst)
        print(f"{old}  →  {os.path.basename(dst)}")

    print("-" * 62)
    print(f"OK — {len(files)} vidéo(s) renommée(s) dans {a.folder}")

if __name__ == "__main__":
    main()
