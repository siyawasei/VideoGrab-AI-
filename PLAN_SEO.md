# SEO 优化方案 — 收录 + 排名

## 审计发现

### 🔴 P0 — 阻塞收录
1. 无 robots.txt — 搜索引擎不知道爬取规则
2. 无 sitemap.xml — 搜索引擎不知道有哪些页面
3. og:image 引用不存在的图片 — 社交分享无预览
4. SPA 客户端渲染 — Google 需要额外渲染才能看到内容

### 🟡 P1 — 影响排名
5. 无 WebSite + FAQ 结构化数据
6. 无内容页面（features/faq）可被索引
7. 无 OG 预览图

## 实施步骤

1. robots.txt + sitemap.xml
2. 修复 index.html OG/JSON-LD
3. 创建 OG 预览图
4. features.html 静态页（可索引）
5. faq.html 静态页（FAQ 富片段）
6. 后端添加静态页面路由
