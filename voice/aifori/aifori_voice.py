#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2024/08/27 18:02:13
@Author  :   ChenHao
@Description  : Aifori服务的语音处理
@Contact :   jerrychen1990@gmail.com
'''

import os
import re
import time


from aifori.client import AiForiClient
from aifori.core import SpeakRequest
import liteai
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.tmp_dir import TmpDir
import liteai.voice
from voice.voice import Voice
from config import conf
import pysilk
from pydub import AudioSegment
from liteai.voice import file2voice
from liteai.api import asr


def mp3_to_silk(mp3_path, silk_path):
    # 将 MP3 转换为 WAV
    logger.debug(f"converting mp3_path={mp3_path}, silk_path={silk_path}")
    audio = AudioSegment.from_mp3(mp3_path)
    wav_path = "temp.wav"
    audio.export(wav_path, format="wav")

    # 打开 WAV 文件并进行转换
    with open(wav_path, 'rb') as wav_file:
        wav_data = wav_file.read()
        silk_data = pysilk.encode(wav_data)

    # 保存 SILK 文件
    with open(silk_path, 'wb') as silk_file:
        silk_file.write(silk_data)

    # 删除临时 WAV 文件
    os.remove(wav_path)


class AiforiVoice(Voice):
    def __init__(self):
        """
        初始化AliVoice类，从配置文件加载必要的配置。
        """
        self.aifori_url = conf().get("aifori_url")
        self.client = AiForiClient(host=self.aifori_url)

    def textToVoice(self, text):
        """
        将文本转换为语音文件。

        :param text: 要转换的文本。
        :return: 返回一个Reply对象，其中包含转换得到的语音文件或错误信息。
        """
        # 清除文本中的非中文、非英文和非基本字符
        logger.info(f"Aifori doing tts:{text}")
        text = re.sub(r'[^\u4e00-\u9fa5\u3040-\u30FF\uAC00-\uD7AFa-zA-Z0-9'
                      r'äöüÄÖÜáéíóúÁÉÍÓÚàèìòùÀÈÌÒÙâêîôûÂÊÎÔÛçÇñÑ，。！？,.]', '', text)

        speak_req = SpeakRequest(assistant_id=conf()["aifori_assistant_id"], message=text)
        local_voice_path = TmpDir().path() + "reply-" + str(int(time.time())) + "-" + str(hash(text) & 0x7FFFFFFF) + ".mp3"

        voice = self.client.speak(speak_req=speak_req, local_voice_path=local_voice_path)
        liteai.voice.dump_voice_stream(voice.byte_stream, local_voice_path)
        silk_path = local_voice_path.replace(".mp3", ".silk")
        mp3_to_silk(local_voice_path, silk_path)

        # 提取有效的token
        if local_voice_path:
            logger.info("[Aifori] textToVoice text={} voice file name={}".format(text, local_voice_path))
            reply = Reply(ReplyType.VOICE, silk_path)
        else:
            reply = Reply(ReplyType.ERROR, "抱歉，语音合成失败")
        return reply

    def voiceToText(self, voice_file):
        """
        将语音文件转换为文本。

        :param voice_file: 要转换的语音文件。
        :return: 返回一个Reply对象，其中包含转换得到的文本或错误信息。
        """
        logger.info(f"Aifori doing asr:{voice_file}")

        voice = file2voice(voice_file)
        xunfei_app_id = conf().get("xunfei_app_id")
        text = asr(voice=voice, model="xunfei_asr", app_id=xunfei_app_id)
        return Reply(ReplyType.TEXT, text)

