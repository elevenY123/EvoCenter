"""Install inert, date-gated presentation hooks in generated browser pages."""
import re

PAGES = ['index.html', 'evocenter.html', 'legacy.html', 'ArtMotion/index.html',
         'ArtMotion/legacy.html', 'ArtMotion/index.en.html', 'ArtMotion/legacy.en.html',
         'IslandBlur/index.html', 'IslandBlur/legacy.html']
HERO = '''<section class="event-hero" aria-labelledby="event-title">
<div class="shell event-hero-inner"><p class="event-kicker">GTA VI · 10-DAY EDITION <span class="event-preview">预览</span></p>
<h2 class="event-title" id="event-title">VICE CITY<br><span>AFTER HOURS.</span></h2>
<p class="event-description">把霓虹，带进你的 iOS。<br>三款插件，一起换上罪恶都市限定外观。</p>
<div class="event-period"><strong>11.10 — 11.20</strong><span>北京时间 · 十日限定</span><a href="https://www.rockstargames.com/VI" target="_blank" rel="noreferrer">GTA VI ↗</a></div></div>
</section>'''

def install(root):
    for file in PAGES:
        path = root / file
        content = path.read_text(encoding='utf-8')
        original = content
        prefix = '../' if '/' in file else ''
        if 'site/event-theme.js' not in content:
            hook = f'<link rel="stylesheet" href="{prefix}site/event-theme.css"><script src="{prefix}site/event-theme.js"></script>'
            content = content.replace('</head>', hook + '</head>', 1)
        if file == 'index.html':
            if 'class="event-hero"' not in content:
                content = content.replace('</header>', '</header>\n' + HERO, 1)
        elif 'data-page="detail"' not in content:
            content = re.sub(r'<html([^>]*)>', r'<html\1 data-page="detail">', content, count=1)
        if content != original:
            path.write_bytes(content.encode())

if __name__ == '__main__':
    from pathlib import Path
    install(Path(__file__).resolve().parents[1])
