#!/usr/bin/env python3
"""从 Pixabay Music 下载免费可商用BGM。需要 API Key（pixabay.com 免费注册即得）。"""

import json
import os
import sys
import urllib.request
from pathlib import Path

MUSIC_DIR = Path(__file__).parent / "music"
PIXABAY_URL = "https://pixabay.com/api/music/"

# 情绪 → Pixabay 搜索词
MOOD_SEARCH = {
    "温馨": "warm gentle peaceful",
    "治愈": "healing calm soothing relaxing",
    "欢快": "happy upbeat cheerful joyful",
    "悲伤": "sad melancholy emotional nostalgic",
    "浪漫": "romantic love sentimental tender",
    "酷炫": "powerful energetic intense",
    "古风": "traditional oriental folk chinese",
    "清新": "fresh nature acoustic ambient",
    "动感": "energetic dynamic electronic pop",
    "史诗": "epic cinematic orchestral powerful",
    "搞笑": "funny comedy quirky playful",
}


def get_key():
    key = os.environ.get("PIXABAY_API_KEY", "")
    if key:
        return key
    try:
        import subprocess
        r = subprocess.run(
            ["python3", str(Path.home() / "CortexOS/pkg/infra/secretvault/standalone.py"),
             "get", "secret://pixabay/api-key"],
            capture_output=True, text=True, timeout=10)
        key = r.stdout.strip().split("\n")[-1] if r.stdout.strip() else ""
    except Exception:
        pass
    return key


def search(key, mood="温馨", page=1, per_page=10):
    query = MOOD_SEARCH.get(mood, "background music")
    url = f"{PIXABAY_URL}?key={key}&q={query}&page={page}&per_page={per_page}"
    req = urllib.request.Request(url, headers={"User-Agent": "music-matcher/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "music-matcher/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        path.write_bytes(resp.read())


def build_library(key, per_mood=5):
    """按情绪拉音乐 + 下载"""
    MUSIC_DIR.mkdir(exist_ok=True)
    tracks = []
    for mood, query in MOOD_SEARCH.items():
        print(f"🎵 {mood} ({query})...", end=" ", flush=True)
        try:
            r = search(key, mood, per_page=per_mood)
            for hit in r.get("hits", [])[:per_mood]:
                tracks.append({
                    "title": hit.get("title", ""),
                    "mood": mood,
                    "duration": hit.get("duration", 0),
                    "url": hit.get("previewURL", hit.get("audio", "")),
                    "file": f"music/{hit['id']}.mp3",
                    "id": str(hit["id"]),
                })
            print(f"{len(r.get('hits',[]))} 首")
        except Exception as e:
            print(f"❌ {e}")

    # 下载所有
    total = len(tracks)
    for i, t in enumerate(tracks):
        f = MUSIC_DIR / f"{t['id']}.mp3"
        if f.exists():
            continue
        print(f"[{i+1}/{total}] {t['title'][:35]}...", end=" ", flush=True)
        try:
            download(t["url"], f)
            print("✅")
        except Exception as e:
            print(f"❌ {e}")

    # 保存索引
    index = {"tracks": tracks, "total": len(tracks)}
    (Path(__file__).parent / "bgm-library.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2))
    print(f"\n✅ 曲库 {len(tracks)} 首 → bgm-library.json + music/")


if __name__ == "__main__":
    key = get_key()
    if not key:
        print("❌ 需要 Pixabay API Key")
        print("   1. 去 https://pixabay.com/api/docs/ 注册（免费）")
        print("   2. cs secrets set secret://pixabay/api-key YOUR_KEY")
        print("   3. 重新运行 python download.py")
        sys.exit(1)

    mood = sys.argv[1] if len(sys.argv) > 1 else None
    if mood:
        r = search(key, mood)
        for h in r.get("hits", [])[:5]:
            print(f"  {h['title'][:40]} | {h.get('duration',0)}s")
    else:
        build_library(key)
