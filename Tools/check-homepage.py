"""Browser regression checks for the repository catalog; saves inspectable screenshots."""
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread
import json
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'site-check-artifacts'
OUT.mkdir(exist_ok=True)
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(ROOT)))
Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/'
results = []
scripts_disabled_passed = False
catalog = json.loads((ROOT / 'site/catalog.json').read_text())['apps']
assert catalog[0]['version'] == json.loads((ROOT / 'release.json').read_text())['releaseLabel'].replace('测试版','')
assert catalog[1]['version'] == json.loads((ROOT / 'ArtMotion/release.json').read_text())['releaseLabel']
assert catalog[2]['version'].lower() == json.loads((ROOT / 'IslandBlur/release.json').read_text())['releaseLabel'].lower()
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for name, width, height, scheme in [('iphone',390,844,'light'), ('small-phone',320,740,'light'),
                ('ipad',820,1180,'light'), ('desktop',1440,1050,'light'), ('iphone-dark',390,844,'dark')]:
            context = browser.new_context(viewport={'width':width,'height':height}, device_scale_factor=2, color_scheme=scheme, reduced_motion='reduce', permissions=['clipboard-read','clipboard-write'])
            page = context.new_page()
            errors, missing = [], []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.on('response', lambda r: missing.append(r.url) if r.status >= 400 else None)
            page.goto(url, wait_until='networkidle')
            page.locator('.tweak').last.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            page.evaluate('window.scrollTo(0,0)')
            assert page.locator('.tweak').count() == 3
            assert page.locator('.shot').count() == 19
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), name
            assert page.locator('.source-button.sileo').get_attribute('href') == 'sileo://source/https://eleveny123.github.io/'
            assert page.locator('.source-button.zebra').get_attribute('href') == 'zbra://sources/add/https://eleveny123.github.io/'
            assert page.locator('.source-button.sileo').is_visible() and page.locator('.source-button.zebra').is_visible()
            assert page.locator('.source-button.sileo').bounding_box()['height'] >= 44
            for selector in ('.tweak-header', '.app-actions', '.search'):
                for box in page.locator(selector).all():
                    bounds = box.bounding_box()
                    assert bounds['x'] >= 0 and bounds['x'] + bounds['width'] <= width + 1, (name, selector, bounds)
            page.screenshot(path=str(OUT / f'{name}.png'), full_page=True)
            page.screenshot(path=str(OUT / f'{name}-viewport.png'))
            page.locator('#search').fill('音乐')
            assert page.locator('.tweak:visible').count() == 1 and page.locator('#artmotion').is_visible()
            page.locator('#search').fill('unmatched-keyword')
            assert page.locator('#empty').is_visible()
            page.locator('#clear-search').click()
            assert page.locator('.tweak:visible').count() == 3
            page.locator('.shot').first.click()
            assert page.locator('#lightbox').is_visible()
            page.locator('#lightbox img').wait_for(state='visible')
            page.wait_for_function("document.querySelector('#lightbox img').complete && document.querySelector('#lightbox img').naturalWidth > 0")
            if name in ('iphone','desktop'):
                page.screenshot(path=str(OUT / f'{name}-lightbox.png'))
            page.locator('#lightbox [data-next]').click()
            assert page.locator('#lightbox-caption').inner_text() == '实机截图 2 / 5'
            page.keyboard.press('ArrowLeft')
            assert page.locator('#lightbox-caption').inner_text() == '实机截图 1 / 5'
            page.keyboard.press('Escape')
            page.wait_for_function("!document.querySelector('#lightbox').open && document.body.style.overflow === ''")
            assert not page.locator('#lightbox').is_visible()
            assert page.evaluate('document.body.style.overflow') == ''
            assert page.locator('.shot').first.evaluate('(el)=>el===document.activeElement')
            gallery = page.locator('#evocenter .shots')
            if gallery.evaluate('(el)=>el.scrollWidth>el.clientWidth+3'):
                page.locator('#evocenter [data-direction="1"]').click()
                assert gallery.evaluate('(el)=>el.scrollLeft') > 0
            page.locator('#copy-source').click()
            assert page.evaluate('navigator.clipboard.readText()') == 'https://eleveny123.github.io/'
            page.locator('#evocenter .detail-link').click()
            assert 'evocenter.html' in page.url
            assert page.locator('h1').inner_text() == 'Evo Center'
            page.locator('.repo-back').click()
            assert page.title() == 'JaySuen Repo · 越狱插件'
            assert not errors, (name, errors)
            assert not missing, (name, missing)
            results.append({'viewport':name,'width':width,'height':height,'theme':scheme,'status':'PASS'})
            context.close()
        # Content and source actions remain available if scripts are disabled.
        context = browser.new_context(viewport={'width':390,'height':844}, java_script_enabled=False)
        page = context.new_page(); page.goto(url)
        assert page.locator('.tweak').count() == 3
        assert page.locator('.source-button').count() == 2
        assert page.locator('.detail-link').count() == 3
        scripts_disabled_passed = True
        context.close(); browser.close()
finally:
    server.shutdown()
    (OUT / 'results.json').write_text(json.dumps({'viewports':results,'javascriptDisabledContent':scripts_disabled_passed},ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results))
