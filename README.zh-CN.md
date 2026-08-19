# 抖音关注行程

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![Vue 3](https://img.shields.io/badge/Vue-3-42b883.svg)](https://vuejs.org/)

把你关注的抖音博主的简介变成一张日历。

抖音博主习惯把行程写在简介里，通常是一行没有分隔的短句，比如
`行程：8.15沈阳/10.3上海/10.7厦门`。本项目从已登录的浏览器会话读取这些简介，
提取「日期 + 地点/活动」以及无日期线索，按日期总表和博主卡片双视图展示。
任务每 24 小时自动刷新，也支持手动刷新；过期行程会自动清理并记录日志。

**[English](README.md)**

---

## 功能

- **简介转日历**：覆盖博主真实使用的中文缩写，包括区间（`8.7-8.9`）、
  同月多日列举（`8.16/21/26/28`）、中文月份（`8月22-23`）和紧凑写法（`925成都qy`）。
- **前后顺序自适应**：逐段判断地点在日期前还是日期后，`沈阳星潮8.15` 与
  `8.15沈阳星潮` 都能正确解析。
- **噪声过滤**：展位号、机型、年龄段、时间段（`E4-29`、`2460f2.8`、`18-28岁`、
  `晚9-11`）不会被误认成日期。
- **双视图**：按日期排序的总表 + 博主卡片；关键词、日期区间、状态筛选在接口层提供。
- **定时 + 手动刷新**：采集失败时保留上一次成功的结果。
- **本地优先**：数据库、浏览器登录态、日志全部保存在 `data/`，不使用官方 API、
  逆向签名或付费第三方服务。

## 环境要求

- Python 3.10+
- Node.js 18+
- Google Chrome（通过 Playwright 驱动）

## 快速开始

```bash
git clone https://github.com/Ami11111/douyin-itinerary.git
cd douyin-itinerary
chmod +x start.sh
./start.sh
```

`start.sh` 会创建虚拟环境、安装前后端依赖、从 `backend/.env.example` 生成
`backend/.env`，并同时启动前后端。

然后打开 <http://127.0.0.1:5173>：

1. 点击「扫码登录」，会打开一个独立的 Chrome 窗口。
2. 在该窗口中扫码 / 登录抖音。
3. 回到页面点击「手动刷新」，等待采集完成。
4. 之后后端会每 24 小时自动采集一次。

Playwright 需要一份 Chrome。如果浏览器启动失败：

```bash
backend/.venv/bin/python -m playwright install chrome
```

## 配置

复制 `backend/.env.example` 为 `backend/.env`，所有配置项都带 `DOUYIN_` 前缀。

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `DOUYIN_HEADLESS` | `false` | 定时采集是否无头运行。改为 `true` 不再弹窗，但更容易触发验证码。 |
| `DOUYIN_SCRAPE_LIMIT` | `700` | 最多采集的关注用户数量。 |
| `DOUYIN_SCROLL_DELAY_MS` | `800` | 加载关注列表时的滚动间隔。 |
| `DOUYIN_PROFILE_DELAY_MS` | `900` | 打开用户主页补全简介时的间隔。 |
| `DOUYIN_MAX_PROFILE_PAGES` | `100` | 每次最多打开多少个无简介用户主页。 |
| `DOUYIN_BROWSER_CHANNEL` | `chrome` | Playwright 浏览器通道。 |
| `DOUYIN_DB_PATH` | `../data/app.db` | SQLite 数据库位置。 |

`data/undated_keywords.txt` 保存无日期线索的触发关键词，一行一个，`#` 开头为
注释；修改后下次刷新生效。

## 解析规则

### 日期

下文示例中的漫展、场馆和 IP 名称均为虚构。解析规则是对着真实简介开发的，
但文档里引用的内容不指向任何真实活动或账号。

支持的写法：

- 单个日期：`8.9`、`8/9`、`8-9`、`8月9日`、`8月9号`、`2026.8.9`、`10. 3`
- 日期区间：`8.7-8.9`、`10.24-25`、`8月22-23`、`7.31～8.2`、`8.22—8.23日`
- 同月多日列举：`9.5 6 12 13`、`8.16/21/26/28`、`4.17.18.19`、`9.18、19、20`、
  `10.24／25`、`8月7-8、10-12，14-16`
- 紧贴地点的紧凑写法：`925成都qy`（同一简介中出现两次以上才启用）

**年份推断**：没写年份时，取距今最近的那一年（去年 / 今年 / 明年），过去方向
略加惩罚，所以距离相同时优先算作未来。简介里常见的「往期行程」——8 月看到的
`5.1 无锡云图车展`——因此会落在今年而不是明年。已经过去的行程不再写入数据库，
避免每次刷新都生成再清理一遍。

超过 31 天的区间只保留起始日，避免长期驻场把日历刷满。行程按一次性事件处理，
不自动重复。

### 名称

- 先按换行和 `｜；。！？` 切分简介，逐段独立判断日期在前还是在后：段落以日期
  结尾、且开头不是「行程：」一类标签时按「地点 + 日期」处理，否则按
  「日期 + 地点」处理。
- 装饰性表情（`🎀✨🌟🩵` 等）只当分隔符，不会被当成地点名。
- 遇到 `阵容`、`商务`、`私信`、`@某人` 等联系方式标记时截断；但整段就是
  `@某某` 时保留该名称。
- 括号不配对（`（延期`、`深圳砚山展】`）会被去掉；只剩 `延期`、`取消` 这类
  状态词时丢弃该条。

### 无日期线索

只有同时满足「事件词 + 地点词 + 没有联系方式噪声」的短句才会记为待定线索
（例如 `线下行程：上海ac全勤`），避免把自我介绍整段当成行程。

## 接口

后端在 `/api` 下提供一组 JSON 接口，交互式文档在
<http://127.0.0.1:8000/docs>。

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/api/health` | 健康检查。 |
| `GET` | `/api/douyin/status` | 登录状态、最近一次任务状态与错误。 |
| `POST` | `/api/douyin/login` | 打开 Chrome 窗口扫码登录。 |
| `POST` | `/api/refresh` | 触发一次采集（202，后台执行）。 |
| `GET` | `/api/itineraries` | 行程列表，支持 `date_from`、`date_to`、`status`、`keyword`、`user_id`。 |
| `GET` | `/api/following` | 关注博主列表及行程数量。 |
| `DELETE` | `/api/itineraries/{id}` | 删除一条行程（写入 `cleanup_log`）。 |

## 目录结构

```text
backend/               FastAPI + SQLite + APScheduler + Playwright
  app/parser.py        简介 → 行程的解析规则
  app/scraper.py       Playwright 采集与 DOM 选择器
  app/service.py       持久化、刷新任务、过期清理
  tests/               pytest 测试
frontend/              Vue 3 + Vite + Element Plus + Pinia
data/                  SQLite 数据库、浏览器登录态、日志、解析配置
start.sh               一键安装依赖并启动前后端
```

## 开发

```bash
# 后端
cd backend
.venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
.venv/bin/python -m pytest

# 前端
cd frontend
npm run dev
```

解析器是纯函数、无副作用的——`ItineraryParser().parse(bio, today=...)` 输入一段
文本、返回 `ParsedTrip` 列表，因此新规则可以直接在
`backend/tests/test_parser.py` 里开发，不需要真的跑一次采集。

## 常见问题

采集失败时不会覆盖上一次成功结果，前端会显示最近一次错误，点击「手动刷新」可
重试。

| 现象 | 处理 |
| --- | --- |
| 登录态过期 | 重新点击「扫码登录」。 |
| 出现验证码 | 在打开的浏览器中完成验证后再刷新。 |
| 采集不到内容 | 抖音网页结构变化，需要调整 `backend/app/scraper.py` 中的 DOM 选择器。 |
| 浏览器启动失败 | 在 `backend/.venv` 中执行 `python -m playwright install chrome`。 |

## 参与贡献

欢迎提 issue 和 PR。最有价值的是解析类问题：请附上简介原文、实际解析结果、
以及你期望的结果。

工作流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可

[MIT](LICENSE) © Ami

## 免责声明

本项目仅读取你自己登录的浏览器中已经可见的内容，不使用官方 API、不做逆向签名、
不依赖付费第三方服务。它面向个人使用——管理你已经关注的博主的行程——其可用性
取决于抖音网页版的页面结构，后者随时可能变化并触发风控。请遵守抖音的服务条款，
不要用于商业用途或高频抓取，也不要转发它采集到的个人信息。
