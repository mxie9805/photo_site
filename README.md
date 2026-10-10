# 摄影个人站

照片放进文件夹、在表格里填一行、发布，网站就会更新。

## 加一张照片

1. 把导出的 JPEG 放进 `photos/`。文件名用英文、数字和连字符，比如 `bryce-hoodoos.jpg`。
   建议导出长边 3000px 左右。这个仓库是公开的，放进来的文件任何人都能下载。
2. 打开 `photos.csv`，加一行。只有 `file` 必填，其余都可以留空。
3. 发布（提交并推送到 GitHub）。几分钟后网站自动更新。

不在 `photos.csv` 里的照片也会出现在网站上，标题取自文件名。

## photos.csv 每一列

| 列 | 填什么 |
|---|---|
| `file` | `photos/` 里的文件名 |
| `title` / `title_zh` | 标题，英文和中文。中文留空就显示英文 |
| `series` | 系列的 slug，要和 `site.toml` 里的一致 |
| `place` / `place_zh` | 地点 |
| `date` | 拍摄日期 `2025-05-18`。留空则读取照片里的拍摄时间 |
| `featured` | 填 `yes` 表示进入首页随机主图的名单 |
| `note` / `note_zh` | 一句说明 |
| `camera` `lens` `focal_length` `aperture` `shutter` `iso` | 留空则读取照片里的参数；填了就以这里为准（胶片扫描件用） |
| `film` | 胶片型号或胶片模拟，需要手填 |

## 其他设置

`site.toml`：网站名称、关于页的文字、联系方式、系列列表。

## 在自己电脑上预览（可选）

```
pip install -r requirements.txt
python build.py --serve
```

然后打开 http://localhost:8000 。

## 拍摄数据

每次生成都会输出 `dist/data/photos.csv`，包含每张照片合并后的全部字段，
上线后在 `网站地址/data/photos.csv`，可以直接拿去分析。

## 文件说明

| 路径 | 作用 |
|---|---|
| `photos/` | 你的照片 |
| `photos.csv` | 每张照片的信息 |
| `site.toml` | 网站设置 |
| `build.py` | 生成网站的脚本 |
| `templates/` `static/` | 页面模板、样式和脚本 |
| `.github/workflows/publish.yml` | 让 GitHub 在每次更新后自动生成并发布 |
