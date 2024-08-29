# encoding:utf-8

import os
import signal
import sys
import time

from dotenv import load_dotenv

from channel import channel_factory
from common import const
from config import load_config
from plugins import *
import threading

from snippets.logs import set_logger


def sigterm_handler_wrap(_signal):
    old_handler = signal.getsignal(_signal)

    def func(_sig, _stack_frame):
        logger.info("signal {} received, exiting...".format(_sig))
        conf().save_user_data()
        if callable(old_handler):  #  check old_handler
            return old_handler(_sig, _stack_frame)
        sys.exit(0)

    signal.signal(_signal, func)


def start_channel(channel_name: str):
    logger.info(f"starting channel {channel_name}")
    channel = channel_factory.create_channel(channel_name)
    if channel_name in ["wx", "wxy", "terminal", "wechatmp", "wechatmp_service", "wechatcom_app", "wework",
                        const.FEISHU, const.DINGTALK]:
        PluginManager().load_plugins()

    if conf().get("use_linkai"):
        try:
            from common import linkai_client
            threading.Thread(target=linkai_client.start, args=(channel,)).start()
        except Exception as e:
            pass
    channel.startup()


def load_aifori():
    load_dotenv()
    path = sys.path
    aifori_path = os.environ["AIFORI_CODE_HOME"]
    if aifori_path not in path:
        sys.path.insert(0, aifori_path)
        logger.info(f"{sys.path=}")


def run():
    try:
        # load config
        print("start")
        logger.info("start")
        config_path = sys.argv[1]
        load_aifori()
        load_config(config_path)
        # ctrl + c
        sigterm_handler_wrap(signal.SIGINT)
        # kill signal
        sigterm_handler_wrap(signal.SIGTERM)

        # create channel
        channel_name = conf().get("channel_type", "wx")

        if "--cmd" in sys.argv:
            channel_name = "terminal"

        if channel_name == "wxy":
            os.environ["WECHATY_LOG"] = "info"

        start_channel(channel_name)

        while True:
            time.sleep(1)
    except Exception as e:
        logger.error("App startup failed!")
        logger.exception(e)


if __name__ == "__main__":
    set_logger("dev", __name__)
    run()
