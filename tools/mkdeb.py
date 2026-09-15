#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mkdeb.py — 不依赖 dpkg-deb 的 .deb 打包器
========================================
.deb 就是一个 ar 归档,内含三个成员:

    debian-binary   →  "2.0\n"
    control.tar.gz  →  ./control, ./postinst, ./prerm, ./postrm
    data.tar.gz     →  实际文件系统(./usr/local/<appid>/...)

本脚本用纯标准库实现 ar + tar.gz,可在 Windows / 无 dpkg 的环境下打包。

用法:
    python3 mkdeb.py --appid <id> --mode single|dual --platform x86_64

输出:
    build/output/<appid>_<ver>_<arch>.deb            (single)
    build/output/<appid>_<platform>.tar.gz           (dual,内含两个 .deb)
    build/output/sha256sum.txt
"""
import argparse, gzip, hashlib, io, os, re, shutil, sys, tarfile, time
from pathlib import Path

FIXED_MTIME = 1700000000          # 固定时间戳,保证可复现
ARCH_MAP = {"x86_64": "amd64", "aarch64": "arm64"}


# ────────────────────────────── ar 写入 ──────────────────────────────
def _ar_header(name: str, size: int, mode: int = 0o100644) -> bytes:
    if len(name) > 15:
        raise ValueError(f"ar member name too long: {name}")
    hdr = (f"{name + '/':<16}"
           f"{FIXED_MTIME:<12}"
           f"{0:<6}{0:<6}"
           f"{mode:<8o}"
           f"{size:<10}"
           f"`\n")
    assert len(hdr) == 60, len(hdr)
    return hdr.encode("ascii")


def write_ar(path: Path, members):
    """members: [(name, bytes, mode)]"""
    with open(path, "wb") as f:
        f.write(b"!<arch>\n")
        for name, data, mode in members:
            f.write(_ar_header(name, len(data), mode))
            f.write(data)
            if len(data) % 2:
                f.write(b"\n")


# ────────────────────────────── tar.gz 构建 ──────────────────────────────
def add_bytes(tf: tarfile.TarFile, arcname: str, data: bytes, mode=0o644):
    ti = tarfile.TarInfo(arcname)
    ti.size = len(data)
    ti.mtime = FIXED_MTIME
    ti.mode = mode
    ti.uid = ti.gid = 0
    ti.uname = ti.gname = "root"
    tf.addfile(ti, io.BytesIO(data))


def add_tree(tf: tarfile.TarFile, src: Path, prefix: str, skip=()):
    """把 src 下的树加进 tar,arcname 前缀为 ./<prefix>/"""
    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if any(str(rel).startswith(s) for s in skip):
            continue
        arc = f"./{prefix}/{rel.as_posix()}"
        if p.is_dir():
            ti = tarfile.TarInfo(arc + "/")
            ti.type = tarfile.DIRTYPE
            ti.mode = 0o755
            ti.mtime = FIXED_MTIME
            ti.uid = ti.gid = 0
            ti.uname = ti.gname = "root"
            tf.addfile(ti)
        elif p.is_file():
            mode = 0o755 if os.access(p, os.X_OK) else 0o644
            with open(p, "rb") as fh:
                ti = tarfile.TarInfo(arc)
                ti.size = p.stat().st_size
                ti.mode = mode
                ti.mtime = FIXED_MTIME
                ti.uid = ti.gid = 0
                ti.uname = ti.gname = "root"
                tf.addfile(ti, fh)


def targz_bytes(build) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        build(tf)
    raw = buf.getvalue()
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", mtime=FIXED_MTIME) as gz:
        gz.write(raw)
    return out.getvalue()


def make_deb(control_dir: Path, root_files, out: Path, data_builder):
    """control_dir 里放 control/postinst/... ;root_files 为 data 树内容构建函数"""
    ctl = targz_bytes(lambda tf: [add_bytes(tf, f"./{f.name}", f.read_bytes(),
                                             0o755 if f.name != "control" else 0o644)
                                  for f in sorted(control_dir.iterdir()) if f.is_file()])
    data = targz_bytes(data_builder)
    write_ar(out, [("debian-binary", b"2.0\n", 0o100644),
                   ("control.tar.gz", ctl, 0o100644),
                   ("data.tar.gz", data, 0o100644)])
    return out


# ────────────────────────────── 元信息读取 ──────────────────────────────
def cfg_version(text: str, default="1.0.0") -> str:
    """config.ini 可能是故意写坏的 JSON,所以用正则兜底。"""
    m = re.search(r'"version"\s*:\s*"([^"]+)"', text)
    return m.group(1) if m else default


def ctl_version(control: Path, default="1.0.0") -> str:
    m = re.search(r"^Version:\s*(\S+)", control.read_text(encoding="utf-8",
                                                          errors="replace"), re.M)
    return m.group(1) if m else default


# ────────────────────────────── 两种模式 ──────────────────────────────
def build_single(appid: str, plat: str) -> Path:
    arch = ARCH_MAP[plat]
    ctl_dir = Path("DEBIAN")
    ver = ctl_version(ctl_dir / "control")

    def data(tf):
        for top, prefix in ((Path("."), f"usr/local/{appid}"),):
            for name in ("config.ini", f"{appid}.lang", f"{appid}.env"):
                p = Path(name)
                if p.is_file():
                    add_bytes(tf, f"./{prefix}/{name}", p.read_bytes())
        for sub in ("images", "init.d", "bin", "nginx", "depends", "webui.bz2"):
            p = Path(sub)
            if p.is_file():
                add_bytes(tf, f"./usr/local/{appid}/{sub}", p.read_bytes())
            elif p.is_dir():
                add_tree(tf, p, f"usr/local/{appid}/{sub}")

    # 平台命名规范:<app_id>_<platform>.deb —— 不含版本号,架构用 x86_64/aarch64
    out = Path("build/output") / f"{appid}_{plat}.deb"
    out.parent.mkdir(parents=True, exist_ok=True)
    return make_deb(ctl_dir, None, out, data)


def build_dual(appid: str, plat: str) -> Path:
    arch = ARCH_MAP[plat]
    dver = ctl_version(Path("data-pkg/DEBIAN/control"))
    sver = ctl_version(Path("source-pkg/DEBIAN/control"))
    bdir = Path("build")
    ddir, sdir = bdir / "output", bdir / "output"
    ddir.mkdir(parents=True, exist_ok=True)

    # --- data 包 ---
    ddeb = ddir / f"{appid}_{dver}_{arch}.deb"

    def data_tree(tf):
        add_tree(tf, Path("data-pkg"), f"usr/local/{appid}",
                 skip=("DEBIAN",))

    make_deb(Path("data-pkg/DEBIAN"), None, ddeb, data_tree)

    # --- source 包(内含真实二进制) ---
    sdeb = sdir / f"{appid}-source_{sver}_{arch}.deb"

    def src_tree(tf):
        add_bytes(tf, f"./usr/local/{appid}/bin/{appid}",
                  (f"#!/bin/sh\n# {appid} runtime (test fixture)\n"
                   f"while true; do sleep 3600; done\n").encode(), 0o755)
        add_bytes(tf, f"./usr/local/{appid}/README",
                  f"{appid} binary package\n".encode(), 0o644)

    make_deb(Path("source-pkg/DEBIAN"), None, sdeb, src_tree)

    # --- 合并成平台归档 ---
    archive = bdir / "output" / f"{appid}_{plat}.tar.gz"
    with tarfile.open(archive, "w:gz") as tf:
        for f in (ddeb, sdeb):
            ti = tf.gettarinfo(str(f), arcname=f.name)
            ti.mtime = FIXED_MTIME
            ti.uid = ti.gid = 0
            ti.uname = ti.gname = "root"
            with open(f, "rb") as fh:
                tf.addfile(ti, fh)
    return archive


# ────────────────────────────── main ──────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--appid", required=True)
    ap.add_argument("--mode", choices=("single", "dual"), required=True)
    ap.add_argument("--platform", default="x86_64")
    a = ap.parse_args()

    if a.platform not in ARCH_MAP:
        sys.exit(f"unsupported platform: {a.platform}")

    # 清掉上次的产物,避免改名/旧文件残留
    shutil.rmtree("build", ignore_errors=True)

    out = build_single(a.appid, a.platform) if a.mode == "single" \
        else build_dual(a.appid, a.platform)

    # 平台要求:每个包配一个同名的 .sha256 文件
    #   sha256sum <package> > <package>.sha256
    # 只声明「提交给平台的那一个包」的哈希,不要把内层文件也写进去。
    odir = out.parent
    h = hashlib.sha256(out.read_bytes()).hexdigest()
    (odir / f"{out.name}.sha256").write_text(f"{h}  {out.name}\n", encoding="utf-8")

    print(f"=== Built: {out} ===")
    for f in sorted(odir.iterdir()):
        print(f"    {f.stat().st_size:>10,}  {f.name}")


if __name__ == "__main__":
    main()
