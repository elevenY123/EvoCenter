# Evo Center 商店发布资料

署名顺序：chatgpt5.6（sol） · JaySuen。
支持系统：iOS 16.0–16.6、iOS 17.0–17.4。

## 文件

- `assets/icon.png`：确认采用的商店图标。
- `assets/banner.png`：蓝色玻璃模块横版 banner，约 16:9，无文字。
- `release.json`：确认文案、兼容范围、署名、反馈、致谢、用户更新日志。
- `index.html`：支持明暗外观和移动端的网页介绍，可本地预览。
- `native.json`：Sileo 原生介绍，分为介绍、更新日志、关于与反馈三页。
- `sileo-featured.json`：源内推荐 banner 条目；需由源维护者合并到源根目录。

## 在线展示方案

公开仓库：https://github.com/elevenY123/EvoCenter 。仅发布展示资料，不包含插件源码。
网页介绍：https://eleveny123.github.io/EvoCenter/ 。
图标、横幅及 Sileo 原生 JSON 使用 GitHub Pages HTTPS 地址；JSON 以 application/json 提供。
此方案不需要建立 APT 软件源，与 Infinidock16 Revival 的展示方式一致。

在项目根目录生成展示文件：

```sh
python3 Tools/prepare-store.py --base-url https://eleveny123.github.io/EvoCenter --web-url https://eleveny123.github.io/EvoCenter/
```

本目录内容发布到仓库根目录。`Packages-fields.txt` 的展示字段已写入 deb 的 control。
展示图片不打包进 deb；插件运行不依赖本目录。原始图片仅保留在展示仓库中。
未来上架软件源时也可合并这些字段；保留源工具生成的 Filename、Size、SHA256 等字段。

Sileo 原生页使用 `SileoDepiction`；兼容网页介绍使用 `Depiction`；
列表图标使用 `Icon` 的 HTTPS 地址。`headerImage` 是包介绍页 banner，
`sileo-featured.json` 则是源推荐 banner，两者不是一个字段。
不能仅靠在 deb 中放图片保证所有商店完整显示。

未确认的价格、许可证、下载量、评分和开发者邮箱不填写；不制造评级
和“官方认证”。反馈请在酷安 App 搜索 JAYSuen，或搜索 Evo Center。

基础依赖约束仅限制大版本区间，并非精确系统支持检测；完整受支持的
范围以介绍中的两个明确区间为准，不将 iOS 16.7.x 宣传为受支持。

## 视觉生成记录

使用 imagegen 技能的内置生成工具，非 CLI/API 回退。
图标提示：蓝色玻璃控制中心模块，两枚方形控制块与白色填充竖向滑块，
无文字、正视图、小尺寸可辨识。沿用用户确认的初稿。
banner 提示：以确认图标为品牌参考，新建全幅不透明 16:9 横向构图，
电蓝玻璃控制块、竖向及横向滑块、圆形控制块，内容集中在安全区域，
不含文字、设备模型和水印。

规范参考：
https://developer.getsileo.app/native-depictions
https://developer.getsileo.app/sileo-featured
