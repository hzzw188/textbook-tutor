# Textbook Tutor · 课本老师

把一条 B 站课程链接或一本电子书交给 Codex，让它从你卡住的地方开始教。每次学一个知识点，先看一个例子，再自己做一道小题。你答完，它会根据你的思路决定是继续往下讲，还是换个更容易理解的例子。

## 两种用法

### 1. 跟着 B 站教程学

把视频链接发给 Codex。合集链接里的 `p` 指定集数，没写 `p` 时默认第 1 集。配置好下方的转写工具后，脚本会先找公开字幕，取不到时再尝试用本地语音识别生成文字稿。

```text
$textbook-tutor 教我这节微信小程序课：
https://www.bilibili.com/video/BV18VTW6TEwE/?p=37

我卡在 wx:for。用一个小例子讲清楚列表里有几项，页面就会显示几行。
讲完出一道小题，等我答完再给反馈。
```

### 2. 按电子书的章节学

把电子书文件发给 Codex，告诉它书的章节、页码或你没看懂的句子。可以用 PDF、EPUB、Word、Markdown 等资料，能否读取取决于当前环境。扫描版 PDF 如果无法提取文字，可以直接发相关页的截图。

```text
$textbook-tutor 按我发的《高等数学》上册教我。
从第一章第三节「函数的极限」开始。
我不明白为什么函数在某一点没有定义，却还能求它的极限。
先举一个例子，讲完让我自己做一道类似的题。
```

### 看看学到哪了

学完可以说「看一下我的学习进度」。学习地图按知识点展示 0–5 级，依据你的练习表现更新。还没做过检查的知识点会标为「待评估」。下面是一个示例。

```text
主题：小程序列表渲染
列表的作用     [████░░░░░░]  2/5  能跟着示例做
渲染每一项     [██░░░░░░░░]  1/5  认识概念  ← 当前
读取对象字段   [··········]  待评估
```

想换个对话接着学，可以先说「导出学习进度」，保存它给你的简短记录，下次和教材一起发过去。

## 安装到 Codex

把仓库克隆到用户级 Skill 目录。若已装过同名 Skill，先确认已有副本的位置，更新那一份即可。

**Windows PowerShell 7**

```powershell
$skillsDir = Join-Path $env:USERPROFILE '.agents\skills'
$skillDir = Join-Path $skillsDir 'textbook-tutor'
New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
git clone https://github.com/hzzw188/textbook-tutor.git $skillDir
```

**macOS / Linux**

```bash
skill_dir="$HOME/.agents/skills/textbook-tutor"
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/hzzw188/textbook-tutor.git "$skill_dir"
```

打开 Codex，在对话里输入 `$` 并选择 `textbook-tutor`。列表没刷新时，重启 Codex 再试。电子书模式可以直接用，下面的转写依赖用于 B 站模式。

[Codex Skill 安装与使用文档](https://learn.chatgpt.com/docs/build-skills)

## 配置 B 站转写（可选）

仓库里的 [bilibili_lesson.py](scripts/bilibili_lesson.py) 负责定位分集并调用独立安装的转写工具，默认到当前用户的主目录下找 `bilibili-transcript`。下面用 Python 3.12 创建脚本预期的 `.venv312` 环境，并检出兼容的上游版本。先确保 `git`、Python 3.12 和 FFmpeg 可用，`ffmpeg -version` 能在终端运行。首次语音识别可能需要联网下载模型。

**Windows PowerShell 7**

```powershell
$toolDir = Join-Path $env:USERPROFILE 'bilibili-transcript'
git clone https://github.com/kqint/bilibili-transcript.git $toolDir
git -C $toolDir checkout --detach 9800dc3d066129a48213221c67ac5bcf78b326e0
py -3.12 -m venv (Join-Path $toolDir '.venv312')
$toolPython = Join-Path $toolDir '.venv312\Scripts\python.exe'
& $toolPython -m pip install -r (Join-Path $toolDir 'workflow\requirements.txt')
$lessonScript = Join-Path $skillDir 'scripts\bilibili_lesson.py'
& $toolPython $lessonScript 'https://www.bilibili.com/video/BV18VTW6TEwE/?p=37'
```

如果没有 `py` 命令，可以用自己的 Python 3.12 可执行文件运行 `-m venv`。

**macOS / Linux**

```bash
tool_dir="$HOME/bilibili-transcript"
git clone https://github.com/kqint/bilibili-transcript.git "$tool_dir"
git -C "$tool_dir" checkout --detach 9800dc3d066129a48213221c67ac5bcf78b326e0
python3.12 -m venv "$tool_dir/.venv312"
tool_python="$tool_dir/.venv312/bin/python"
"$tool_python" -m pip install -r "$tool_dir/workflow/requirements.txt"
"$tool_python" "$skill_dir/scripts/bilibili_lesson.py" 'https://www.bilibili.com/video/BV18VTW6TEwE/?p=37'
```

在安装 Skill 时的同一终端运行上面的命令，或者先把 `$skillDir`（Windows）或 `$skill_dir`（macOS / Linux）设为实际的 Skill 目录。成功后可把脚本输出的 `.doc.md` 交给 Codex。安装在其他位置时，在运行脚本的命令末尾加上 `--tool-dir "实际目录"`，或在聊天时把路径告诉 Codex。

同一分集已有 `.doc.md` 时会直接复用。首次提取需要能访问 B 站。脚本以无浏览器 Cookie 的方式运行，带登录限制或音频不可访问的课程可以提供已有字幕、笔记或截图。

[bilibili-transcript 项目与安装说明](https://github.com/kqint/bilibili-transcript)

## 仓库文件

- [SKILL.md](SKILL.md) 定义教学流程、练习反馈、复习和学习地图。
- [scripts/bilibili_lesson.py](scripts/bilibili_lesson.py) 获取 B 站分集信息并调用转写工具。
