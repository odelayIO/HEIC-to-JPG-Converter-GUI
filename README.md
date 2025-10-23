# HEIC to JPG Converter Application

This is a Python Qt5 application which converts iPhone HEIC to JPG images.  

Provide the binary download for Windows and Linux in [Releases](https://github.com/odelayIO/HEIC-to-JPG-Converter-GUI/releases).

Also provided a helper Python script to rename the JPG images to date/time from the meta information in the JPG image.

![heic2jpg](./heic2jpg.png)

## Quick Start

Create Python Virtual Environment and start `heic2jpg_gui.py` application:

```bash
python3 -m venv venv
source ./venv/bin/activate
pip install --upgrade pip setuptools wheel
pip3 install -r requirements.txt
python3 heic2jpg_gui.py
```



## Detailed Instructions

To use the application, create a Python Virtual Environment:

```bash
python -m venv venv
```

Then start the Python Virtual Environment:

```bash
source ./venv/bin/activate
```

To exit the Python Virtual Environment:

```bash
deactivate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## Creating Standalone Executable 

```bash
pip install pyinstaller
pyinstaller --onefile --windowed heic2jpg_gui.py
```
