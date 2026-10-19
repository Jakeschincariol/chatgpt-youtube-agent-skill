# The YouTube agent skill

Eleven ChatGPT skills that run a YouTube channel. Free, MIT, no signup, no API key, nothing to
connect.

One of them writes your script off 21 hook formulas and scores the hook before you waste a take on
it. One lints the title and the thumbnail as a single pairing, because writing them separately is
why half of your click surface says the same thing twice. One reads your audience-retention export
and tells you the exact second people left and what you were saying when they did. One turns a
transcript into an edit decision list. One finds the Shorts already hiding inside a long video. One
goes and finds what is working in your niche and ranks it by how far each video beat its own
channel, not by how big the channel is.

**Nothing gets published until you do it.** These skills write. You upload.

## Install and run locally

This repository contains eleven skill instruction folders and six standalone Python scripts.
Cloning the repository does not, by itself, install these skills into the ChatGPT Android app
or give ChatGPT access to files stored in Termux.

To obtain the project and run its tests locally:

```bash
git clone https://github.com/adrianopoggianella-sketch/chatgpt-youtube-agent-skill.git
cd chatgpt-youtube-agent-skill
python3 -m unittest discover -s tests -v
```

If you already cloned the repository, run commands from its existing directory instead of
cloning again. The Python scripts can be run directly with Python 3; see the usage examples below.

## The eleven

| skill | what it does |
|---|---|
| `yt-script` | writes the script off 21 hook formulas, scores the hook |
| `yt-package` | title and thumbnail linted as one pairing |
| `yt-viral` | finds what is working in your niche, ranked by channel-relative lift |
| `yt-retention` | reads your retention export, names the second people left |
| `yt-edit` | transcript to an edit decision list, dead air flagged |
| `yt-plan` | the week's upload schedule |
| `yt-comment` | drafts replies in your voice |
| `yt-seo` | description, tags, and search surface |
| `yt-chapters` | chapter markers off the transcript |
| `yt-shorts` | finds the Shorts hiding in a long video |
| `yt-audit` | reads a channel and says what is actually wrong |

## Script usage

Run these commands from the repository root with Python 3.

### Audience retention

```bash
python3 skills/yt-retention/retention.py retention.csv
python3 skills/yt-retention/retention.py retention.csv --json
python3 skills/yt-retention/retention.py retention.csv --axis seconds
python3 skills/yt-retention/retention.py retention.csv --axis percent --duration 600
python3 skills/yt-retention/retention.py retention.csv --transcript transcript.srt
```

Use `--axis auto`, `--axis percent`, or `--axis seconds` to select the time axis. `--duration` supplies video duration and `--transcript` associates transcript text with retention drops.

### Edit decision list

```bash
python3 skills/yt-edit/deadair.py transcript.srt
python3 skills/yt-edit/deadair.py transcript.srt --floor 0.35 --json
```

Accepts SRT/VTT transcripts and Whisper JSON. The default minimum gap is 0.45 seconds. The script suggests cuts; it does not edit video files.

### YouTube chapters

```bash
python3 skills/yt-chapters/chapters.py transcript.srt
python3 skills/yt-chapters/chapters.py transcript.srt --target 8 --json
```

Accepts SRT/VTT transcripts and Whisper JSON. The generated list must start at `00:00`, contain at least three chapters, and give each chapter at least 10 seconds. Review the draft titles before publishing.

## Your voice

`templates/voice.md` is a template for a personal channel voice profile. For a compatible local
agent that can read your filesystem, copy and complete it with:

```bash
mkdir -p ~/.codex/youtube
cp templates/voice.md ~/.codex/youtube/voice.md
```

Only skills whose instructions explicitly reference this profile are configured to use it.
ChatGPT on Android does not automatically read files from Termux. When working in ChatGPT,
provide the relevant voice-profile text in the conversation or attach the file when supported.

## The tools

Six dependency-free Python scripts, no packages to install: `hookscore.py`, `title.py`,
`deadair.py`, `chapters.py`, `retention.py`, `swipe.py`.

MIT.
