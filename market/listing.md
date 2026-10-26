# 推广素材：JD 红旗检测

> 把「抗压能力强」「薪资面议」翻回原形，并告诉你面试该问什么。

下面每条文案都用本仓脚本测过 AI 味。

---

## 一、GitHub 仓库元信息

**About**：见仓库设置（已由发布脚本写入）。

**Social preview**：`market/social-preview.png`（1280×640，已生成）。


---

## 二、小红书

**标题（5 选 1）**

1. 面了 12 家公司，我发现坑都写在 JD 里
2. 「抗压能力强」这五个字，我劝你别当真
3. 我把招聘 JD 里的黑话做了一个翻译器
4. 薪资面议的岗位，我最后都拒了
5. 这家公司值不值得面，看这三个地方

**正文**

面了两年，我慢慢发现一件事：**公司的坑，大部分提前写在 JD 里了**。

只是它用了自己的说法。

「抗压能力强」= 会加班，且不打算给加班费。
「一人多岗」= 编制不够，一个人干三个人的活。
「不要只看钱」= 钱给不到位。
「薪资面议」= 不想写，或者想看你报多少。

我做了一个脚本，把这些话翻回来，还顺手给每一条配了「面试该怎么问」。

比如「抗压能力强」这条，别问「你们加班多吗」（一定答「还好」），要问：

「这个岗位上一任做的人是多久之前离开的？大概因为什么？」

一句话能问出岗位稳定性、真实强度、离职原因是不是和加班有关。

脚本还有个我觉得最有用的功能：**检查 JD 里「没写什么」**。

没写薪资区间、没写五险一金、没写工作时间、没写团队规模——这四项缺失，比写了一条不利条款更值得警惕。

实测：一份满是红旗的 JD 跑 **100 分**，一份正常的 JD 跑 **0 分**。同一套规则。

零依赖，一个 py 文件，MIT。

敢不敢把你正在看的那份 JD 跑一下？评论区报个分数 👇

`#求职` `#面试` `#招聘` `#避坑` / `#打工人` `#找工作` `#简历` `#职场` / `#我的求职记录`

**首评（置顶）**

补一句：它不是告诉你「别去」，是告诉你「去之前问这三句」。除了明显违法的（押金、无薪试岗），其他都该你自己判断——「狼性 + 高薪」对有些人就是好选择。


---

## 三、X / Twitter（英文）

```
Job postings tell you exactly what the company is. They just use their own vocabulary.

Built a linter for it:

→ 抗压能力强 = overtime, unpaid
→ 一人多岗 = one person, three jobs
→ 薪资面议 = won't write it, wants to see your number first
→ 不要只看钱 = the money is bad

Scores 0-100, and every hit comes with the exact phrase + a question to ask in the interview (not "do you work late" — they'll say no).

Best part: it also flags what's *missing*. No salary range, no social insurance, no working hours, no team size. Absence is louder than any bad clause.

Calibration: toxic JD 100, normal JD 0. Same rules.

Zero deps, MIT, Chinese-first.
```


---

## 四、Show HN

```
Show HN: JD-redflag – score job postings for red flags

Every job posting is a company describing itself honestly, in its own dialect.
"Thrives under pressure" means overtime. "Wears many hats" means three jobs.
"Competitive salary" means they won't write a range.

So I turned the dialect into a scoring tool. ~50 regex rules across six
dimensions (hours, comp traps, scope creep, culture language, vague promises,
compliance risks), each rule carrying the real meaning plus a question to ask
in the interview.

The part I ended up using most: it also reports omissions. No salary range, no
mention of social insurance, no working hours, no team size. In my sample, a
posting with four omissions was worse than one with a single bad clause.

Calibration on two fixtures: toxic posting scores 100, clean one scores 0.

Caveats: rules match words, not context. A genuinely well-paying "high pressure"
shop still scores high — the score is a prompt to ask questions, not a verdict.
And the lexicon is Chinese-first, so the value to an English audience is mostly
the design rather than the word list.

github.com/zhbehx/jd-redflag
```


---

## 五、发布清单

| 渠道 | 素材 | 关键动作 |
| --- | --- | --- |
| GitHub | Release v1.0.0 | 已发布 |
| X | 上面的英文稿 | 配终端截图，分数可见 |
| Show HN | 上面的 HN 稿 | 周二至周四 UTC 14:00–16:00 |
| 社群 / 即刻 | 一句话 + 链接 | 只讲一个点，别贴 README |