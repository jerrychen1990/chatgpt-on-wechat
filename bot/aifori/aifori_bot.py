#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@Time    :   2024/08/23 17:10:33
@Author  :   ChenHao
@Description  :
@Contact :   jerrychen1990@gmail.com
'''

from aifori.core import ChatRequest
from bot.bot import Bot
from bridge.context import Context, ContextType
from bridge.reply import Reply, ReplyType
from channel.wechat.wechat_message import WechatMessage
from common.log import logger
from aifori.client import AiForiClient
from config import conf, load_config


# ZhipuAI对话模型API
class AiforiBot(Bot):

    def __init__(self):
        super().__init__()
        self.client = AiForiClient(host="https://aifori.fun/api")

    def reply(self, query, context=None):
        # acquire reply content
        if context.type == ContextType.TEXT:
            logger.info(f"context={str(context)}")
            logger.info("[Aifori] query={}".format(query))
            msg: WechatMessage = context.kwargs["msg"]
            logger.info(f"msg = {str(msg)}")

            session_id = context["session_id"]
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query in clear_memory_commands:
                self.client.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.client.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                reply = Reply(ReplyType.INFO, "配置已更新")
            if reply:
                return reply
            user_id = msg.other_user_id
            self.client.get_or_create_user(user_id=user_id, name=msg.other_user_nickname, desc=msg.other_user_nickname)
            req = ChatRequest(assistant_id="Aifori", user_id=user_id, session_id=session_id, message=query, do_remember=True)

            reply_content = self.client.chat(req, stream=False).content

            reply = Reply(ReplyType.TEXT, reply_content)
            return reply
        elif context.type == ContextType.IMAGE_CREATE:
            ok, retstring = self.create_img(query, 0)
            reply = None
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))


if __name__ == "__main__":

    from aifori.client import AiForiClient
    bot = AiforiBot()
    resp = bot.reply(query="你好", context=Context(type=ContextType.TEXT, content="你好", kwargs={"session_id": "test"}))
    print(resp)
