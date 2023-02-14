"""
Author: color·sky
Date: 2022/02/14(为什么是情人节)
Modified by: sgmklp
Modified Date: 2023/02/14(又到情人节了)
"""
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QFileDialog, QMenu
from datetime import datetime, timedelta
from pysubparser import parser
from typing import List
import subprocess
import shutil
import json
import os
import re

ENABLE_BETA = False


def denoise(inputFile):
    filename = inputFile
    tempfilename = filename.replace(".mp4", "_temp.mp4")
    wavfilename = filename.replace(".mp4", ".flac")
    print("extracting audio")
    ff1 = f"ffmpeg -y -loglevel quiet -i \"{filename}\" -q:a 0 -map a \"{wavfilename}\""
    subprocess.call(ff1, shell=True)
    print("done extraction...")
    print("begin denoising")
    if os.path.exists(wavfilename[:-5]):
        shutil.rmtree(wavfilename[:-5])
    separator.separate_to_file(
        wavfilename, wavfilename[:-5], filename_format='{instrument}.{codec}')
    ff2 = f"ffmpeg -y -loglevel quiet -i \"{filename}\" -i \"{wavfilename[:-5]}/vocals.wav\" -vcodec copy -map 0:0 -map 1:0 \"{tempfilename}\""
    subprocess.call(ff2, shell=True)
    if os.path.exists(filename):
        os.remove(filename)
    if os.path.exists(wavfilename[:-5]):
        shutil.rmtree(wavfilename[:-5])
    if os.path.exists(wavfilename):
        os.remove(wavfilename)
    os.rename(tempfilename, filename)
    if os.path.exists(tempfilename):
        os.remove(tempfilename)
    print(f"done denoising: {filename}")


class ProjectSetup:
    inputFolder = None
    outputFolder = None
    videoCaptionPairs = {}
    dialogue = []
    filtedDialogue = []

    def __init__(self) -> None:
        if "config.json" in os.listdir("./"):
            with open("config.json", encoding="utf-8") as json_file:
                s = json_file.read()
                if not s:
                    data = {}
                else:
                    data = json.loads(s)
                self.inputFolder = data.get("inputFolder")
                self.outputFolder = data.get("outputFolder")

    def fetchEpisodeCaptionPairs(self):
        """Look into the inputFolder and fetch all video:caption pairs"""
        videoFormats = [".mkv", ".mp4", ".avi", ".mov", ".wmv"]
        captionFormats = [".sub", ".ass", ".srt", ".ssa"]
        videoFiles = []
        captionFiles = []
        for filename in os.listdir(self.inputFolder):
            if any([videoFormat in filename for videoFormat in videoFormats]):
                videoFiles.append(filename)
            if any([
                    captionFormat in filename
                    for captionFormat in captionFormats
            ]):
                captionFiles.append(filename)
        self.videoCaptionPairs = {}
        for videoFile in videoFiles:
            video_name = videoFile.split(".")[0]
            for cap_extension in captionFormats:
                try:
                    with open(f"{self.inputFolder}/{video_name}{cap_extension}") as caption_file:
                        pass
                    self.videoCaptionPairs[videoFile] = f"{video_name}{cap_extension}"
                    break
                except FileNotFoundError:
                    continue

    def updateDialogue(self, itemIndex):
        self.dialogue = []
        if not self.videoCaptionPairs:
            return
        if itemIndex == -1:
            return
        if itemIndex == 0:
            filenames = list(self.videoCaptionPairs.values())
        else:
            filenames = [list(self.videoCaptionPairs.values())[itemIndex - 1]]
        for i, filename in enumerate(filenames):
            episode = i + 1 if len(filenames) > 1 else itemIndex
            subtitles = parser.parse(f'{self.inputFolder}/{filename}')
            for subtitle in subtitles:
                self.dialogue.append(
                    (episode, subtitle.start.strftime('%H:%M:%S'), subtitle.end.strftime('%H:%M:%S'), subtitle.text))


class Clip:
    def __init__(self, inputFile, e, st, et, d, lo=0, ro=0):
        self.episode = e
        self.startTime = st
        self.endTime = et
        self.dialogue = d
        self.inputFile = inputFile
        self.outputFile = "".join(
            x for x in f"{e}_{st.replace(':','_')}_{et.replace(':','_')}_{d}"
            if x.isalnum() or x in ('.', '_')) + ".mp4"
        self.leftOffset = lo
        self.rightOffset = ro

    def __repr__(self):
        return f"{self.inputFile} -> {self.outputFile}"

    def getClipFilename(self, outputDir=None, denoise_=False):
        if not outputDir:
            outputDir = "./temp"
        # print(self.__repr__() +
        #       f" lo:{self.leftOffset}, ro:{self.rightOffset}")
        start_dt = datetime.strptime(
            self.startTime, '%H:%M:%S') - timedelta(seconds=self.leftOffset)
        end_dt = datetime.strptime(
            self.endTime, '%H:%M:%S') + timedelta(seconds=self.rightOffset)
        duration = str(end_dt - start_dt)
        # Convert begin-end time into %H:%M:%S format
        start_dt = str(start_dt).split(" ")[-1]
        outputFileName = f"{outputDir}/{self.outputFile}"
        ffmpeg_instruction = f"ffmpeg -y -ss {start_dt} -i \"{self.inputFile}\" -t {duration} -vcodec copy \"{outputFileName}\" -loglevel quiet"
        subprocess.call(ffmpeg_instruction, shell=True)
        if denoise_:
            denoise(outputFileName)
        print(f"Clip output to: {outputFileName}")
        return outputFileName


class Ui_MainWindow(object):
    projectSetup = ProjectSetup()
    filtered_dialogue = []
    folderChanged = False

    def getInputFolder(self, MainWindow):
        self.folderChanged = True
        data = {}
        try:
            with open("./config.json", encoding="utf-8") as json_file:
                s = json_file.read()
                if not s:
                    data = {}
                else:
                    data = json.loads(s)
        except FileNotFoundError:
            pass

        fileDir = QFileDialog.getExistingDirectory(
            MainWindow, 'Select input folder', data.get("inputFolder"))
        # Validate the selection
        if fileDir:
            self.projectSetup.inputFolder = fileDir
            data["inputFolder"] = fileDir
            with open("./config.json", "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False)
        else:
            return
        self.InputDirectory.setText(self.projectSetup.inputFolder)
        self.projectSetup.fetchEpisodeCaptionPairs()
        # Append Episodes into the EpisodeSelection
        self.EpisodeSelection.clear()
        for episodeName in ["All"] + list(
                self.projectSetup.videoCaptionPairs.keys()):
            self.EpisodeSelection.addItem(episodeName)

    def getOutputFolder(self, MainWindow):
        with open("./config.json", encoding="utf-8") as json_file:
            s = json_file.read()
            if not s:
                data = {}
            else:
                data = json.loads(s)
        fileDir = QFileDialog.getExistingDirectory(
            MainWindow, 'Select output folder', data.get("outputFolder"))
        # Validate the selection
        if fileDir:
            self.projectSetup.outputFolder = fileDir
            data["outputFolder"] = fileDir
            with open("./config.json", "w", encoding="utf-8") as json_file:
                json.dump(data, json_file, ensure_ascii=False)
        else:
            return
        self.OutputDirectory.setText(self.projectSetup.outputFolder)

    def updateDialogue(self):
        self.projectSetup.updateDialogue(self.EpisodeSelection.currentIndex())
        self.updateSearch()

    def updateSearch(self, clear_hist=True):
        self.tableWidget.clearContents()
        if clear_hist:
            self.filtered_dialogue = []
            for row in self.projectSetup.dialogue:
                e, st, et, d = row
                if self.SearchText.text():
                    if not re.findall(self.SearchText.text(), d):
                        continue
                self.filtered_dialogue.append((e, st, et, d))
        self.tableWidget.setRowCount(len(self.filtered_dialogue))
        for i, row in enumerate(self.filtered_dialogue):
            e, st, et, d = row
            if self.SearchText.text():
                if not re.findall(self.SearchText.text(), d):
                    continue
            item = QtWidgets.QTableWidgetItem(str(e))
            self.tableWidget.setItem(i, 0, item)
            item = QtWidgets.QTableWidgetItem(str(st))
            self.tableWidget.setItem(i, 1, item)
            item = QtWidgets.QTableWidgetItem(str(et))
            self.tableWidget.setItem(i, 2, item)
            item = QtWidgets.QTableWidgetItem(str(d))
            self.tableWidget.setItem(i, 3, item)
        self.ResultLabel.setText(
            f"<font color=\"gray\">找到 {len(self.filtered_dialogue)} 行结果</font>")

    def getClipFile(self) -> List[Clip]:
        selectedItems = self.tableWidget.selectedItems()
        if not selectedItems:
            return
        clips = []
        while selectedItems:
            e = selectedItems.pop(0).text()
            st = selectedItems.pop(0).text()
            et = selectedItems.pop(0).text()
            d = selectedItems.pop(0).text()
            inputFile = list(
                self.projectSetup.videoCaptionPairs.keys())[int(e) - 1]
            inputFile = f"{self.InputDirectory.toPlainText()}/{inputFile}"
            clip = Clip(inputFile, e, st, et, d, self.LOffsetSpinBox.value(),
                        self.ROffsetSpinBox.value())
            clips.append(clip)
        return clips

    def getConcateClipFilename(self, clips, output_folder=None, denoise_=False):
        if not clips:
            return
        start_time = str(clips[0].startTime).replace(":", "_")
        end_time = str(clips[-1].endTime).replace(":", "_")
        outputFilename = f"./temp/合并_{start_time}_{end_time}.mp4"
        if output_folder:
            outputFilename = f'"{output_folder}/合并_{start_time}_{end_time}.mp4"'

        # Write config file
        clip_names = []
        with open("./temp/concat.txt", "w") as config_file:
            for clip in clips:
                clipFilename = clip.getClipFilename()[7:]
                config_file.write(f"file '{clipFilename}'\n")
                clip_names.append(f"./temp/{clipFilename}")
        ffmpegScript = f"ffmpeg -f concat -safe 0 -i ./temp/concat.txt -c copy {outputFilename} -loglevel quiet"
        subprocess.call(ffmpegScript, shell=True)

        if denoise_:
            denoise(outputFilename)

        # Remove single clips
        [os.remove(clip_name)
         for clip_name in clip_names+["./temp/concat.txt"]]
        return outputFilename

    def previewSelected(self):
        # Clear tempfolder
        dir = './temp/'
        if not os.path.exists(dir):
            # Create a new directory because it does not exist
            os.makedirs(dir)
        for files in os.listdir(dir):
            path = os.path.join(dir, files)
            try:
                shutil.rmtree(path)
            except OSError:
                os.remove(path)
        # Acquire clip
        clips = self.getClipFile()
        if not clips:
            return
        if len(clips) == 1 or not self.ConcatenateCheckBox.isChecked():  # Only selected one clip
            clip = clips[-1]  # Only Preview the last selected file
            clipFilename = clip.getClipFilename(
                denoise_=self.DenoiseCheckBox.isChecked())
        else:
            clipFilename = self.getConcateClipFilename(
                clips, denoise_=self.DenoiseCheckBox.isChecked())
        print(clipFilename)
        ffplayScript = f"ffplay -x 800 -y 600  -autoexit {clipFilename}"
        if not self.PreviewCheckBox.isChecked():
            ffplayScript += " -nodisp"
        subprocess.call(ffplayScript, shell=True)
        print("Preview Finished")
        for files in os.listdir(dir):
            path = os.path.join(dir, files)
            try:
                shutil.rmtree(path)
            except OSError:
                os.remove(path)

    def exportSelected(self):
        clips = self.getClipFile()
        if not clips:
            return
        if self.ConcatenateCheckBox.isChecked() and len(clips) > 1:
            self.getConcateClipFilename(
                clips, self.OutputDirectory.toPlainText(), denoise_=self.DenoiseCheckBox.isChecked())
        else:
            for clip in clips:
                clipFilename = clip.getClipFilename(
                    self.OutputDirectory.toPlainText(), denoise_=self.DenoiseCheckBox.isChecked())

    def generateScript(self):

        print("Generate!")
        sentences = {}
        self.updateSearch(clear_hist=False)
        for row in range(self.tableWidget.rowCount()):
            e = self.tableWidget.item(row, 0).text()
            st = self.tableWidget.item(row, 1).text()
            et = self.tableWidget.item(row, 2).text()
            d = self.tableWidget.item(row, 3).text()
            info = {"e":e, "st":st, "et":et, "d":d}
            punct = ".,。，?!？！\s\r\n"
            kwd = re.sub(f"[{punct}]+","，", d)
            if not kwd:
                continue
            if kwd[-1] in punct:
                kwd = kwd[:-1]
            sentences[kwd] = info

        extracted_keys = extractive_summarize(sentences, self.SourceAmount.text(), self.TargetAmount.text(), self.RandomSeed.text())
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(len(extracted_keys))
        cursor = 0
        for k in extracted_keys:
            v = sentences.get(k)
            if not v:
                continue
            e, st, et, d = v["e"], v["st"], v["et"], v["d"]
            item = QtWidgets.QTableWidgetItem(str(e))
            self.tableWidget.setItem(cursor, 0, item)
            item = QtWidgets.QTableWidgetItem(str(st))
            self.tableWidget.setItem(cursor, 1, item)
            item = QtWidgets.QTableWidgetItem(str(et))
            self.tableWidget.setItem(cursor, 2, item)
            item = QtWidgets.QTableWidgetItem(str(d))
            self.tableWidget.setItem(cursor, 3, item)
            cursor += 1
        self.ResultLabel.setText(
            f"<font color=\"gray\">成功生成 {len(extracted_keys)} 行剧本</font>")

    def openAbout(self):
        url = QtCore.QUrl("https://space.bilibili.com/2181001")
        QtGui.QDesktopServices.openUrl(url)

    def resource_path(self, relative_path):
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)


    def setupUi(self, MainWindow):
        filename = self.resource_path(os.path.join("ico","icon.ico"))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(filename))
        MainWindow.setObjectName("MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(800, 600)
        MainWindow.setWindowIcon(icon)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Fixed,
                                           QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QtCore.QSize(800, 615))
        MainWindow.setMaximumSize(QtCore.QSize(800, 615))
        MainWindow.setAutoFillBackground(False)
        MainWindow.setAnimated(True)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        self.menu_About = QtWidgets.QMenu(self.menubar)
        self.menu_About.setObjectName("menu_About")
        MainWindow.setMenuBar(self.menubar)
        self.actionAuthor_color_sky = QtGui.QAction(MainWindow)
        self.actionAuthor_color_sky.setObjectName("actionAuthor_color_sky")
        self.menu_About.addAction(self.actionAuthor_color_sky)
        self.menubar.addAction(self.menu_About.menuAction())
        self.InputDirButton = QtWidgets.QPushButton(self.centralwidget)
        self.InputDirButton.setEnabled(True)
        self.InputDirButton.setGeometry(QtCore.QRect(689, 19, 101, 32))
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.InputDirButton.sizePolicy().hasHeightForWidth())
        self.InputDirButton.setSizePolicy(sizePolicy)
        self.InputDirButton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.InputDirButton.setObjectName("InputDirButton")
        self.OutputDirButton = QtWidgets.QPushButton(self.centralwidget)
        self.OutputDirButton.setEnabled(True)
        self.OutputDirButton.setGeometry(QtCore.QRect(689, 59, 101, 32))
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.OutputDirButton.sizePolicy().hasHeightForWidth())
        self.OutputDirButton.setSizePolicy(sizePolicy)
        self.OutputDirButton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.OutputDirButton.setObjectName("OutputDirButton")
        self.InputDirectory = QtWidgets.QTextEdit(self.centralwidget)
        self.InputDirectory.setEnabled(False)
        self.InputDirectory.setGeometry(QtCore.QRect(10, 20, 670, 30))
        self.InputDirectory.setObjectName("InputDirectory")
        self.OutputDirectory = QtWidgets.QTextEdit(self.centralwidget)
        self.OutputDirectory.setEnabled(False)
        self.OutputDirectory.setGeometry(QtCore.QRect(10, 60, 670, 30))
        self.OutputDirectory.setObjectName("OutputDirectory")
        self.EpisodeLabel = QtWidgets.QLabel(self.centralwidget)
        self.EpisodeLabel.setGeometry(QtCore.QRect(10, 100, 60, 30))
        self.EpisodeLabel.setObjectName("EpisodeLabel")
        self.EpisodeSelection = QtWidgets.QComboBox(self.centralwidget)
        self.EpisodeSelection.setGeometry(QtCore.QRect(45, 106, 200, 21))
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Preferred,
            QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.EpisodeSelection.sizePolicy().hasHeightForWidth())
        self.EpisodeSelection.setSizePolicy(sizePolicy)
        self.EpisodeSelection.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.EpisodeSelection.setObjectName("EpisodeSelection")
        self.EpisodeSelection.addItem("")
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        self.SearchText = QtWidgets.QLineEdit(self.centralwidget)
        self.SearchText.setGeometry(QtCore.QRect(45, 140, 745, 30))
        self.SearchText.setObjectName("SearchText")
        self.SearchLabel = QtWidgets.QLabel(self.centralwidget)
        self.SearchLabel.setGeometry(QtCore.QRect(10, 140, 60, 30))
        self.SearchLabel.setObjectName("SearchLabel")

        self.ScriptGenerateButton = QtWidgets.QPushButton(
            self.centralwidget)
        self.ScriptGenerateButton.setEnabled(True)
        self.ScriptGenerateButton.setGeometry(
            QtCore.QRect(660, 179, 131, 50))
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.ScriptGenerateButton.sizePolicy().hasHeightForWidth())
        self.ScriptGenerateButton.setSizePolicy(sizePolicy)
        self.ScriptGenerateButton.setFocusPolicy(
            QtCore.Qt.FocusPolicy.NoFocus)
        self.ScriptGenerateButton.setObjectName("ScriptGenerateButton")

        self.ScriptConfig = QtWidgets.QLabel(self.centralwidget)
        self.ScriptConfig.setGeometry(QtCore.QRect(660, 227, 300, 30))
        self.ScriptConfig.setObjectName("ScriptConfig")

        self.SourceAmount = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.SourceAmount.setGeometry(QtCore.QRect(660, 256, 40, 30))
        self.SourceAmount.setObjectName("SourceAmount")
        self.SourceAmount.setDecimals(1)
        self.SourceAmount.setMinimum(0.0)
        self.SourceAmount.setMaximum(9999999999)
        self.SourceAmount.setSingleStep(0.1)
        self.SourceAmount.setValue(0.3)

        self.TargetAmount = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.TargetAmount.setGeometry(QtCore.QRect(705, 256, 40, 30))
        self.TargetAmount.setObjectName("TargetAmount")
        self.TargetAmount.setDecimals(1)
        self.TargetAmount.setMinimum(0.0)
        self.TargetAmount.setMaximum(9999999999)
        self.TargetAmount.setSingleStep(0.1)
        self.TargetAmount.setValue(20)

        self.RandomSeed = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.RandomSeed.setGeometry(QtCore.QRect(750, 256, 40, 30))
        self.RandomSeed.setObjectName("RandomSeed")
        self.RandomSeed.setDecimals(0)
        self.RandomSeed.setMinimum(0)
        self.RandomSeed.setMaximum(9999999999)
        self.RandomSeed.setSingleStep(1)
        self.RandomSeed.setValue(233)

        self.DenoiseCheckBox = QtWidgets.QCheckBox(self.centralwidget)
        self.DenoiseCheckBox.setGeometry(QtCore.QRect(659, 291, 130, 45))
        self.DenoiseCheckBox.setChecked(False)
        self.DenoiseCheckBox.setObjectName("DenoiseCheckBox")

        self.ResultLabel = QtWidgets.QLabel(self.centralwidget)
        self.ResultLabel.setAlignment(
            QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.ResultLabel.setGeometry(QtCore.QRect(672, 138, 100, 35))
        self.ResultLabel.setObjectName("ResultLabel")
        self.ConcatenateCheckBox = QtWidgets.QCheckBox(self.centralwidget)
        self.ConcatenateCheckBox.setGeometry(QtCore.QRect(659, 355, 130, 45))
        self.ConcatenateCheckBox.setChecked(False)
        self.ConcatenateCheckBox.setObjectName("ConcatenateCheckBox")
        self.PreviewCheckBox = QtWidgets.QCheckBox(self.centralwidget)
        self.PreviewCheckBox.setGeometry(QtCore.QRect(659, 323, 130, 45))
        self.PreviewCheckBox.setChecked(False)
        self.PreviewCheckBox.setObjectName("PreviewCheckBox")
        self.LOffsetSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.LOffsetSpinBox.setGeometry(QtCore.QRect(710, 402, 60, 35))
        self.LOffsetSpinBox.setMinimum(-1000.0)
        self.LOffsetSpinBox.setMaximum(1000.0)
        self.LOffsetSpinBox.setSingleStep(0.5)
        self.LOffsetSpinBox.setObjectName("LOffsetSpinBox")
        self.LOffsetLabel = QtWidgets.QLabel(self.centralwidget)
        self.LOffsetLabel.setGeometry(QtCore.QRect(660, 402, 50, 35))
        self.LOffsetLabel.setObjectName("LOffsetLabel")
        self.ROffsetLabel = QtWidgets.QLabel(self.centralwidget)
        self.ROffsetLabel.setGeometry(QtCore.QRect(660, 442, 50, 35))
        self.ROffsetLabel.setObjectName("ROffsetLabel")
        self.ROffsetSpinBox = QtWidgets.QDoubleSpinBox(self.centralwidget)
        self.ROffsetSpinBox.setGeometry(QtCore.QRect(710, 442, 60, 35))
        self.ROffsetSpinBox.setMinimum(-1000.0)
        self.ROffsetSpinBox.setMaximum(1000.0)
        self.ROffsetSpinBox.setSingleStep(0.5)
        self.ROffsetSpinBox.setObjectName("ROffsetSpinBox")
        self.seconds_1 = QtWidgets.QLabel(self.centralwidget)
        self.seconds_1.setGeometry(QtCore.QRect(778, 402, 22, 35))
        self.seconds_1.setObjectName("seconds_1")
        self.PerviewButton = QtWidgets.QPushButton(self.centralwidget)
        self.PerviewButton.setEnabled(True)
        self.PerviewButton.setGeometry(QtCore.QRect(660, 482, 131, 50))
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.PerviewButton.sizePolicy().hasHeightForWidth())
        self.PerviewButton.setSizePolicy(sizePolicy)
        self.PerviewButton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.PerviewButton.setObjectName("PerviewButton")
        self.seconds_2 = QtWidgets.QLabel(self.centralwidget)
        self.seconds_2.setGeometry(QtCore.QRect(778, 442, 22, 35))
        self.seconds_2.setObjectName("seconds_2")
        self.ExportButton = QtWidgets.QPushButton(self.centralwidget)
        self.ExportButton.setEnabled(True)
        self.ExportButton.setGeometry(QtCore.QRect(660, 534, 131, 50))
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.ExportButton.sizePolicy().hasHeightForWidth())
        self.ExportButton.setSizePolicy(sizePolicy)
        self.ExportButton.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.ExportButton.setObjectName("ExportButton")
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QtCore.QRect(10, 180, 640, 403))
        self.tableWidget.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.tableWidget.setLineWidth(1)
        self.tableWidget.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tableWidget.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableWidget.setGridStyle(QtCore.Qt.PenStyle.NoPen)
        self.tableWidget.setWordWrap(True)
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.setObjectName("tableWidget")
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(2, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setHorizontalHeaderItem(3, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setItem(0, 0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setItem(0, 1, item)
        item = QtWidgets.QTableWidgetItem()
        self.tableWidget.setItem(0, 2, item)
        item = QtWidgets.QTableWidgetItem()
        item.setFlags(QtCore.Qt.ItemFlag.ItemIsSelectable
                      | QtCore.Qt.ItemFlag.ItemIsEnabled)
        self.tableWidget.setItem(0, 3, item)
        self.tableWidget.horizontalHeader().setVisible(True)
        self.tableWidget.horizontalHeader().setCascadingSectionResizes(True)
        self.tableWidget.horizontalHeader().setDefaultSectionSize(60)
        self.tableWidget.horizontalHeader().setHighlightSections(True)
        self.tableWidget.horizontalHeader().setMinimumSectionSize(20)
        self.tableWidget.horizontalHeader().setSortIndicatorShown(False)
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setDefaultSectionSize(21)
        self.tableWidget.verticalHeader().setSortIndicatorShown(False)
        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(
            _translate("MainWindow", "Dialogue Extractor v1.0"))
        self.menu_About.setTitle(_translate("MainWindow", "&关于"))
        self.actionAuthor_color_sky.setText(
            _translate("MainWindow", "&关于作者 (color·sky)"))
        self.actionAuthor_color_sky.triggered.connect(lambda: self.openAbout())

        self.InputDirButton.setText(_translate("MainWindow", "导入路径"))
        self.InputDirButton.clicked.connect(
            lambda: self.getInputFolder(MainWindow))
        self.OutputDirButton.setText(_translate("MainWindow", "导出路径"))
        self.OutputDirButton.clicked.connect(
            lambda: self.getOutputFolder(MainWindow))

        self.EpisodeLabel.setText(_translate("MainWindow", "集数"))
        self.EpisodeSelection.setItemText(0, _translate("MainWindow", "全部"))
        self.EpisodeSelection.currentIndexChanged.connect(
            lambda: self.updateDialogue())
        self.SearchLabel.setText(_translate("MainWindow", "搜索"))

        self.ScriptGenerateButton.setText(_translate("MainWindow", "剧本生成"))
        self.ScriptConfig.setText(_translate(
            "MainWindow", "      S            T             R"))
        self.DenoiseCheckBox.setText(
            _translate("MainWindow", "   人声提取"))

        if not ENABLE_BETA:
            self.ScriptGenerateButton.setEnabled(False)
            self.SourceAmount.setEnabled(False)
            self.TargetAmount.setEnabled(False)
            self.RandomSeed.setEnabled(False)
            self.DenoiseCheckBox.setEnabled(False)
        else:
            self.ScriptGenerateButton.clicked.connect(lambda: self.generateScript())

        self.SearchText.returnPressed.connect(lambda: self.updateSearch())
        self.ConcatenateCheckBox.setText(
            _translate("MainWindow", "   合并多选"))
        self.ConcatenateCheckBox.setChecked(True)
        self.PreviewCheckBox.setText(
            _translate("MainWindow", "   视频预览"))
        self.PreviewCheckBox.setChecked(True)
        self.LOffsetLabel.setText(_translate("MainWindow", "左偏移"))
        self.ROffsetLabel.setText(_translate("MainWindow", "右偏移"))

        self.seconds_1.setText(_translate("MainWindow", "秒"))
        self.PerviewButton.setText(_translate("MainWindow", "预览"))
        self.PerviewButton.clicked.connect(lambda: self.previewSelected())

        self.seconds_2.setText(_translate("MainWindow", "秒"))
        self.ExportButton.setText(_translate("MainWindow", "提取"))
        self.ExportButton.clicked.connect(lambda: self.exportSelected())

        item = self.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "集数"))
        item = self.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "开始"))
        item = self.tableWidget.horizontalHeaderItem(2)
        item.setText(_translate("MainWindow", "结束"))
        item = self.tableWidget.horizontalHeaderItem(3)
        item.setText(_translate("MainWindow", "字幕"))
        __sortingEnabled = self.tableWidget.isSortingEnabled()
        self.tableWidget.setSortingEnabled(False)
        self.tableWidget.setSortingEnabled(__sortingEnabled)
        # self.tableWidget.doubleClicked.connect(lambda: self.previewSelected())


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    if ENABLE_BETA:
        from spleeter.separator import Separator
        from Bert_ext import extractive_summarize
        separator = Separator('spleeter:4stems')
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
