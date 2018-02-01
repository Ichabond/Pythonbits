#!/usr/bin/env python2
# encoding: utf-8
"""
Screenshots.py

Created by Ichabond on 2012-07-03.
Copyright (c) 2012 Baconseed. All rights reserved.
"""

from Ffmpeg import FFMpeg
from ImgurUploader import ImgurUploader


def createScreenshots(file, shots=2):
    ffmpeg = FFMpeg(file)
    images = ffmpeg.takeScreenshots(shots)
    urls = ImgurUploader(images).upload()

    return urls
