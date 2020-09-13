import asyncio
import os
from graia.application import GraiaMiraiApplication, Session, Friend
from graia.application.message.chain import MessageChain
from graia.application.group import Group, Member, MemberPerm
from graia.application.message.elements.internal import Plain, Image, At
from graia.broadcast import Broadcast
import config
from function import *
from logging import handlers
import logging

#  日志部分
loghandler = handlers.TimedRotatingFileHandler(os.path.join('log', 'mocaBot.log'), when='midnight', encoding='utf-8')
loghandler.setLevel(logging.DEBUG)
loghandler.setFormatter(logging.Formatter('%(asctime)s - [%(levelname)s]: %(message)s'))
logger = logging.getLogger('botlogger')
logger.addHandler(loghandler)
logger.setLevel(logging.DEBUG)
logger.info("日志初始化成功")
#  日志部分


loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=f"http://{config.server_ip}:{config.server_port}",  # 填入 httpapi 服务运行的地址
        authKey=config.auth_key,  # 填入 authKey
        account=config.bot_id,  # 你的机器人的 qq 号
        websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    )

)


@bcc.receiver("GroupMessage")
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    text = message.asDisplay()
    group_id = group.id

    if message.has(At):
        at_data = message.get(At)[0].dict()
        at_target = at_data['target']
        at_target_name = at_data['display'].lstrip("@")

        if at_target == app.connect_info.account:   # At毛力的操作开始
            logger.debug(f"[{group_id}] At了毛力")
            if member.permission == MemberPerm.Administrator or \
                    member.permission == MemberPerm.Owner or \
                    member.id == config.superman:
                logger.debug(f"[{group_id}] 管理员At了毛力")
                #   管理员At操作开始

                #   管理员At操作结束

            #   非必须管理员At操作开始
            if "统计次数" in text or "次数统计" in text:
                if not is_in_cd(group_id, "replyHelpCD"):
                    logger.info(f"[{group_id}] 请求统计次数")
                    await update_cd(group_id, "replyHelpCD")
                    create_dict_pic(json.loads(r.hget("COUNT", group_id)), f'{group_id}_count', '次数')
                    await app.sendGroupMessage(group, MessageChain.create([
                        Image.fromLocalFile(os.path.join(config.temp_path, f'{group_id}_count.png'))
                    ]))
                else:
                    logger.debug(f"[{group_id}] 帮助类cd冷却中")
                return

            if "关键词" in text:
                if not is_in_cd(group_id, "replyHelpCD"):
                    logger.info(f"[{group_id}] 请求关键词列表")
                    await update_cd(group_id, "replyHelpCD")
                    create_dict_pic(json.loads(r.hget("KEYWORDS", group_id)), f'{group_id}_key', '关键词')
                    await app.sendGroupMessage(group, MessageChain.create([
                        Image.fromLocalFile(os.path.join(config.temp_path, f'{group_id}_key.png'))
                    ]))
                else:
                    logger.debug(f"[{group_id}] 帮助类cd冷却中")
                return

            if "图片数量" in text:
                if not is_in_cd(group_id, "replyHelpCD"):
                    logger.info(f"[{group_id}] 请求统计图片数量")
                    await update_cd(group_id, "replyHelpCD")
                    create_dict_pic(fetch_picture_count_list(group_id), f'{group_id}_piccount', '图片数量')
                    await app.sendGroupMessage(group, MessageChain.create([
                        Image.fromLocalFile(os.path.join(config.temp_path, f'{group_id}_piccount.png'))
                    ]))
                else:
                    logger.debug(f"[{group_id}] 统计次数cd冷却中")
                return

            if "爬" in text or "爪巴" in text:
                if not is_in_cd(group_id, "keaiPaCD"):
                    if random_do(fetch_config(group_id, "keaiPaChance")):
                        await update_cd(group_id, "keaiPaCD")
                        logger.info(f"[{group_id}] moca爬了")
                        random_file = random.choice(os.listdir(os.path.join(config.resource_path, "pa")))
                        await app.sendGroupMessage(group, MessageChain.create([
                            Image.fromLocalFile(os.path.join(config.resource_path, 'pa', random_file))
                        ]))
                    else:
                        logger.debug(f"[{group_id}] moca爬，但是没有命中概率")
                else:
                    logger.debug(f"[{group_id}] moca爬，但是cd冷却中")
                await update_count(group_id, '爬')
                return

            if "可爱" in text or "老婆" in text or "lp" in text or "mua" in text:
                if not is_in_cd(group_id, "keaiPaCD"):
                    if random_do(fetch_config(group_id, "keaiPaChance")):
                        await update_cd(group_id, "keaiPaCD")
                        logger.info(f"[{group_id}] moca可爱")
                        random_file = random.choice(os.listdir(os.path.join(config.resource_path, "keai")))
                        await app.sendGroupMessage(group, MessageChain.create([
                            Image.fromLocalFile(os.path.join(config.resource_path, 'keai', random_file))
                        ]))
                    else:
                        logger.debug(f"[{group_id}] moca可爱，但是没有命中概率")
                else:
                    logger.debug(f"[{group_id}] moca可爱，但是cd冷却中")
                await update_count(group_id, '可爱')
                return
            #   非必须管理员At操作结束
        else:
            #   At了他人的操作开始
            logger.debug(f"[{group_id}] At {at_target_name} {at_target}")
            if '换lp次数' in text.replace('老婆', 'lp'):
                count = fetch_clp_times(at_target)
                if count > 0:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"{at_target_name} 换了{count}次lp了哦~")
                    ]))
                else:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"{at_target_name} 还没有换过lp呢~")
                    ]))
                return
            #   At了他人的操作结束

    else:
        #   普通操作开始
        pass
        #   普通操作结束

app.launch_blocking()
