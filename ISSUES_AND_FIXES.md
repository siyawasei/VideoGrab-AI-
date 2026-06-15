# 问题记录与修复方案

## 1. B站 412 Precondition Failed（yt-dlp 反爬）

**现象**: yt-dlp 解析 B站视频时报错 `HTTP Error 412: Precondition Failed`

**原因**: B站 2024 年起启用了 WBI 签名反爬机制，yt-dlp 的 Bilibili extractor 无法绕过。即使提供浏览器 cookies、自定义 User-Agent、Referer 头均无效。

**修复**: 新建 `backend/api/bilibili.py`，完全绕过 yt-dlp，直接调用 B站 API：
- `/x/frontend/finger/spi` → 获取 buvid 反爬指纹
- `/x/web-interface/view` → 获取视频详情（标题、封面、UP主、播放量等）
- `/x/player/wbi/playurl` → 获取 DASH 流地址（视频流 + 音频流）
- 自动判断 URL 是否为 B站，路由到专用处理器

---

## 2. ffmpeg 找不到（Windows PATH 问题）

**现象**: `FileNotFoundError: [WinError 2] 系统找不到指定的文件`

**原因**: ffmpeg 安装在 `C:\Program Files\ffmpeg\bin\` 但未添加到系统 PATH 环境变量。

**修复**: `bilibili_merge_streams()` 函数中自动搜索常见安装路径：
```python
ffmpeg = shutil.which("ffmpeg")
if not ffmpeg:
    for path in [r"C:\Program Files\ffmpeg\bin\ffmpeg.exe", r"C:\ffmpeg\bin\ffmpeg.exe"]:
        if os.path.exists(path):
            ffmpeg = path
            break
```

---

## 3. `os` 模块未定义

**现象**: 下载到 85% 合并阶段报错 `name 'os' is not defined`

**原因**: `bilibili_merge_streams()` 函数内部只导入了 `subprocess` 和 `shutil`，但代码中使用了 `os.path.exists()`。

**修复**: 在函数内部补充 `import os`。

---

## 4. 前端错误显示 `[object Object]`

**现象**: 下载失败时，前端错误信息显示为 `[object Object]` 而非可读文字

**原因**: 
- API 拦截器的 `err.response?.data?.detail` 可能是数组或对象（Pydantic 验证错误格式）
- SSE 返回的 `data.error` 可能是 Python 异常对象而非字符串
- JavaScript 直接拼接对象会变成 `[object Object]`

**修复**: 
- 新增 `safeStr()` 工具函数，统一处理 Error 对象、数组、对象等类型
- API 拦截器增加对数组/对象类型 detail 的处理

---

## 5. `Input should be a valid string`（Pydantic 验证）

**现象**: 点击下载时后端报错 `Input should be a valid string`

**原因**: B站返回的 `format_id` 是数字类型（如 `32`），但后端 Pydantic 模型要求 `str`。

**修复**: 前端调用时强制转为字符串：
```javascript
downloader.startDownload(url, String(format.format_id), String(format.quality))
```

---

## 6. 封面图不显示（防盗链）

**现象**: 解析成功但封面图显示为空白

**原因**: B站图片 CDN 有防盗链机制，浏览器直接请求时因 Referer 头被拦截。

**修复**: 所有 `<img>` 标签添加 `referrerpolicy="no-referrer"` 属性，阻止浏览器发送 Referer。

---

## 7. 下载卡在 70% 然后超时

**现象**: 进度条到 70% 后不动，最终报超时错误

**原因**: B站 DASH 格式需要分别下载视频流和音频流再合并。原代码串行下载（先视频后音频），视频下载耗时较长，期间音频流的 CDN URL 已过期（B站流 URL 有时效性 deadline 参数）。

**修复方案**:
1. **并发下载**: 用 `ThreadPoolExecutor` 同时下载视频流和音频流，不再串行等待
2. **CDN 备用节点**: B站 API 返回 `backup_url` 列表，当主 CDN 节点超时时自动切换到备用节点（如 `bilivideo.com`、`upos-sz-mirrorcoso1.bilivideo.com`）
3. **每次下载获取新 URL**: 不再使用缓存的流地址，避免 URL 过期

---

## 8. B站流 URL 时效性

**现象**: 解析后过一段时间再下载，流 URL 失效

**原因**: B站 DASH 流 URL 包含 `deadline` 参数，通常 10-20 分钟后过期。

**修复**: 
- 解析结果加缓存（10 分钟 TTL），用于前端展示
- 下载时重新调用 API 获取最新流 URL
- `bilibili_download_stream()` 支持 `backup_urls` 参数，自动重试

---

## 9. 优酷格式解析为空（vcodec/acodec 缺失）

**现象**: 优酷视频能解析到标题，但格式列表中 `has_video=False, has_audio=False`，前端不显示任何可下载选项

**原因**: 优酷的 yt-dlp 格式数据没有 `vcodec` 和 `acodec` 字段（值为 `None`）。原代码判断逻辑 `f.get("vcodec") not in (None, "none")` 当 vcodec 不存在时返回 `False`，误判为"无视频"。

**修复**: 改为推断逻辑——当 vcodec 为 None 时，有 height 就认为有视频；acodec 为 None 时默认认为有音频：
```python
has_video = vcodec not in (None, "none") if vcodec is not None else bool(height)
has_audio = acodec not in (None, "none") if acodec is not None else True
```

---

## 10. 抖音链接格式不支持

**现象**: 用户粘贴抖音短链接 `https://v.douyin.com/xxx` 或精选页 `https://www.douyin.com/jingxuan?modal_id=xxx` 时报错"不支持的链接格式"

**原因**: yt-dlp 的抖音 extractor 只识别标准格式 `https://www.douyin.com/video/{id}`，不支持短链接和精选页链接。

**修复**: 新增 `normalize_url()` 函数，在解析/下载前自动规范化 URL：
- `v.douyin.com` 短链接 → 跟随 HTTP 重定向获取真实地址
- `douyin.com/jingxuan?modal_id=xxx` → 提取 modal_id 构造标准链接
- `youtu.be/xxx` → 展开为 `youtube.com/watch?v=xxx`
- `b23.tv/xxx` → 跟随重定向获取 B站真实地址

**注意**: 下载路由中也需调用 `normalize_url()`，否则解析成功但下载失败。

---

## 11. 抖音格式列表重复（CDN 变体）

**现象**: 抖音同一个画质显示多个选项，且画质越高文件越小（如 720p 显示 40MB 和 15MB 两个）

**原因**: yt-dlp 返回了多个 CDN 变体（`h264_720p-0`, `h264_720p-1`, `h264_720p-2`）和不同编码（H.264 vs H.265）。H.265 压缩率更高所以文件更小，但用户会困惑。

**修复**:
- 格式去重：按分辨率+扩展名去重，同分辨率只保留一个
- 下载策略：抖音用 `format: best` 让 yt-dlp 自动选最佳格式，不手动指定 format_id（手动指定容易因 CDN 问题失败）

---

## 12. YouTube 下载后没有声音

**现象**: YouTube 视频能下载，播放时画面正常但没有声音

**原因**: YouTube 使用 DASH 格式，视频流和音频流是分开存储的。原代码没有正确合并音视频流。

**修复**: YouTube 专用下载策略：
```python
ydl_opts["format"] = "bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]/bestvideo+bestaudio/best"
ydl_opts["format_sort"] = ["vcodec:h264", "acodec:aac"]
```
- 强制选 H.264 视频 + AAC 音频（兼容所有播放器）
- 自动合并为单个 MP4 文件

---

## 13. YouTube 视频无法播放（编码不兼容）

**现象**: YouTube 视频下载后，部分播放器无法播放

**原因**: YouTube 默认提供 VP9/AV1 视频编码 + Opus 音频编码，这些编码在某些播放器中不被支持。

**修复**: 解析和下载时都优先选择 H.264 + AAC 编码：
- 解析时 `format_sort: [vcodec:h264, acodec:aac]` 优先返回兼容格式
- 下载时 `bestvideo[vcodec^=avc1]+bestaudio[acodec^=mp4a]` 强制选兼容格式

---

## 14. B站画质太少（只有 480p/360p）

**现象**: B站视频只显示 480p 和 360p 两个画质选项

**原因**: B站 API 未登录状态下只返回低画质流。720p/1080p/4K 等高画质需要 SESSDATA cookie（B站登录凭证）。

**修复**:
- 新增 SESSDATA 配置功能（`/api/bilibili/sessdata`）
- 前端 Cookies 下拉菜单新增 SESSDATA 输入框
- 用户按 F12 → Application → Cookies → bilibili.com → 复制 SESSDATA 值
- 保存后自动加载，下次解析时携带 SESSDATA 请求高画质

---

## 15. B站音视频下载后是两个文件

**现象**: B站下载后得到 `.m4s` 视频文件和 `.m4s` 音频文件，没有合并为 MP4

**原因**: B站 DASH 格式将视频和音频分开存储，ffmpeg 合并步骤失败（可能是 ffmpeg 路径问题或合并超时）。

**修复**:
- ffmpeg 自动搜索常见安装路径（已在问题 #2 中修复）
- 并发下载视频流和音频流，减少总等待时间
- CDN 备用节点自动切换，避免单节点超时
- 下载完成后自动清理临时 .m4s 文件

---

## 16. 芒果TV 下载后是 TS 格式而非 MP4

**现象**: 芒果TV 视频下载后得到 `.ts` 文件（MPEG-TS 格式），部分播放器无法播放

**原因**: 芒果TV 使用 HLS（m3u8）格式传输，yt-dlp 直接下载 TS 分片但没有转封装为 MP4。虽然设置了 `merge_output_format: "mp4"`，但 yt-dlp 找不到 ffmpeg 来执行转封装。

**修复**: 在 yt-dlp 配置中显式指定 ffmpeg 路径：
```python
opts["ffmpeg_location"] = _find_ffmpeg()  # 自动搜索 C:\Program Files\ffmpeg\bin 等路径
```
同时加 `remux_video: "mp4"` 确保 TS 自动转封装为 MP4。

---

## 17. 芒果TV/腾讯视频下载进度一直为 0

**现象**: 芒果TV和腾讯视频下载时，前端进度条一直显示 0%

**原因**: HLS 下载的进度上报方式与普通下载不同。yt-dlp 对 HLS 使用 `fragment_index/fragment_count`（分片进度）而非 `total_bytes/downloaded_bytes`（字节进度）。原代码只处理了字节进度，分片进度被忽略。

**修复**: 进度钩子增加三种进度计算方式：
1. 字节进度：`downloaded_bytes / total_bytes`
2. HLS 分片进度：`fragment_index / fragment_count`
3. 百分比字符串：`_percent_str` 字段

---

## 18. 腾讯视频/爱奇艺解析成功但无可下载格式

**现象**: 腾讯视频能解析到标题，但格式列表为空；爱奇艺直接报错"Can't find any video"

**原因**:
- 腾讯视频：DRM 版权保护，yt-dlp 无法获取流地址（`formats` 为空）
- 爱奇艺：yt-dlp extractor 代码过时，API 接口已变更

**修复**: 在 `extract_info` 中检测 0 formats 情况，返回友好错误提示：
```
"[腾讯视频] 解析成功但无可下载格式。可能原因：视频受 DRM 版权保护、需要登录、或 yt-dlp 解析器已过时。"
```

---

## 19. 抖音下载报错"不支持的链接格式"（二次修复）

**现象**: 抖音 `jingxuan` 链接在解析时正常，但下载时报错"不支持的链接格式"

**原因**: `routes.py` 的 download 路由中，`normalize_url` 的结果存在变量 `url` 中，但后续调用 `start_download()` 时仍使用原始的 `req.url`。解析路由已修复但下载路由遗漏。

**修复**: 将 `start_download(req.url, ...)` 改为 `start_download(url, ...)`（使用规范化后的 URL）。

---

## 20. 腾讯视频下载极慢（CDN 限速）

**现象**: 腾讯视频能解析到格式，但下载速度只有 ~1KB/s，ETA 20+ 小时

**原因**: 腾讯视频的 HLS CDN 对非浏览器客户端限速。yt-dlp 下载 m3u8 分片时被 CDN 识别为爬虫并限速。这是腾讯平台的反爬策略，不是代码问题。

**修复**: 更新平台状态为 `throttled`（CDN 限速），前端显示橙色状态灯和提示"CDN 限速，下载极慢，不建议使用"。

---

## 21. 芒果TV VIP 视频无法下载

**现象**: 部分芒果TV视频解析报错 401 Unauthorized

**原因**: 芒果TV VIP 视频需要登录会员才能获取流地址。API `getSource` 返回 401 表示无权访问。免费视频可正常下载。

**识别方法**: API 返回 `trialtime: 300` 表示 VIP 视频（只能试看 5 分钟）。

**修复**: 无需修复，这是平台限制。免费视频正常下载，VIP 视频需要用户自行在浏览器中登录会员。

---

## 22. 腾讯视频部分视频 0 formats

**现象**: 某些腾讯视频能解析到标题，但格式列表为空

**原因**: 腾讯视频对部分内容启用 DRM 保护，yt-dlp 无法获取流地址。不同视频的保护级别不同。

**修复**: 检测 0 formats 情况，返回友好提示"视频受 DRM 版权保护或需要登录"。

---

## 技术架构补充

### B站下载完整流程
```
用户粘贴 URL → 解析 API → B站 API 获取视频信息 + 流地址
                         → 前端展示视频信息（标题/封面/UP主/播放量/画质选择）
用户选择画质 → 下载 API → 重新获取最新流 URL
                        → 并发下载视频流 + 音频流（自动 CDN 备用）
                        → ffmpeg 合并为 MP4
                        → SSE 推送进度 → 前端显示
```

### 国内平台 yt-dlp 支持现状（2026.06.12）
```
✅ 直接可用: B站(自定义API) | 优酷 | AcFun | 抖音 | 芒果TV(免费)
⚠️ 需cookies: 西瓜视频
🟠 CDN限速:  腾讯视频(解析OK，下载极慢)
❌ 不可用:   爱奇艺(API过时) | 微博(bug) | 快手(无extractor) | 小红书(失效) | 芒果TV-VIP(需登录)
```

### 文件变更清单
| 文件 | 变更 |
|------|------|
| `backend/api/bilibili.py` | B站专用处理器（API解析+流下载+CDN备用+ffmpeg合并+SESSDATA+画质去重） |
| `backend/api/routes.py` | URL规范化+B站路由+下载任务+平台状态/Cookie/SESSDATA API |
| `backend/api/downloader.py` | URL规范化+平台检测+友好错误+格式去重+YouTube/抖音专用下载策略+ffmpeg_location+HLS进度+remux |
| `backend/config.py` | 新增 COOKIES_DIR |
| `frontend/src/composables/useDownloader.js` | safeStr() 错误处理 |
| `frontend/src/api/index.js` | API拦截器+cookies/SESSDATA/平台API |

---

## 23. B站字幕获取失败 — `/x/player/v2` 无 SESSDATA 时返回空字幕

**现象**: AI 视频总结功能中，B站视频字幕获取失败。调用 `/x/player/v2` API 返回 `subtitles: []`（空数组），导致 AI 总结只能使用标题+描述，无法生成带时间戳的章节。

**原因**: B站的 `/x/player/v2` 和 `/x/player/wbi/v2` API **必须携带 SESSDATA（登录态）** 才会返回字幕列表。未登录时几乎必定返回空数组，即使视频本身有 AI 自动生成的字幕。

**排查过程**:
1. 测试 `/x/player/v2?bvid=xxx&cid=xxx` → `subtitles: []`（无 SESSDATA）
2. 测试 `/x/player/wbi/v2` + WBI 签名 → `subtitles: []`（WBI 签名正确但仍需登录态）
3. 测试 yt-dlp → `HTTP Error 412`（B站反爬）
4. 测试页面 HTML 抓取 → B站使用客户端渲染，HTML 中无字幕数据
5. **最终发现**: `/x/v2/dm/view` API **不需要 SESSDATA** 即可返回字幕列表

**修复**: 在 `bilibili_get_subtitle()` 函数中采用双 API 策略：

```python
# 方法 1: /x/v2/dm/view API（不需要 SESSDATA，优先使用）
dm_data = _api_get(f"https://api.bilibili.com/x/v2/dm/view?type=1&oid={cid}&pid={cid}", cookies)
subtitle_list = dm_data["data"]["subtitle"]["subtitles"]

# 方法 2: /x/player/v2 API（需要 SESSDATA，作为备用）
if not subtitle_list:
    player_data = _api_get(f"https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}", cookies)
    subtitle_list = player_data["data"]["subtitle"]["subtitles"]
```

**关键技术点**:
| API | 需要 SESSDATA | 返回字幕 | 用途 |
|-----|:---:|:---:|------|
| `/x/player/v2` | ✅ 必须 | 有登录态时返回 | 备用方案 |
| `/x/player/wbi/v2` | ✅ 必须 | 有登录态时返回 | 备用方案（WBI签名） |
| `/x/v2/dm/view` | ❌ 不需要 | ✅ 始终返回 | **主要方案** |

字幕 CDN 地址（`aisubtitle.hdslb.com`）本身也不需要认证，只需 `Referer: https://www.bilibili.com` 即可下载。

**涉及文件**:
| 文件 | 变更 |
|------|------|
| `backend/api/bilibili.py` | `bilibili_get_subtitle()` 改用 `/x/v2/dm/view` 为主，`/x/player/v2` 为备 |
| `frontend/src/views/HomeView.vue` | format_id 转 String |
| `frontend/src/components/DownloadModal.vue` | 视频信息展示+referrerpolicy+自动合并提示 |
| `frontend/src/components/HistorySection.vue` | referrerpolicy |
| `frontend/src/components/Navbar.vue` | Cookies上传+SESSDATA配置入口 |
| `frontend/src/components/PlatformsSection.vue` | API实时平台状态 |
| `ISSUES_AND_FIXES.md` | 问题记录文档（持续更新） |

---

## 24. Mermaid 思维导图动态导入失败

**现象**: 浏览器报错 `Failed to fetch dynamically imported module: http://localhost:8000/assets/mermaid.core-xxx.js`，思维导图无法渲染，下载按钮无反应。

**原因**: Vite 构建时 mermaid 被拆分为独立 chunk，浏览器缓存了旧的 index.html（引用旧 hash 的 chunk 文件），导致请求的 JS 文件不存在。

**修复**:
1. 添加模块缓存：首次加载成功后缓存 mermaid 模块实例，避免重复导入
2. CDN 兜底：动态导入失败时自动从 `cdn.jsdelivr.net/npm/mermaid@11` 加载
3. index.html 添加 `Cache-Control: no-cache` 头，确保更新后立即生效

**涉及文件**:
| 文件 | 变更 |
|------|------|
| `backend/app.py` | SPA 兜底路由中 index.html 添加 no-cache 头 |
| `frontend/src/components/VideoSummary.vue` | mermaid 模块缓存 + CDN 兜底 + 下载错误提示 |

---

## 25. 思维导图下载无反应

**现象**: 点击思维导图的 SVG/PNG 下载按钮没有反应，没有文件下载。

**原因**:
1. SVG 序列化时缺少 `xmlns` 声明，浏览器 Image 拒绝加载，canvas 静默失败
2. `canvas.toBlob()` 返回 null 时没有错误提示
3. 使用 blob URL 方式在某些浏览器中被阻止

**修复**:
1. 克隆 SVG 后手动补上 `xmlns="http://www.w3.org/2000/svg"` 和 `xmlns:xlink`
2. 改用 base64 data URL 替代 blob URL（`btoa(unescape(encodeURIComponent(svgData)))`）
3. 下载函数添加用户可见的错误提示（`alert()`）
4. PNG 生成失败时提示用户使用 SVG 格式

**涉及文件**:
| 文件 | 变更 |
|------|------|
| `frontend/src/components/VideoSummary.vue` | downloadMindmapSvg/Png 重写，补 xmlns，base64 编码，错误提示 |

---

## 26. 模态框打开时背景页面可滚动

**现象**: 打开登录弹窗或下载弹窗后，滑动滚轮会导致背景的主页跟着滚动，体验不佳。

**原因**: 固定定位的模态框（`position: fixed`）不会阻止父级滚动事件传播。

**修复**: 在 LoginModal 和 DownloadModal 中添加 `watch`，当 `visible` 变为 true 时设置 `document.body.style.overflow = 'hidden'` 锁定背景，关闭时恢复为空字符串。

**涉及文件**:
| 文件 | 变更 |
|------|------|
| `frontend/src/components/LoginModal.vue` | watch visible → body overflow 控制 |
| `frontend/src/components/DownloadModal.vue` | watch visible → body overflow 控制 |

---

## 27. 配置文件硬编码敏感信息

**现象**: `config.py` 中硬编码了数据库密码 `123456`、JWT 密钥 `your-secret-key-change-in-production`，提交到 git 会泄露。

**原因**: 开发阶段直接写死了配置值，没有使用环境变量。

**修复**:
1. 所有敏感配置改为 `os.getenv()` 读取环境变量
2. JWT 密钥未设置时自动生成随机密钥（`secrets.token_hex(32)`）
3. 安装 `python-dotenv`，`app.py` 启动时自动加载 `backend/.env` 文件
4. 创建 `.env.example` 模板（提交到 git，不含真实密钥）
5. `.gitignore` 全面覆盖：`*.env`、`cookies/*`、`deepseek_key.txt`、`page_debug.html`

**涉及文件**:
| 文件 | 变更 |
|------|------|
| `backend/config.py` | 所有敏感值改为 `os.getenv()` |
| `backend/app.py` | 添加 `python-dotenv` 自动加载 `.env` |
| `backend/.env.example` | 新建，配置模板（无真实密钥） |
| `.gitignore` | 全面覆盖敏感文件 |
