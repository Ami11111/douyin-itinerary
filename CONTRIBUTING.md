# Contributing / 参与贡献

Thanks for taking the time. Issues and pull requests are both welcome.
感谢你的时间，欢迎提 issue 和 PR。

## Reporting a parsing bug / 报告解析问题

This is the most useful kind of report. Please include:
这是最有价值的一类反馈，请附上：

1. The bio text, verbatim — copy it rather than retyping, the exact punctuation
   and emoji matter. 简介原文（请直接复制，标点和表情会影响解析）。
2. What the app produced. 实际解析结果。
3. What you expected. 期望的结果。
4. The date you ran it, since year inference is relative to today.
   运行日期——年份推断是相对于「今天」的。

Please redact anything you would not want in a public repository, such as
contact details that appear in the bio.
请先去掉你不希望公开的内容，例如简介里的联系方式。

## Development setup / 开发环境

```bash
./start.sh                              # installs everything and runs both servers
cd backend && .venv/bin/python -m pytest
```

The parser is a pure function, so you rarely need to run a scrape to work on it:
解析器是纯函数，改规则通常不需要真的跑采集：

```python
from datetime import date
from app.parser import ItineraryParser

ItineraryParser().parse("行程：8.15沈阳/10.3上海", today=date(2026, 8, 19))
```

## Pull requests / 提交 PR

- **Every parsing change needs a test.** Add a case to
  `backend/tests/test_parser.py` that fails before your change and passes after.
  每个解析改动都要配一个测试：改动前失败、改动后通过。
- Run `pytest` before opening the PR — the suite is fast.
  提交前跑一遍 `pytest`，很快。
- Keep changes focused; a rule that fixes one bio while breaking three others is
  worse than no rule. Real bios are ambiguous, and it is fine to leave a case
  unhandled and say so.
  改动尽量聚焦：修好一条简介却弄坏三条，不如不改。真实简介本身就有歧义，
  处理不了的情况可以明确留着不处理。
- Match the surrounding style: comments explain *why* a rule exists, usually with
  the real bio snippet that motivated it.
  保持现有风格：注释说明规则为什么存在，通常附上触发它的真实简介片段。

## Scope / 范围

This project reads content that is already visible in a browser you are signed
into yourself. Pull requests that add official API calls, request signing,
captcha solving, account automation, or anything aimed at higher-volume
collection are out of scope and will be declined.

本项目只读取你自己登录的浏览器中已经可见的内容。涉及官方 API、请求签名、
验证码绕过、账号自动化，或以提高采集量为目的的 PR 不在范围内，不会被合并。
