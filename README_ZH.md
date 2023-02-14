# DialogueExtractor
## [English](README.md)
使用字幕提取视频片段的工具


# 演示视频
[演示视频（点击跳转）](https://www.bilibili.com/video/BV1Ba41187cP/)

# 依赖项
* 安装[ffmpeg](https://ffmpeg.org/),并将其`bin`目录添加到系统的环境变量。

# 安装
* 安装[Miniconda](https://docs.conda.io/en/latest/miniconda.html)。
* 使用`conda create -n Dex python=3.7`创建Python3.7虚拟环境。
* 在`DialogueExtractor_ch`下打开cmd,使用`conda activate Dex`打开虚拟环境。
## 基础功能
* 在虚拟环境下，使用`pip install -r requirements.txt`,安装所需的包。
* 在虚拟环境下，使用`python DialogueExtractor.py`打开程序。
### 打包为exe(建议)
* 在虚拟环境下，使用`pip install pyinstaller`,安装所需的包。
* 在虚拟环境下，使用`pyinstaller DialogueExtractor_exe.spec`来打包，完成后将在`dist`目录下生成exe文件。
* 注意：本exe仍然依赖`ffmpeg`,但不在需要`Miniconda`与`Python3.7`的环境。可更改exe文件名和位置，但请注意运行程序会当在前路径下生成`temp`文件夹和`config.json`文件。
## 测试功能
* 注意：如需打包exe,请在额外安装测试功能所需包之前进行打包。安装额外的包后打包的exe文件体积将显著增大，但仍然可以运行（启动时间变长）。
* 注意：不要尝试打包测试功能为exe，目前打包后的exe无法正常工作且体积庞大。要使用测试功能只能使用源码。
* 使用`conda install -c conda-forge ffmpeg libsndfile`安装所需的包。
* 在虚拟环境下，使用`pip install -r requirements-beta.txt`,安装所需的包。
* 前往[这里](https://github.com/explosion/spacy-models/releases/download/zh_core_web_lg-2.3.1/zh_core_web_lg-2.3.1.tar.gz)下载`zh_core_web_lg-2.3.1.tar.gz`（访问github可能需要梯子）。
* 完成下载后，在虚拟环境下，使用`pip install zh_core_web_lg-2.3.1.tar.gz`安装下载的文件。
* 使用`conda install pytorch torchvision torchaudio -c pytorch -y`安装所需的包。
* 打开`DialogueExtractor.py`,将第16行的`ENABLE_BETA = False`改为`ENABLE_BETA = True`，之后在虚拟环境下使用`python DialogueExtractor.py`打开带有测试功能的程序。（第一次打开会下载必要文件，耐心等待即可）。

# FAQ（常见的问题解答）
* UnicodeDecodeError: "utf-8" codec can't decode byte 0x.... : invalid continuation byte.
* 您的字幕文件可能未使用 “utf-8” 编码，请仔细检查。