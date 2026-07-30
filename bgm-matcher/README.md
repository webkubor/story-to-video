# 🎵 配乐 BGM Matcher

> **Skills Hub 商业技能** — 给视频自动匹配当下最火的背景音乐。
> 网易云 6 大歌单实时拉取 + 热度评分 + 情绪分类，537 首热门歌曲随取随用。

## 为什么这个是值钱的 Skills？

做视频最头疼的是找 BGM。大多数人翻网易云/抖音翻半天，找到的歌要么不搭、要么用烂了。这个 Skill 一步解决：

- 🎯 **文案直接出配乐**：输入"治愈猫咪日常" → 返回最匹配的热门歌曲
- 🔥 **按热度排序**：热歌榜 TOP1 分数 148.5，只推荐真正火的歌
- 🏷️ **情绪精准匹配**：覆盖温馨/治愈/欢快/悲伤/浪漫/酷炫/古风/动感等
- ⚡ **零门槛**：不需要 API Key，不需要注册任何平台
- 🔄 **每周自动刷新**：曲库跟着热歌榜实时更新

**目标用户**：短视频创作者、vlogger、剪辑师、内容运营。

---

## 两项目协同

| 项目 | 定位 | 仓库 |
|------|------|------|
| **music-matcher** | 🛒 Skills Hub 技能 — 拉取+匹配+推荐 | `webkubor/music-matcher` |
| **web-assets** | 🗄️ 静态资源库 — 音乐/图片/字体 CDN | `webkubor/web-assets` |

```
music-matcher（Skills）          web-assets（资源库）
  ┌──────────────┐               ┌──────────────┐
  │ hot.py fetch │──拉取网易云──→│ manifest/     │
  │ hot.py match │  热度评分     │ music.json    │
  │ sync.py      │──同步推送──→│   ↓           │
  └──────────────┘               │ git push      │
                                  │   ↓           │
                                  │ R2 CDN        │
                                  │ music.😊.online│
                                  └──────────────┘
```

- **卖 Skills** → 用户买 music-matcher，拿到配乐推荐能力
- **自己用** → web-assets 直接读 R2 CDN，任何项目都能拉音乐清单

---

## 快速开始

```bash
# 拉取曲库
python hot.py fetch

# 匹配配乐
python hot.py match "治愈温馨的猫咪日常"
python hot.py match "古风旅拍汉服"
python hot.py match "燃向卡点混剪"

# 查看曲库统计
python hot.py list
```

## 同步到资源库

```bash
cd ~/web-assets
python ~/music-matcher/sync.py full
# → manifest/music.json 更新 → Git 推送 → R2 CDN 同步
# → https://music.webkubor.online/manifest.json 可公开访问
```

## 情绪标签

`温馨` `治愈` `欢快` `悲伤` `浪漫` `酷炫` `古风` `清新` `动感` `史诗` `搞笑`

## 搜索关键词

`配乐` `背景音乐` `BGM` `视频配乐` `音乐推荐` `情绪匹配` `短视频` `抖音` `视频号` `小红书` `Vlog` `卡点` `混剪` `热门歌曲` `网易云` `AI配乐` `智能推荐` `一键配乐` `剪辑必备` `内容创作` `后期制作`

## 文件说明

| 文件 | 功能 |
|------|------|
| `hot.py` | 核心引擎：拉取+热度评分+情绪匹配 |
| `sync.py` | 同步到 web-assets 资源库 + R2 CDN |
| `download.py` | 下载 Pixabay 免费可商用 BGM（可选） |
| `SKILL.md` | Skills Hub 技能定义 |
