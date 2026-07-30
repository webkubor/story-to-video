#!/usr/bin/env python3
"""热门BGM推荐 — 网易云实时热歌榜 + 热度评分 + 情绪匹配。"""

import json
import sys
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta

DATA_DIR = Path(__file__).parent
INDEX_FILE = DATA_DIR / "bgm-index.json"
CACHE_FILE = DATA_DIR / ".cache.json"

PLAYLISTS = {
    "热歌榜":  ("3778678",   ["动感", "欢快"]),
    "新歌榜":  ("3779629",   ["清新", "动感"]),
    "原创榜":  ("2884035",   ["治愈", "清新"]),
    "说唱榜":  ("19723756",  ["酷炫", "动感"]),
    "抖音榜":  ("2250011882",["动感", "欢快"]),
    "电音榜":  ("1978921795",["动感", "酷炫"]),
}

TITLE_MOOD = {
    "温馨": ["温柔", "温暖", "阳光", "日常", "生活", "幸福", "微笑", "甜蜜", "家", "慢", "晚安"],
    "治愈": ["治愈", "钢琴", "吉他", "舒缓", "纯", "安静", "冥想", "睡觉", "眠", "轻", "空"],
    "欢快": ["快乐", "欢快", "开心", "跳跃", "活泼", "元气", "嗨", "fun", "party", "舞"],
    "悲伤": ["悲伤", "伤感", "难过", "眼泪", "分手", "遗憾", "Emo", "哭", "痛", "离"],
    "浪漫": ["浪漫", "恋爱", "告白", "婚礼", "花", "星", "约定", "甜", "喜欢", "心"],
    "酷炫": ["卡点", "节奏", "转场", "混剪", "燃", "炸", "bang", "rap", "hip", "trap"],
    "古风": ["古风", "国风", "戏腔", "民乐", "江湖", "侠", "长安", "琵琶", "笛", "琴"],
    "史诗": ["大气", "史诗", "电影", "弦乐", "交响", "纪录片", "战", "荣耀", "征"],
    "清新": ["清新", "自然", "旅行", "夏天", "风", "旅途", "森", "海", "云", "路"],
    "动感": ["运动", "健身", "街舞", "电子", "pop", "流行", "抖", "摇", "晃", "跳"],
    "搞笑": ["搞笑", "鬼畜", "沙雕", "魔性", "欢乐", "哈哈", "笑"],
}

def fetch_playlist(pid):
    url = f"https://music.163.com/api/playlist/detail?id={pid}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "Referer": "https://music.163.com/",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read()).get("result", {}).get("tracks", [])
    except Exception as e:
        print(f"  ⚠️ {e}")
        return []


def classify(title, base_moods):
    t = title.lower()
    extra = [m for m, kws in TITLE_MOOD.items() if any(kw in t for kw in kws)]
    result = base_moods.copy()
    for e in extra:
        if e not in result:
            result.append(e)
    return result


def hot_score(rank, playlist_weight=1.0):
    """热度评分：排名越前分越高，热歌榜权重更高"""
    base = max(0, 100 - rank)  # rank 1 → 99分, rank 100 → 0分
    return base * playlist_weight


def build_index(force=False):
    if CACHE_FILE.exists() and not force:
        cache = json.loads(CACHE_FILE.read_text())
        last = datetime.fromisoformat(cache.get("last_fetch", "2000-01-01"))
        if datetime.now() - last < timedelta(hours=12):
            print(f"📦 缓存 ({last.strftime('%m-%d %H:%M')})，跳过")
            return INDEX_FILE

    # 歌单权重：热歌榜/抖音榜权重大
    WEIGHTS = {"热歌榜": 1.5, "抖音榜": 1.3, "新歌榜": 1.0, "原创榜": 0.8, "说唱榜": 1.0, "电音榜": 0.8}

    index = {"version": datetime.now().isoformat(), "tracks": [], "stats": {}}
    seen = set()

    for name, (pid, base_moods) in PLAYLISTS.items():
        print(f"🎵 {name}...", end=" ", flush=True)
        tracks = fetch_playlist(pid)
        print(f"{len(tracks)} 首")
        w = WEIGHTS.get(name, 1.0)
        for rank, t in enumerate(tracks):
            title = t.get("name", "").strip()
            if not title or title in seen:
                continue
            seen.add(title)
            score = hot_score(rank + 1, w)
            index["tracks"].append({
                "title": title,
                "source": "wyy",
                "playlist": name,
                "rank": rank + 1,
                "score": round(score, 1),
                "emotions": classify(title, base_moods),
            })

    # 按热度分降序
    index["tracks"].sort(key=lambda x: x["score"], reverse=True)
    index["stats"]["total"] = len(index["tracks"])

    emo_count = {}
    for t in index["tracks"]:
        for e in t["emotions"]:
            emo_count[e] = emo_count.get(e, 0) + 1
    index["stats"]["by_emotion"] = emo_count
    index["stats"]["top_score"] = index["tracks"][0]["score"] if index["tracks"] else 0

    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2))
    CACHE_FILE.write_text(json.dumps({"last_fetch": datetime.now().isoformat()}))

    print(f"\n✅ {index['stats']['total']} 首 (最高热度: {index['stats']['top_score']})")
    for e, c in sorted(emo_count.items(), key=lambda x: -x[1]):
        print(f"  {e}: {c}")


def match(text, top_n=8, min_score=0):
    if not INDEX_FILE.exists():
        print("❌ 先 python hot.py fetch")
        return []

    index = json.loads(INDEX_FILE.read_text())
    tracks = index["tracks"]

    desired = [m for m, kws in TITLE_MOOD.items() if any(kw in text for kw in kws)]
    if not desired:
        desired = ["清新", "动感"]

    print(f"🔍 「{text}」→ {', '.join(desired)}")
    print(f"📊 曲库 {len(tracks)} 首\n")

    scored = []
    for t in tracks:
        base = t["emotions"][:2]
        extra = t["emotions"][2:]
        s = sum(2 for e in desired if e in base) + sum(1 for e in desired if e in extra)
        if s and t["score"] >= min_score:
            scored.append((s * 10 + t["score"] / 10, t))

    scored.sort(key=lambda x: x[0], reverse=True)

    for _, t in scored[:top_n]:
        emo = ','.join(t['emotions'])
        print(f"  🔥{t['score']:5.1f} {t['title'][:30]:30s} | {emo:22s} | {t['playlist']}")

    return [t for _, t in scored[:top_n]]


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "match"
    arg = sys.argv[2] if len(sys.argv) > 2 else "治愈日常"

    if cmd in ("fetch", "weekly"):
        build_index(force=True)
    elif cmd == "match":
        match(arg)
    elif cmd == "list":
        if INDEX_FILE.exists():
            index = json.loads(INDEX_FILE.read_text())
            for e, c in sorted(index["stats"]["by_emotion"].items(), key=lambda x: -x[1]):
                print(f"{e}: {c}首")
    else:
        print("python hot.py fetch     拉热门+算热度")
        print("python hot.py match 'xx'  推荐配乐")
        print("python hot.py list        曲库统计")
