"""Build the repository's browser catalog from published release metadata.

Run from any directory: python3 Tools/build-homepage.py
Then run Tools/export-homepage-previews.ps1 if preview assets are new.
The APT index update is deliberately separate from this presentation builder.
"""
from pathlib import Path
from html import escape
import json

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
SITE.mkdir(exist_ok=True)
read = lambda path: json.loads((ROOT / path).read_text())
evo, art, island = read('release.json'), read('ArtMotion/release.json'), read('IslandBlur/release.json')

original = ROOT / 'evocenter.html'
if not original.exists():
    content = (ROOT / 'index.html').read_text()
    assert '<title>Evo Center</title>' in content, 'Expected original Evo Center depiction before migration'
    original.write_text(content)

# Keep browser navigation separate from package-manager depictions.
detail_pages = {'evocenter.html': './', 'legacy.html': './', 'IslandBlur/index.html': '../',
                'ArtMotion/index.html': '../', 'ArtMotion/legacy.html': '../',
                'ArtMotion/index.en.html': '../', 'ArtMotion/legacy.en.html': '../'}
legacy_island = ROOT / 'IslandBlur/legacy.html'
if not legacy_island.exists():
    content = (ROOT / 'IslandBlur/index.html').read_text()
    content = content.replace('<title>IslandBlur</title>', '<title>IslandBlur (Legacy)</title>')
    content = content.replace('<h1>IslandBlur</h1>', '<h1>IslandBlur (Legacy)</h1>')
    content = content.replace('<footer>IslandBlur ·', '<footer>IslandBlur (Legacy) ·')
    content = content.replace('<dt>版本</dt>', '<dt>设备架构</dt><dd>arm64</dd><dt>版本</dt>')
    legacy_island.write_text(content)
detail_pages['IslandBlur/legacy.html'] = '../'
for file, back in detail_pages.items():
    path = ROOT / file
    content = path.read_text()
    if 'class="repo-back"' not in content:
        content = content.replace('<main>', f'<main><a class="repo-back" href="{back}" style="display:inline-flex;align-items:center;gap:6px;min-height:44px;margin-bottom:12px;font-size:14px;color:#507da8">← 所有插件</a>', 1)
        path.write_text(content)

apps = [
    {'id': 'evocenter', 'name': 'Evo Center', 'subtitle': '重新设计你的控制中心',
     'description': '自由组合模块、调整尺寸与分页，把 HomeKit、专注模式和快捷指令放在顺手的位置。',
     'version': evo['releaseLabel'].replace('测试版', ''), 'os': 'iOS 16.0–17.4', 'category': '控制中心',
     'keywords': 'control center homekit focus shortcuts 模块 自定义 分页', 'page': 'evocenter.html', 'legacy': 'legacy.html',
     'iconSource': 'assets/icon.png', 'package': evo['package'], 'legacyPackage': evo['legacyPackage'],
     'screenshots': [{'file': s['path'], 'width': s['width'], 'height': s['height'], 'alt': s['accessibilityText']} for s in evo['screenshots']]},
    {'id': 'artmotion', 'name': 'ArtMotion', 'subtitle': '让专辑封面融入整个屏幕',
     'description': '音乐播放页与锁屏的沉浸式专辑封面。自然延展画面边缘，支持 Apple Music 动态封面与 iPad 布局。',
     'version': art['releaseLabel'], 'os': 'iOS / iPadOS 16–17', 'category': '音乐与锁屏',
     'keywords': 'music album artwork lock screen animated 动态 专辑 封面 音乐 锁屏', 'page': 'ArtMotion/', 'legacy': 'ArtMotion/legacy.html',
     'iconSource': 'ArtMotion/assets/icon.png', 'package': art['variants'][0]['package'], 'legacyPackage': art['variants'][1]['package'],
     'screenshots': [{'file': 'ArtMotion/' + s['file'], 'width': s['width'], 'height': s['height'], 'alt': f"ArtMotion 截图 {s['order']}：{s['caption']}"} for s in art['screenshots']]},
    {'id': 'islandblur', 'name': 'IslandBlur', 'subtitle': '灵动岛，也可以更轻盈',
     'description': '为灵动岛实时活动加入柔和渐变、高斯模糊与液态玻璃材质，让展开卡片更自然地融入界面。',
     'version': island['releaseLabel'].replace('beta', 'Beta'), 'os': 'iOS 16–17', 'category': '灵动岛',
     'keywords': 'dynamic island live activities blur glass 透明 模糊 液态玻璃 实时活动', 'page': 'IslandBlur/', 'legacy': 'IslandBlur/legacy.html',
     'iconSource': 'IslandBlur/assets/icon.png', 'package': island['variants'][0]['package'], 'legacyPackage': island['variants'][1]['package'],
     'screenshots': [{'file': 'IslandBlur/' + s['path'], 'width': s['width'], 'height': s['height'], 'alt': s['accessibilityText']} for s in island['screenshots']]}
]

jobs = []
for app in apps:
    app['icon'] = f"site/icons/{app['id']}.png"
    jobs.append({'source': app['iconSource'], 'output': app['icon'], 'width': 192, 'format': 'png'})
    for number, shot in enumerate(app['screenshots'], 1):
        wide = shot['width'] > shot['height']
        widths = (1024, 1536) if wide else (480, 960)
        for width in widths:
            jobs.append({'source': shot['file'], 'output': f"site/previews/{app['id']}/{number}-{width}.jpg", 'width': width, 'format': 'jpg'})
        shot['preview'] = f"site/previews/{app['id']}/{number}-{widths[0]}.jpg"
        shot['srcset'] = ', '.join(f"site/previews/{app['id']}/{number}-{width}.jpg {width}w" for width in widths)
        shot['sizes'] = '(max-width: 700px) 370px, (min-width: 1200px) 488px, 455px' if wide else '(max-width: 700px) 139px, (min-width: 1200px) 184px, 171px'
(SITE / 'preview-jobs.json').write_text(json.dumps(jobs, ensure_ascii=False, indent=2) + '\n')
(SITE / 'catalog.json').write_text(json.dumps({'source': 'https://eleveny123.github.io/', 'apps': apps}, ensure_ascii=False, indent=2) + '\n')

def svg(name, size=16):
    paths = {'search': '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/>',
             'arrow': '<path d="m9 5 7 7-7 7"/>', 'left': '<path d="m15 5-7 7 7 7"/>',
             'phone': '<rect x="6" y="2" width="12" height="20" rx="3"/><path d="M10 18h4"/>',
             'tag': '<path d="M20 13 12 21 3 12V3h9l8 8a1.4 1.4 0 0 1 0 2Z"/><circle cx="7.5" cy="7.5" r=".7"/>',
             'version': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
             'copy': '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M15 8V3H3v12h5"/>',
             'plus': '<path d="M12 5v14M5 12h14"/>', 'close': '<path d="m6 6 12 12M6 18 18 6"/>',
             'swipe': '<path d="M3 12h18M7 8l-4 4 4 4m10-8 4 4-4 4"/>'}
    return f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[name]}</svg>'

def card(app, index):
    name = escape(app['name'])
    search = escape(' '.join(str(app[k]) for k in ('name', 'subtitle', 'description', 'category', 'keywords')), quote=True)
    shots = []
    for number, s in enumerate(app['screenshots'], 1):
        loading = 'loading="eager" fetchpriority="high"' if index == 0 and number == 1 else 'loading="lazy"'
        shots.append(f'<a class="shot" href="{s["file"]}" aria-label="放大{name}截图{number}"><img src="{s["preview"]}" srcset="{s["srcset"]}" sizes="{s["sizes"]}" width="{s["width"]}" height="{s["height"]}" alt="{escape(s["alt"], quote=True)}" {loading} decoding="async"></a>')
    return f'''<article class="tweak" id="{app['id']}" aria-labelledby="{app['id']}-name" data-search="{search}">
      <div class="tweak-header"><a href="{app['page']}" tabindex="-1" aria-hidden="true"><img class="app-icon" src="{app['icon']}" width="76" height="76" alt="" decoding="async"></a>
        <div><h2 id="{app['id']}-name"><a href="{app['page']}">{name}</a></h2><p class="app-subtitle">{app['subtitle']}</p></div>
        <div class="app-actions"><a class="detail-link" href="{app['page']}" aria-label="查看{name}详情">查看详情{svg('arrow',12)}</a><a class="legacy-link" href="{app['legacy']}" aria-label="查看{name} Legacy 版本">Legacy 版</a></div></div>
      <p class="description">{app['description']}</p>
      <div class="meta"><span class="meta-item">{svg('phone',13)}{app['os']}</span><span class="meta-separator"></span><span class="meta-item">{svg('tag',13)}{app['category']}</span><span class="meta-separator"></span><span class="meta-item">{svg('version',13)}{app['version']}</span></div>
      <div class="gallery"><div class="shots" role="region" aria-label="{name}截图，可横向滑动" tabindex="0">{''.join(shots)}</div>
        <div class="gallery-footer"><span class="gallery-hint">{svg('swipe',14)}滑动浏览 · 点击放大</span><div class="gallery-controls"><button type="button" data-direction="-1" aria-label="{name}上一组截图">{svg('left',14)}</button><button type="button" data-direction="1" aria-label="{name}下一组截图">{svg('arrow',14)}</button></div></div></div>
    </article>'''

document = f'''<!doctype html>
<html lang="zh-CN" data-source="https://eleveny123.github.io/">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="color-scheme" content="light dark"><meta name="theme-color" content="#f6f7f9" media="(prefers-color-scheme:light)"><meta name="theme-color" content="#101113" media="(prefers-color-scheme:dark)">
<title>JaySuen Repo · 越狱插件</title><meta name="description" content="浏览 Evo Center、ArtMotion 和 IslandBlur。预览实机截图，发现控制中心、沉浸式封面与灵动岛的更多可能，一键添加到 Sileo 或 Zebra。"><link rel="canonical" href="https://eleveny123.github.io/"><link rel="icon" type="image/png" href="CydiaIcon.png"><link rel="apple-touch-icon" href="CydiaIcon.png"><meta property="og:title" content="JaySuen Repo"><meta property="og:description" content="三款插件，让你的 iOS 更合心意。"><meta property="og:image" content="https://eleveny123.github.io/CydiaIcon.png"><link rel="stylesheet" href="site/site.css"><script src="site/site.js" defer></script></head>
<body><a class="skip" href="#plugins">跳到插件列表</a>
<header class="topbar"><div class="shell topbar-inner"><a class="brand" href="./" aria-label="JaySuen Repo 首页"><img src="CydiaIcon.png" width="36" height="36" alt="">JaySuen Repo</a><nav class="topnav" aria-label="网站导航"><a href="#plugins">浏览插件</a><a href="#feedback">反馈与建议</a></nav></div></header>
<main class="shell"><section class="intro" aria-labelledby="page-title"><p class="eyebrow">MADE FOR YOUR IOS</p><div class="intro-row"><div><h1 id="page-title">让 iOS，更合心意。</h1><p class="subtitle"><span id="result-count" aria-live="polite">3 款插件</span> · 从控制中心，到你喜欢的每一处细节。</p></div><label class="search" for="search">{svg('search',19)}<input id="search" type="search" placeholder="搜索插件或功能" aria-label="搜索插件或功能" autocomplete="off"></label></div></section>
<section class="catalog" id="plugins" aria-label="插件列表">{''.join(card(app,index) for index,app in enumerate(apps))}</section>
<section class="empty" id="empty" hidden><strong>没有找到相关插件</strong><p>试试“音乐”“控制中心”或“灵动岛”。</p><button id="clear-search" type="button">查看全部插件</button></section>
<footer class="page-footer" id="feedback"><p>JaySuen Repo · Rootless / RootHide<br>反馈：酷安搜索 JAYSuen 私信，或在插件最新帖子评论。</p><a href="https://www.coolapk.com/" rel="noreferrer">前往酷安 ↗</a></footer></main>
<aside class="source-bar" aria-label="添加软件源"><div class="source-inner"><div class="source-info"><strong>添加软件源，开始体验。</strong><div class="source-address"><span>eleveny123.github.io</span><button class="copy-source" id="copy-source" type="button" aria-label="复制源地址 https://eleveny123.github.io/">{svg('copy',12)}复制源地址</button></div></div><div class="source-buttons"><a class="source-button sileo" href="sileo://source/https://eleveny123.github.io/">{svg('plus',18)}添加到 Sileo</a><a class="source-button zebra" href="zbra://sources/add/https://eleveny123.github.io/">{svg('plus',18)}添加到 Zebra</a></div></div></aside>
<div class="toast" id="toast" role="status" aria-live="polite" hidden></div>
<dialog class="lightbox" id="lightbox" aria-labelledby="lightbox-title" aria-describedby="lightbox-caption"><div class="lightbox-head"><strong id="lightbox-title">实机截图</strong><button type="button" data-close aria-label="关闭截图">{svg('close',18)}</button></div><div class="lightbox-media"><button type="button" data-previous aria-label="上一张截图">{svg('left',22)}</button><img class="lightbox-image" alt=""><button type="button" data-next aria-label="下一张截图">{svg('arrow',22)}</button></div><p id="lightbox-caption" class="lightbox-caption"></p></dialog>
</body></html>
'''
(ROOT / 'index.html').write_text(document)
from event_presentation import install
install(ROOT)
print(f'Built repository homepage: {len(apps)} products, {sum(len(a["screenshots"]) for a in apps)} ordered screenshots, {len(jobs)} preview assets.')
