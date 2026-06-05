# Morning Brief 使用说明

---

## 1. 这是个啥

Morning Brief 是一个跑在你自己电脑上的市场情报工具。造它的原因很简单：每天早上你想知道"今天市场咋了"，但主流财经 APP 推送太多太乱，彭博这类专业工具看不懂也太贵，而且你的持仓散在 IBKR、币安、Coinbase 几个地方，没有任何一个 app 帮你把这些串起来。

Morning Brief 解决的问题是：用白话+图表+AI 解读，让你 5 分钟内把市场大方向和自己的持仓状态搞清楚。所有数据来源全部免费（yfinance、CoinGecko 等），AI 解读用你已有的 Anthropic API Key，每天大约花 $0.05（几分钱人民币）。整个工具就是一个文件夹，可以放在 Mac、Windows，也可以通过 Git 同步到 iPhone 看快照。

工具分两个入口（"Surface"）：

- **Surface A — Daily Brief**：每天跑一次，抓取 9 个市场指标 + 加密货币恐惧贪婪指数 + BTC 抄底分，然后让 Claude 帮你写白话总结，最后生成一个 HTML 文件——你发给任何人，对方直接在浏览器里看，不需要安装任何东西，也没有任何警告弹窗。
- **Surface B — Portfolio Explorer**：你把券商导出的 CSV 文件拖进去，它帮你画持仓饼图、盈亏棒图，还用 Claude 写 4 段白话总结告诉你"你持仓是什么风格、什么在赚、什么在亏、要警惕什么"。这个只在你本地运行，上传的 CSV 永远不会离开你的电脑。

---

## 2. 第一次使用 — 一次性设置

### 2.1 装 Python

Morning Brief 需要 Python 3.10 或更高版本。

**Mac**：打开 Terminal（聚焦搜索输入"Terminal"），输入：

```bash
python3 --version
```

如果显示 `Python 3.10.x` 或更高就直接跳到下一步。如果提示"command not found"或版本太低，去 [python.org](https://www.python.org/downloads/) 下载安装包，一路点"继续"就好。

**Windows**：打开 PowerShell（开始菜单搜索"PowerShell"），输入：

```powershell
python --version
```

如果没有 Python，去 [python.org](https://www.python.org/downloads/windows/) 下载，安装时**务必勾选"Add Python to PATH"**，否则后续命令会报错。

### 2.2 装依赖（一行命令）

在 Terminal（Mac）或 PowerShell（Windows）里，先 `cd` 进项目文件夹，然后运行：

**Mac：**
```bash
cd ~/Desktop/morning-brief   # 或者你放项目的路径
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows：**
```powershell
cd C:\Users\你的名字\Desktop\morning-brief   # 换成你的路径
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

装完后会看到一大堆"Successfully installed"的提示，正常。这步只需要做一次。

### 2.3 配 ANTHROPIC_API_KEY

AI 解读功能需要一个 Anthropic 的 API Key（密钥）。

**第一步：获取 Key**

去 [console.anthropic.com](https://console.anthropic.com/) 注册/登录。点击左侧 "API Keys" → "Create Key"。复制那串以 `sk-ant-` 开头的字符串，这就是你的密钥。妥善保管，不要截图发给别人。

**第二步：放到项目里**

项目文件夹里有一个叫 `.env.example` 的文件。把它复制一份，改名叫 `.env`（注意：Mac Finder 默认隐藏以点开头的文件，用 Terminal 操作更可靠）：

**Mac：**
```bash
cp .env.example .env
```

**Windows：**
```powershell
copy .env.example .env
```

然后用文本编辑器（Mac 用 TextEdit，Windows 用记事本）打开 `.env`，把这一行：

```
ANTHROPIC_API_KEY=sk-ant-replace-me
```

改成你的真实 Key：

```
ANTHROPIC_API_KEY=sk-ant-你的真实key在这里
```

保存文件。

**第三步：验证生效**

运行下面的命令，如果最后没有报"no_api_key"错误就说明 Key 配好了：

```bash
# Mac
.venv/bin/python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.environ.get('ANTHROPIC_API_KEY', 'NOT SET')[:10])"
```

正常输出会显示你 Key 的前几位字符，比如 `sk-ant-api`。

### 2.4 （可选）让 Mac mini 每天早上自动跑

如果你有 Mac mini 24 小时开着，可以安装一个定时任务，让它每天早上 8:00 自动抓数据、生成快照，你起床就能直接看。

在 Terminal 里运行：

```bash
cd ~/Desktop/morning-brief
./scripts/install_launchd.sh
```

装完后每天早上 8:00（意大利时间）会自动跑一次。日志存在项目文件夹里的 `.launchd.out.log`。

取消自动运行：

```bash
launchctl unload ~/Library/LaunchAgents/com.jiawen.morning-brief.plist
```

---

## 3. 每日使用 — Surface A 每日 Brief

### 3.1 怎么启动

**方式一：双击启动器（推荐）**

打开项目文件夹里的 `launchers/` 子文件夹：

- Mac：双击 `Daily-Brief.command`
  - 第一次双击 macOS 可能弹出"无法验证开发者"——右键点文件 → "打开" → "打开"，之后就可以直接双击了。
- Windows：双击 `Daily-Brief.bat`
  - 第一次 SmartScreen 可能拦截——点"更多信息" → "仍然运行"，之后就可以直接双击了。

**方式二：命令行**

```bash
# Mac
cd ~/Desktop/morning-brief
.venv/bin/python morning_brief.py

# Windows
cd C:\Users\你的名字\Desktop\morning-brief
.venv\Scripts\python.exe morning_brief.py
```

命令行还有几个可选参数：

- `--no-open`：跑完不自动打开浏览器（适合服务器环境）
- `--commit`：把今天的快照用 git commit 存档
- `--commit --push`：存档并推送到远程（适合自动化）

### 3.2 看着 dashboard 怎么读

Dashboard 分几个区域，下面逐一解释每个数字是什么意思。

---

**顶部"今日一句话"（Headline）**

Claude 给你写的一句白话总结，概括今天最重要的一件事。比如"美股今日高开，纳指领涨，市场情绪偏乐观，BTC 维持横盘"。这是你 5 秒钟就能知道今天大方向的地方。

---

**概览栏（Overview）— 9 个核心指标**

这 9 个数字是市场的"体检报告"：

- **SPY / QQQ / VOO**：美股大盘的"温度计"。
  - SPY 代表标普 500（美国最大的 500 家公司），QQQ 代表纳斯达克 100（以科技股为主），VOO 也是标普 500 的另一支 ETF。
  - 数字旁边的百分比（比如 `+0.38%`）是今天相对昨天的涨跌幅。
  - 直觉锚点：标普 500 每天正常波动大约 ±0.5%，超过 ±1.5% 就算比较大的行情。
  - 颜色：绿色 = 涨，红色 = 跌，全书一致。

- **VIX（恐惧指数）**：衡量市场"紧张程度"的指标。
  - VIX 越低 = 市场越平静，VIX 越高 = 市场越紧张害怕。
  - 直觉锚点：VIX 15 大约等于市场预期标普 500 接下来一个月每天波动约 ±1%；VIX 30 则意味着市场预期接下来会非常动荡。
  - 经验判断：低于 20 = 平静正常；20-25 = 轻微警觉；高于 25 = 比较紧张；高于 35 = 恐慌状态（历史上这种时候买入通常结果不错，但也意味着市场确实出了大事）。

- **DXY（美元指数）**：追踪美元相对一篮子主要货币的强弱。
  - DXY 涨 = 美元升值，通常对黄金、比特币、新兴市场有压力。
  - DXY 跌 = 美元走弱，通常对这些资产有支撑。
  - 直觉锚点：DXY 100 是一个心理整数关口，高于这个数说明美元比较强。

- **GLD（黄金）**：追踪黄金价格的 ETF。金价一般和美元反向运动，经济不确定性增加时往往上涨。

- **USO（原油）**：追踪原油价格的 ETF。油价对通胀预期影响很大。

- **BTC-USD / ETH-USD**：比特币和以太坊的美元价格，以及 24 小时涨跌幅。

---

**BTC 抄底分（BTC Bottom Score）**

这是整个工具的核心指标之一，范围 0-100，综合了 4 个免费市场信号：

- **ETF 资金流（权重 38%）**：机构资金今天往 BTC 现货 ETF 净流入还是净流出。净流入越多，说明机构在买入，分数越高；净流出越多，机构在卖出，分数越低。
- **Funding Rate（资金费率，权重 25%）**：永续合约市场上多空方向的情绪指标。费率为正说明大家普遍做多（看涨），为负说明大家偏向做空（看跌）。
- **Crypto Fear & Greed Index（加密货币恐惧贪婪指数，权重 22%）**：下面 F&G 卡片里的那个数字，0 = 极度恐惧，100 = 极度贪婪。
- **Long/Short Ratio（多空比，权重 15%）**：合约市场里做多的人和做空的人的比例。

**如何读分数：**

| 分数范围 | 含义 | 历史规律 |
|---------|------|---------|
| 0 – 15 | 极度恐惧 | 历史上通常是买入的好时机，但下行可能还没结束 |
| 16 – 45 | 恐惧 | 偏低，市场情绪负面，但不是极端 |
| 46 – 55 | 中性 | 没有明确信号 |
| 56 – 85 | 贪婪 | 市场情绪乐观，注意别追高 |
| 86 – 100 | 极度贪婪 | 历史上往往是卖出的好时机 |

**"BTC Bottom Score 38 — Fear 是建议买吗？"**

38 不算极端恐惧，只是偏向恐惧。历史上分数在 35-45 区间时，往后 60 天 BTC 回报通常为正——但这只是统计规律，不是保证。这个分数是观察工具，不是买卖信号。

---

**Crypto F&G（加密货币恐惧贪婪指数）**

这是 alternative.me 网站每天发布的独立指数，综合了价格波动、交易量、社交媒体情绪、比特币占比等多个维度。0 = 极度恐惧，100 = 极度贪婪。

**"F&G 42 — Fear 跟 BTC Bottom Score 啥关系？"**

F&G 是 BTC Bottom Score 四个组件之一（权重 22%）。两者通常方向一致，但不完全相同——BTC Bottom Score 还包含了资金流向和合约市场的信息，所以更全面。

**温度计颜色含义：**

- 红色（两端极端区）：极度恐惧（0-15）或极度贪婪（86-100）都用红色标出——两种极端都意味着市场可能即将反转，是需要格外注意的区域。
- 橙黄色（警戒区）：偏向恐惧（16-30）或偏向贪婪（70-85），情绪有些偏斜。
- 绿色（中性区）：31-69，市场情绪相对平衡，没有极端信号。

---

**个股/个币卡片**

Watchlist 里的每只股票和加密货币各有一张卡片，显示：

- 当前价格
- 24 小时涨跌幅（绿色 = 涨，红色 = 跌）
- Claude 写的一句话 thesis（这只票今天的简要看法）

---

**Liquidity Tone（流动性基调）**

Claude 写的一句话，概括今天市场整体的流动性状态——钱是在流进来（risk-on，愿意冒险）还是流出去（risk-off，偏保守）。

---

**Top 10**

Claude 给你挑的今日 10 件值得知道的事，每条附一个"操作提示"。不一定都和你持仓直接相关，但都是今天市场上重要的信息点。

---

### 3.3 demos/YYYY-MM-DD.html 这文件能干嘛

每次跑完 Daily Brief，除了在浏览器里打开，还会在项目文件夹的 `demos/` 里生成一个以日期命名的 HTML 文件，比如 `demos/2026-06-05.html`。

这个文件是"凝固快照"——所有图表、数据、AI 解读都已经烘焙进这一个 HTML 文件里，不依赖任何外部数据，不需要网络，不需要服务器。任何人用任何浏览器打开就能看到完整内容。

**典型用途：**

- 发邮件给朋友：把文件作为附件发过去，对方双击即可打开，零安装零警告。
- 发 LinkedIn：上传到公司网盘/GitHub Pages，分享链接，对方点开就看到，不需要账号不需要 App。
- 归档历史：你可以翻回去看 6 个月前市场是什么状态。`demos/` 里按日期存着所有历史快照（但注意默认被 `.gitignore` 排除在 git 之外，所以只在本机有，不会同步到 GitHub）。

---

## 4. 每日使用 — Surface B 个人持仓

### 4.1 怎么启动

**方式一：双击启动器（推荐）**

- Mac：双击 `launchers/Portfolio-Explorer.command`
- Windows：双击 `launchers/Portfolio-Explorer.bat`

**方式二：命令行**

```bash
# Mac
.venv/bin/python webui.py

# Windows
.venv\Scripts\python.exe webui.py
```

启动后浏览器会自动打开 `http://127.0.0.1:8765/`。这个地址只有你自己的电脑能访问，外面的人访问不到。

### 4.2 准备你的 CSV

不同券商导出 CSV 的方式不同：

**Interactive Brokers（IBKR）：**
1. 登录网页端 → 左侧菜单 "Performance & Reports"
2. → "Statements" → "Activity"
3. → 选择时间范围 → 格式选 "CSV"
4. 下载得到的文件直接上传即可

**Binance：**
1. 登录网页端 → 右上角头像 → "User Center"
2. → "Account" → "Order History"
3. → "Export" → 选时间范围 → 下载
4. 也可以在 App 里：订单 → 成交记录 → 导出

**Coinbase：**
1. 登录网页端 → 右上角 "Settings"
2. → "Statements"
3. → "Generate Account Report" → 选 "Transaction History" → CSV
4. 下载并上传

**通用 CSV（自己手动整理）：**

如果你在其他平台或者自己记录持仓，可以手动创建一个表格（Excel 或 Google Sheets），列名包含以下三个（大小写不敏感，允许有其他列）：

| symbol | quantity | cost |
|--------|----------|------|
| NVDA | 10 | 450.00 |
| BTC | 0.5 | 60000 |

导出为 CSV 格式即可上传。`cost` 是每单位的成本价（买入价），不是总成本。

### 4.3 拖进去后看着仪表盘怎么读

**Allocation Donut（持仓饼图）**

一个圆环图，每个颜色代表你持仓里的一只资产，扇区大小代表该资产占你总持仓价值的比例。鼠标悬停可以看到具体比例。

- 看这张图的重点：有没有某只资产比例过大（比如超过 50%）？集中度太高意味着这只票涨你就赚多，跌你就亏多，波动会很大。
- 术语：这就是"Concentration Risk（集中风险）"——一个篮子里放了太多鸡蛋。

**P&L Bar Chart（盈亏棒图）**

每只资产一根条形柱，向上（绿色）= 盈利，向下（红色）= 亏损。柱子高度代表百分比涨跌幅，不是绝对金额。

- 看这张图的重点：有没有某只票亏损特别深？如果一只票已经跌了 30%，你要考虑它的逻辑有没有变化，还是只是市场情绪暂时的波动。

**AI 解读面板（4 个板块）**

Claude 根据你的持仓数据写的白话总结，分四个部分：

- **你持仓是啥（What You Hold）**：一句话概括你持仓的整体风格。比如"你的持仓以美股科技股为主，高风险高弹性，对大盘波动敏感"。
- **什么在赚（Working）**：列出目前盈利的持仓，附一句话说明原因。
- **什么在亏（Not Working）**：列出目前亏损的持仓，附一句话说明现状。如果没有亏损的会写"none today"。
- **要警惕啥（Watch）**：1-2 句话，指出你持仓里最值得注意的风险。比如集中度太高、某个行业占比过多、或者某只票的波动率特别大。

### 4.4 隐私提醒

- **只跑本地**：Portfolio Explorer 的服务器绑定在 `127.0.0.1`（本机回环地址），外网完全访问不到。即使你在公共 WiFi 也不会暴露。
- **CSV 不进 git**：`portfolios/` 文件夹已被 `.gitignore` 排除。即使你用 git 管理这个项目，上传的 CSV 也绝对不会被 commit 或推送到 GitHub。
- **AI 调用方式**：你的持仓数据会被发给 Anthropic 的 API 用于生成解读文字。Anthropic 的数据政策里不允许用 API 调用的数据训练模型。如果你对这个有顾虑，可以在上传前把持仓量改成非真实数字（只保留比例结构），解读质量不会受太大影响。

---

## 5. 常见情况怎么办

### "今天数据没刷新"

**可能原因 1：周末/美国假日**

yfinance 的美股数据在周末和美国假日没有更新，所以 SPY/VIX 等数字会显示上一个交易日的值。这是正常的，不是 bug。加密货币数据 7×24 小时都有。

**可能原因 2：数据源暂时挂了**

fetcher 会在网络请求失败时返回 `None`，不会让整个程序崩溃。如果某个数据源今天请求超时，对应的格子会显示空值或占位符，其他数据不受影响。通常过一会儿重跑就好了。

**排查方法：**

```bash
# 查看最近的日志（如果用 launchd 自动跑的话）
cat ~/.../morning-brief/.launchd.err.log | tail -20
```

### "AI commentary 是占位的"

如果 Headline 那里显示的是"(set ANTHROPIC_API_KEY in .env to enable AI commentary)"，说明 API Key 没有配置好。

**排查步骤：**

1. 打开项目文件夹里的 `.env` 文件（Mac Finder 里默认是隐藏的，用 Terminal `open .env` 打开）
2. 确认 `ANTHROPIC_API_KEY=` 后面是你真实的 Key，不是 `sk-ant-replace-me`
3. 确认 Key 前后没有多余的空格
4. 保存文件后重跑

如果 Key 是对的但 AI 还是不出现，可能是 Anthropic API 暂时不可用，或者你的账户余额不足——登录 [console.anthropic.com](https://console.anthropic.com/) 检查。

### "CSV 上传报错"

**常见情况：列名不匹配**

通用 CSV 解析要求列名包含 `symbol`、`quantity`、`cost` 三个关键词（大小写不敏感，允许有其他列）。IBKR / Binance / Coinbase 的标准导出格式已内置识别。

**排查方法：**

用 Excel 或 Numbers 打开你的 CSV，看第一行的列名是什么。如果是自制 CSV，确认包含这三列。

**常见错误：**

- 成本列叫 `avg_cost` 或 `buy_price` → 改成 `cost`
- 数量列叫 `amount` → 改成 `quantity`
- 符号列叫 `ticker` → 改成 `symbol`

### "想加一个新标的进 watchlist"

打开项目文件夹里的 `config/watchlist.json`，用任意文本编辑器编辑：

- `equities` 数组：添加美股代码，格式参考现有条目，`symbol` 是 yfinance 能识别的代码（比如 `"AAPL"`、`"MSFT"`）
- `crypto` 数组：添加加密货币，`symbol` 是你想显示的名字，`coingecko_id` 是 CoinGecko 上的 ID（比如 `"bitcoin"`、`"ethereum"`、`"solana"`）
- `overview` 数组：这是每日大盘概览的 9 个位置，可以替换成你更关注的指标

CoinGecko ID 查找方法：在 [coingecko.com](https://www.coingecko.com/) 搜索代币名，进入详情页，URL 里最后一段就是 ID，比如 `coingecko.com/en/coins/bitcoin` 里的 `bitcoin`。

### "想跨设备看"

**iPhone 看历史快照（只读，零安装）：**

1. 把项目放进 iCloud Drive（把文件夹拖到 `~/Library/Mobile Documents/com~apple~CloudDocs/`，或者直接在 Finder 把文件夹拖进 iCloud Drive）
2. iPhone 打开"文件"App → iCloud Drive → 找到 morning-brief → demos → 点击当天的 `.html` 文件
3. 用 Safari 打开，所有图表和 AI 解读都可以看

**用 Git 同步到其他电脑：**

1. 在 GitHub 创建一个私有仓库（注意选 Private，不要 Public）
2. `git remote add origin git@github.com:你的用户名/morning-brief.git`
3. 每次跑完加 `--commit` 参数把快照提交：`python morning_brief.py --commit --push`
4. 其他电脑 `git pull` 就能拿到最新快照

---

## 6. 名词术语表（专门给金融小白）

**VIX（波动率指数，Volatility Index）**
衡量市场"紧张程度"的指标，由芝加哥期权交易所计算。简单理解：VIX 越高，市场越怕。低于 20 = 市场平静，高于 25 = 市场紧张，高于 35 = 恐慌。不是价格，是"情绪温度"。

**DXY（美元指数，Dollar Index）**
追踪美元对欧元、日元、英镑、瑞郎、加元、瑞典克朗六种货币的综合强弱。DXY 涨意味着美元升值，通常对黄金和比特币有压力。DXY 100 是常用的心理关口。

**F&G（恐惧贪婪指数，Fear & Greed Index）**
0 到 100 的市场情绪指数。0 = 极度恐惧（所有人都在卖），100 = 极度贪婪（所有人都在追）。这里指的是加密货币市场的 F&G，由 alternative.me 发布，综合了价格波动率、交易量、社交媒体情绪等多个维度。

**Funding Rate（资金费率）**
加密货币永续合约市场上的特有机制。做多的人需要定期支付费用给做空的人（或反之），用来让合约价格贴近现货价格。费率为正 = 多头支付给空头，说明市场偏多（看涨情绪浓）；费率为负 = 空头支付给多头，说明市场偏空。长期极正说明市场可能过热。

**Long/Short Ratio（多空比）**
合约市场上持有做多仓位的账户数量，除以持有做空仓位的账户数量。比例大于 1 说明多头更多，市场偏乐观；小于 1 说明空头更多，市场偏悲观。

**ETF 净流入（ETF Net Flow）**
每天流入 ETF 的新资金减去流出的资金。净流入为正说明投资者在买入这只 ETF，资金在入场；净流出为负说明投资者在卖出，资金在离场。BTC 现货 ETF 的资金流向反映机构对 BTC 的态度。

**Allocation（持仓分配）**
你各资产占总持仓价值的比例。比如你总共有 $10,000，其中 $5,000 在 NVDA，那 NVDA 的 allocation 就是 50%。

**P&L（盈亏，Profit and Loss）**
当前市值减去成本的差值。P&L 为正 = 盈利，为负 = 亏损。通常用百分比表示（比如 +15% 或 -8%）。

**Cost Basis（成本基础）**
你买入某资产时的平均成本价。如果你分三次买 BTC，每次价格不同，cost basis 就是加权平均买入价。P&L 就是用当前价格减成本基础算出来的。

**Concentration Risk（集中风险）**
持仓过度集中在单一资产、单一行业或单一市场的风险。典型例子：90% 仓位都在 BTC，如果 BTC 跌 50%，你的总资产就少了 45%。分散持仓可以降低集中风险。

**Liquidity Tone（流动性基调）**
对当天市场整体资金流向和风险偏好的一句话描述。"Risk-on"= 资金在流向高风险资产（股票、加密货币），市场情绪乐观；"Risk-off"= 资金在撤离风险资产，流向黄金、国债等避险资产，市场情绪悲观。

**Drawdown（回撤）**
从一个高点到低点的跌幅。比如 BTC 从 $70,000 跌到 $50,000，回撤就是 28.6%。最大回撤（Max Drawdown）是历史上最大的跌幅区间，是衡量风险的重要指标。

**ETF（Exchange-Traded Fund，交易所交易基金）**
一种在股票交易所上市交易的基金。SPY 是追踪标普 500 的 ETF，你买一股 SPY 就等于持有了一小份 500 家公司的股票组合。BTC 现货 ETF（如 IBIT、FBTC）让传统金融机构可以通过股票账户持有比特币。

**SRI（Subresource Integrity，子资源完整性）**
一种网页安全技术。HTML 文件里的外部脚本会附带一串校验码，浏览器下载脚本后会验证内容是否和校验码匹配。如果有人篡改了 CDN 上的脚本，你的浏览器就会拒绝执行，防止被注入恶意代码。

---

## 7. 不要碰的东西

**不要把 `.env` 文件 commit 进 git**

`.env` 里存着你的 `ANTHROPIC_API_KEY`。这个文件已经被 `.gitignore` 排除，正常操作不会进入 git——但如果你手动 `git add .env`，就会把你的密钥暴露到 GitHub 上。一旦密钥泄露，任何人都可以用你的账户调用 API，产生费用。泄露了要立刻去 Anthropic Console 撤销旧 Key，生成新的。

**不要把 `portfolios/` 里的 CSV 截图发给别人**

这里面有你真实的持仓数量和成本价，属于敏感财务信息。`portfolios/` 已被 `.gitignore` 排除，不会同步到 GitHub。但截图或直接发文件是你自己的行为，工具管不了。

**不要修改 `lib/` 里的代码除非你测过**

`lib/` 里是核心逻辑，所有功能都通过 `tests/` 里的 35 个测试用例覆盖。如果你改了 `lib/` 的代码，跑一下 `.venv/bin/pytest tests/` 确认没有测试失败，再使用。

**不要把 ANTHROPIC_API_KEY 截图分享给别人**

密钥是一串字符，截图后别人可以直接用。不要在屏幕分享、截图分享、任何地方展示这个 Key，即使是 `sk-ant-` 开头的前几位也尽量避免完整截图。

---

## 8. 还在做什么（Roadmap 快照）

P2 阶段计划中，以下是最期待的 5 条：

1. **链上指标（LTH-MVRV / NUPL / SOPR）** — 把 Day1Global 的 13 个指标打完整，BTC 抄底分会更准，特别是长期持有者的行为指标
2. **PDF 财报上传 → Claude 解读** — 把一份财报 PDF 拖进来，Claude 帮你提取最重要的 3-5 个要点，用白话写出来
3. **GitHub Pages 公网快照** — 用 `--commit --push` 自动把每天的 HTML 快照推到 GitHub Pages，生成一个公开链接，发给任何人都能看，不需要附件
4. **Telegram / Mac 通知** — 当 BTC 抄底分进入极端区（低于 15 或高于 85）时，自动推送通知到你的手机
5. **Fund Finance 行业镜头** — 追踪电力电子、半导体等欧洲工业相关 ETF 的资金流向，专门为 UniCredit 申请那类岗位定制市场视野

完整 Roadmap 见 `README.md` 里的 "Roadmap (P2)" 章节。
