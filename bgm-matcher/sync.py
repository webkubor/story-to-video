#!/usr/bin/env python3
"""同步热门音乐榜单 → web-assets manifest + R2。
在 web-assets 项目根目录执行，自动从 music-matcher 拉最新数据。"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

HOT_INDEX = Path.home() / "music-matcher/bgm-index.json"
MANIFEST = Path("manifest/music.json")

# 同步阈值：只同步热度分 > 此值的音乐（减少噪音）
MIN_SCORE = 15
TOP_PER_EMOTION = 20


def build():
    if not HOT_INDEX.exists():
        print("❌ music-matcher 曲库不存在，先: cd ~/music-matcher && python hot.py fetch")
        sys.exit(1)

    bgm = json.loads(HOT_INDEX.read_text())
    tracks = bgm["tracks"]

    # 按热度过滤
    hot = [t for t in tracks if t["score"] >= MIN_SCORE]

    # 按情绪分组 TOP20
    by_emo = {}
    for t in tracks:
        for e in t["emotions"]:
            if e not in by_emo:
                by_emo[e] = []
            by_emo[e].append(t["title"])

    manifest = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(hot),
        "cdn": "https://music.webkubor.online/",
        "source": "网易云音乐实时热歌榜",
        "min_score": MIN_SCORE,
        "charts": {
            "hot": sorted(hot, key=lambda x: x["score"], reverse=True),
        },
        "by_emotion": {e: songs[:TOP_PER_EMOTION] for e, songs in by_emo.items()},
    }

    MANIFEST.parent.mkdir(exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"✅ music.json → {len(hot)} 首 (热度>{MIN_SCORE})")


def push():
    """Git 提交 + 推送"""
    result = subprocess.run(
        ["git", "add", str(MANIFEST), "&&", "git", "commit", "-m",
         f"sync: [music-matcher] 热门音乐榜单 {datetime.now().strftime('%m-%d')}",
         "&&", "git", "push"],
        shell=True, capture_output=True, text=True, timeout=30
    )
    print(result.stdout.strip() or "✅ 已推送")
    if result.stderr.strip():
        print(result.stderr.strip()[-200:])


def sync_r2():
    """同步到 R2 CDN（需要 wrangler）"""
    r = subprocess.run(
        ["bash", "sync.sh", "music"],
        capture_output=True, text=True, timeout=30
    )
    if r.returncode == 0:
        print("📦 R2 同步完成 → https://music.webkubor.online/manifest.json")
    else:
        print(f"⚠️ R2 同步跳过: {r.stderr.strip()[-100:]}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"

    if cmd == "build":
        build()
        print("下一步: python sync.py push   # Git提交")
    elif cmd == "push":
        build()
        push()
    elif cmd == "full":
        build()
        push()
        sync_r2()
    else:
        print("python sync.py build  生成manifest")
        print("python sync.py push   Git提交推送")
        print("python sync.py full   生成+推送+R2同步")
