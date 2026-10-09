# -*- coding: utf-8 -*-
"""
Silk Touch Budding Amethyst —— 打包脚本

把 sources/ 下的数据文件同时打成三种形态（内容完全一致）：

  1. Fabric 模组 .jar      -> 放到 mods/          （Fabric 服务端 / 客户端都能用）
  2. 数据包文件夹          -> 放到 world/datapacks/（任何服务端、任何加载器都能用）
  3. 数据包 .zip           -> 同上，压缩形态

用法：
    python build.py
    python build.py --out "D:\\somewhere"     # 自定义产物目录
"""

import argparse
import json
import os
import sys
import zipfile

try:
    sys.stdout.reconfigure(errors="replace")
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "sources")
MODID = "silk_touch_budding_amethyst"
VERSION = "1.0.0"
# 数据包里被“覆盖”的原版文件：必须与它同名同路径才会生效
LOOT_PATH = "data/minecraft/loot_table/blocks/budding_amethyst.json"


def build(out_dir):
    if not os.path.isdir(SRC):
        raise SystemExit("缺少 sources/ 目录")

    payload = []  # [(相对路径, 文本内容)]
    for dirpath, _dirs, files in os.walk(SRC):
        for name in files:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, SRC).replace("\\", "/")
            with open(full, "r", encoding="utf-8") as f:
                payload.append((rel, f.read()))
    payload.sort()

    # 语法门禁：任何一个 JSON 坏掉，装进游戏就是“安全错误”，必须拦在打包前
    for rel, text in payload:
        if rel.endswith(".json"):
            json.loads(text)
    assert any(rel == LOOT_PATH for rel, _ in payload), "缺少掉落表：" + LOOT_PATH

    mod_json = json.load(open(os.path.join(ROOT, "fabric.mod.json"), encoding="utf-8"))
    pack_json = json.load(open(os.path.join(ROOT, "pack.mcmeta"), encoding="utf-8"))
    loot_text = dict(payload)[LOOT_PATH]
    loot = json.loads(loot_text)
    conds = loot["pools"][0]["conditions"]
    assert any(c.get("condition") == "minecraft:match_tool" for c in conds), "掉落条件里没有 match_tool"
    assert loot["pools"][0]["entries"][0]["name"] == "minecraft:budding_amethyst"

    os.makedirs(out_dir, exist_ok=True)
    outputs = []

    # ---------- 1. Fabric 模组 ----------
    jar_path = os.path.join(out_dir, "%s-%s.jar" % (MODID, VERSION))
    with zipfile.ZipFile(jar_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("fabric.mod.json", json.dumps(mod_json, ensure_ascii=False, indent=2))
        for rel, text in payload:
            z.writestr(rel, text)
    outputs.append(jar_path)

    # ---------- 2. 数据包文件夹 ----------
    dp_name = "%s-datapack" % MODID
    dp_dir = os.path.join(out_dir, dp_name)
    for dirpath, _dirs, files in os.walk(dp_dir, topdown=False):
        for name in files:
            os.remove(os.path.join(dirpath, name))
        os.rmdir(dirpath) if not os.listdir(dirpath) else None
    for rel, text in payload:
        dst = os.path.join(dp_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    with open(os.path.join(dp_dir, "pack.mcmeta"), "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(pack_json, ensure_ascii=False, indent=2))
    outputs.append(dp_dir)

    # ---------- 3. 数据包 zip ----------
    zip_path = os.path.join(out_dir, "%s-%s-datapack.zip" % (MODID, VERSION))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("pack.mcmeta", json.dumps(pack_json, ensure_ascii=False, indent=2))
        for rel, text in payload:
            z.writestr(rel, text)
    outputs.append(zip_path)

    print("=" * 60)
    print("载荷文件：")
    for rel, _ in payload:
        print("   " + rel)
    for p in outputs:
        print(("DIR  " if os.path.isdir(p) else "FILE ") + p)
    # 回读自检
    with zipfile.ZipFile(jar_path) as z:
        names = z.namelist()
        assert "fabric.mod.json" in names and LOOT_PATH in names
        rt = json.loads(z.read(LOOT_PATH).decode("utf-8"))
        assert rt["pools"][0]["entries"][0]["name"] == "minecraft:budding_amethyst"
    with zipfile.ZipFile(zip_path) as z:
        assert "pack.mcmeta" in z.namelist() and LOOT_PATH in z.namelist()
    print("自检通过：两种形态都含目标掉落表，JSON 全部可解析")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"), help="产物输出目录")
    args = ap.parse_args()
    build(os.path.abspath(args.out))


if __name__ == "__main__":
    main()
