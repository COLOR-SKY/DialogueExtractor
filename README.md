# DialogueExtractor
## [中文文档](README_ZH.md)
A tool that extracts video clips using subtitles

# Video Demo
Video Demo: https://www.bilibili.com/video/BV1Ba41187cP/

# Pre-requisit
* `ffmpeg ffprobe` added to system path
* Basic features: pip install -r requirements.txt
* Beta features: pip install -r requirements-beta.txt

# Beta Features
Change line#16 in DialogueExtractor.py to **TRUE** to enable beta features

# FAQ
* UnicodeDecodeError: "utf-8" codec can't decode byte 0x.... : invalid continuation byte.

* Your subtitle file may not be encoded with "utf-8", please double check.