import asyncio
import hashlib
import traceback

from graia.application import GraiaMiraiApplication, Session
from graia.application.event.mirai import BotInvitedJoinGroupRequestEvent, BotJoinGroupEvent, MemberLeaveEventKick
from graia.application.group import Group, Member, MemberPerm
from graia.application.message.elements.internal import Plain, Image, At, ImageType, Voice
from graia.broadcast import Broadcast
from graia.application.entry import GroupMessage, MemberJoinEvent
from function import *
from logging import handlers
import logging
import urllib
from functions.signin_pan import signin, consume_pan, buy_pan, BUY_PAN_INTERVAL, get_pan_amount, PAN_TWICE_LP_CONSUME, \
    eat_pan, EAT_PAN_AMOUNT, rob_pan, ROB_CD

#  日志部分
loghandler = handlers.TimedRotatingFileHandler(os.path.join('log', 'mocaBot.log'), when='midnight', encoding='utf-8')
loghandler.setLevel(logging.INFO)
loghandler.setFormatter(logging.Formatter('%(asctime)s - [%(levelname)s]: %(message)s'))
logger = logging.getLogger('botlogger')
logger.addHandler(loghandler)
logger.setLevel(logging.INFO)
logger.info("日志初始化成功")
#  日志部分

string = '/\:*<>|"'
runtime_var = {'file_list_update_time': -1}
dictionary = {
    "band": {
        "ro": "Roselia",
        "ppp": "Poppin'Party",
        "pp": "Pastel*Palettes",
        "ag": "Afterglow",
        "hhw": "Hello, Happy World",
        "ras": "RAISE A SUILEN",
        "mo": "Morfonica",
        "rimi": "牛込りみ",
        "saaya": "山吹沙綾",
        "arisa": "市ヶ谷有咲",
        "otae": "花園たえ",
        "ayaxmocaxlisaxkanonxtsugu": "彩×モカ×リサ×花音×つぐみ",
        "pppxykn": "Poppin'Party×友希那",
        "ksmxranxayaxyknxkkr": "香澄×蘭×彩×友希那×こころ",
        "hhwxranxaya": "ハロハピ×蘭×彩",
        "roxran": "Roselia×蘭",
        "agxkkr": "Afterglow×こころ",
        "pppxgg": "Poppin‘Party × Glitter*Green",
        "ksmxag": "香澄×Afterglow",
        "pppxayaxkkr": "Poppin'Party×彩×こころ"
    },
    "level": {
        "ex": "EXPERT",
        "sp": "SPECIAL",
        "full": "FULL"
    },
    "type": {
        "og": "原创",
        "co": "翻唱"
    }
}
twice_lp_pan_amount = 2

if os.path.isfile('debug'):
    debug_mode = True
else:
    debug_mode = False


loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=f"http://{config.server_ip}:{config.server_port}",  # 填入 httpapi 服务运行的地址
        authKey=config.auth_key,  # 填入 authKey
        account=config.bot_id,  # 你的机器人的 qq 号
        websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    ),
    enable_chat_log=False
)


# noinspection PyBroadException
@bcc.receiver(GroupMessage)
async def group_message_handler(message: MessageChain, group: Group, member: Member):
    text = message.asDisplay().replace(" ", "").lower()
    group_id = group.id

    if debug_mode:
        if not group_id == 907274961:
            return

    #   Temporary
    if not rc.sismember("GROUPS", str(group_id)):
        rc.sadd('GROUPS', str(group_id))

    #   初始化群组参数数据
    if not r.hexists("KEYWORDS", str(group_id)):
        r.hset("KEYWORDS", str(group_id), r.hget("KEYWORDS", "key_template"))
        r.hset("CONFIG", str(group_id), r.hget("CONFIG", "config_template"))

    if message.has(At):
        at_data = message.get(At)[0].dict()
        at_target = at_data['target']
        at_target_name = at_data['display'].lstrip("@")

        if at_target == app.connect_info.account:  # At毛力的操作开始
            logger.debug(f"[{group_id}] At了毛力")
            if member.permission == MemberPerm.Administrator or \
                    member.permission == MemberPerm.Owner or \
                    is_superman(member.id):
                logger.debug(f"[{group_id}] 管理员At了毛力")

                #   管理员At操作开始
                #   管理员At操作结束

            #   非必须管理员At操作开始

            #   查看统计次数
            #   权限：成员
            #   是否At机器人：是
            if "统计次数" in text or "次数统计" in text:
                if not is_in_cd(runtime_var, group_id, "replyHelpCD"):
                    logger.info(f"[{group_id}] 请求统计次数")
                    update_cd(runtime_var, group_id, "replyHelpCD")
                    sorted_keyword_list = sort_dict(json.loads(r.hget("COUNT", group_id)))
                    create_dict_pic(sorted_keyword_list, f'{group_id}_count', '次数', sort_by_value=True)
                    await app.sendGroupMessage(group, MessageChain.create([
                        Image.fromLocalFile(os.path.join(config.temp_path, f'{group_id}_count.png'))
                    ]))
                else:
                    logger.debug(f"[{group_id}] 帮助类cd冷却中")
                return

            #   查看关键词列表
            #   权限：成员
            #   是否At机器人：是
            if "关键词" in text:
                if not is_in_cd(runtime_var, group_id, "replyHelpCD"):
                    logger.info(f"[{group_id}] 请求关键词列表")
                    update_cd(runtime_var, group_id, "replyHelpCD")
                    sorted_keyword_list = sort_dict(json.loads(r.hget("KEYWORDS", group_id)))
                    create_dict_pic(sorted_keyword_list, f'{group_id}_key', '关键词')
                    await app.sendGroupMessage(group, MessageChain.create([
                        Image.fromLocalFile(os.path.join(config.temp_path, f'{group_id}_key.png'))
                    ]))
                else:
                    logger.debug(f"[{group_id}] 帮助类cd冷却中")
                return

            #   查看图片数量
            #   权限：成员
            #   是否At机器人：是
            if "图片数量" in text:
                if not is_in_cd(runtime_var, group_id, "replyHelpCD"):
                    logger.info(f"[{group_id}] 请求统计图片数量")
                    update_cd(runtime_var, group_id, "replyHelpCD")
                    count_list = sort_dict(fetch_picture_count_list(group_id))
                    create_dict_pic(count_list, f'{group_id}_piccount', '图片数量', sort_by_value=True)
                    await app.sendGroupMessage(group, MessageChain.create([
                        Image.fromLocalFile(os.path.join(config.temp_path, f'{group_id}_piccount.png'))
                    ]))
                else:
                    logger.debug(f"[{group_id}] 帮助类cd冷却中")
                return

            #   查看lp排行(置于lp关键词前，防止先触发lp关键词)
            #   权限：成员
            #   是否At机器人：是
            if "lp排行" in text:
                if not is_in_cd(runtime_var, group_id, "replyHelpCD"):
                    logger.info(f"[{group_id}] 请求lp排行榜")
                    update_cd(runtime_var, group_id, "replyHelpCD")
                    result = lp_list_rank()
                    create_dict_pic(result, f'{group_id}_rank', '前十人数')
                    await app.sendGroupMessage(group, MessageChain.create([
                        Image.fromLocalFile(os.path.join(config.temp_path, f'{group_id}_rank.png'))
                    ]))
                else:
                    logger.debug(f"[{group_id}] 帮助类cd冷却中")
                return

            #   毛力爬
            #   权限：成员；
            #   是否At机器人：是
            if "爬" in text or "爪巴" in text:
                if not is_in_cd(runtime_var, group_id, "keaiPaCD"):
                    if random_do(fetch_config(group_id, "keaiPaChance")):
                        update_cd(runtime_var, group_id, "keaiPaCD")
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

            #   毛力可爱
            #   权限：成员
            #   是否At机器人：是
            if "可爱" in text or "老婆" in text or "lp" in text or "mua" in text:
                if not is_in_cd(runtime_var, group_id, "keaiPaCD"):
                    if random_do(fetch_config(group_id, "keaiPaChance")):
                        update_cd(runtime_var, group_id, "keaiPaCD")
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

            #   签到
            #   权限：成员
            #   是否At机器人：是
            if "签到" in text and exp_enabled(group_id):
                await signin(member.id, r, app, group)
                return

            #   提交图片
            #   权限：成员
            #   是否At机器人：是
            if '提交图片' in text:
                error_flag = False
                error_info = ""
                if len(text) > 4:
                    logger.info(f"[{group_id}] 提交图片")
                    data_list = []
                    if not message.has(Image):
                        await app.sendGroupMessage(group, MessageChain.create([
                            Plain("错误：你至少需要包含一张图片")
                        ]))
                        return
                    category = text[text.index("提交图片"):].lstrip("提交图片").replace("[图片]", "")
                    if category == "":
                        await app.sendGroupMessage(group, MessageChain.create([
                            Plain("错误：请附带分类，例如：@毛力 提交图片 群友b话，再加上图片")
                        ]))
                        return
                    for n in category:
                        if n in string:
                            await app.sendGroupMessage(group, MessageChain.create([
                                Plain("错误：名称中含有非法字符，请检查")
                            ]))
                            return
                    message_data = message.dict()['__root__']
                    for index in range(len(message_data)):
                        if message_data[index].get('type') == ImageType.Group:
                            data_list.append({
                                "url": message_data[index].get("url"),
                                "file_name": message_data[index].get("imageId").split(".")[0]
                                .replace("{", "")
                                .replace("}", "")
                            })

                    # upload/{群号}/月/日/{imageId}
                    month = time.strftime("%m")
                    day = time.strftime("%d")
                    save_path = os.path.join(config.temp_path, "upload", str(group_id), month, day, category)
                    if not os.path.exists(save_path):
                        os.makedirs(save_path)
                    for file_index in range(len(data_list)):
                        try:
                            await save_image(data_list[file_index]["url"],
                                             data_list[file_index]["file_name"], save_path)
                        except Exception as e:
                            logger.error(str(traceback.format_exc()))
                            error_flag = True
                            error_info = repr(e)
                    if error_flag:
                        await app.sendGroupMessage(group, MessageChain.create([
                            Plain(f'错误：提交失败，错误：{error_info}')
                        ]))
                    else:
                        file_count = len(data_list)
                        await app.sendGroupMessage(group, MessageChain.create([
                            Plain(f'提交成功，收到{file_count}张图片')
                        ]))
                else:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f'错误：参数错误')
                    ]))
                return

            #   语音 (EXPERIMENTAL)
            #   权限：成员
            #   是否At机器人：是
            if "说话" in text or "语音" in text:
                if is_in_user_cd(runtime_var, member.id, "voice"):
                    return
                voice_file = random.choice(os.listdir(os.path.join('resource', 'voice')))
                with open(os.path.join('resource', 'voice', voice_file), 'rb')as voice_bin_file:
                    voice = await app.uploadVoice(voice_bin_file)
                await app.sendGroupMessage(group, MessageChain.create([
                  voice
                ]))
                update_user_cd(runtime_var, member.id, "voice", 30)
                return

            #   非必须管理员At操作结束
        else:
            #   At了他人的操作开始

            logger.debug(f"[{group_id}] @{at_target_name} {at_target}")

            #   抢面包 (DISABLED)
            #   权限：成员
            #   是否At机器人：否
            #   需At任意群员
            if '抢面包fghjsdrgsdjyu6' in text:
                if member.id == at_target:
                    await app.sendGroupMessage(group, MessageChain.create([
                        At(target=member.id),
                        Plain(f" 不能抢自己的面包哦！~")
                    ]))
                    return
                if is_in_user_cd(runtime_var, member.id, "rob"):
                    return

                status = rob_pan(member.id, at_target, r)
                if status[0]:
                    await app.sendGroupMessage(group, MessageChain.create([
                        At(target=member.id),
                        Plain(f" 抢面包成功了！你获得了{status[1]}个面包~\n你现在有{status[2]}个面包，ta现在有{status[3]}个面包呢~")
                    ]))
                    return
                else:
                    if status[1] == -99:
                        await app.sendGroupMessage(group, MessageChain.create([
                            At(target=member.id),
                            Plain(f" 抢面包失败了...ta没有面包了QAQ")
                        ]))
                        return
                    if status[1] == 0:
                        await app.sendGroupMessage(group, MessageChain.create([
                            At(target=member.id),
                            Plain(f" 抢面包失败了...但你也没有面包了呢www")
                        ]))
                        return
                    await app.sendGroupMessage(group, MessageChain.create([
                        At(target=member.id),
                        Plain(f" 抢面包失败了...你失去了{status[1]}个面包...\n你现在还有{status[2]}个面包，ta现在有{status[3]}个面包www")
                    ]))
                update_user_cd(runtime_var, member.id, "rob", ROB_CD)
                return

            #   查看他人换lp次数
            #   权限：成员
            #   是否At机器人：否
            #   需At任意群员
            if '换lp次数' in text.replace('老婆', 'lp'):
                count = fetch_clp_times(at_target)
                if count > 0:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"{at_target_name}换了{count}次lp了哦~")
                    ]))
                else:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"{at_target_name}还没有换过lp呢~")
                    ]))
                return

            #   口他
            #   权限：管理员/群主/superman
            #   是否At机器人：否
            #   需At任意群员且机器人为管理员
            plain_text = message.get(Plain)
            if len(plain_text) > 0:
                p_text = plain_text[0].dict()['text'] \
                    .replace(" ", "") \
                    .replace("他", "ta") \
                    .replace("她", "ta") \
                    .replace("它", "ta")
                if "禁言" in p_text or "口ta" in p_text:
                    if (group.accountPerm == MemberPerm.Administrator or group.accountPerm == MemberPerm.Owner) and \
                            (member.permission == MemberPerm.Administrator or member.permission == MemberPerm.Owner
                             or is_superman(member.id)):
                        #   需同时机器人是管理员且操作者为管理员
                        target: Member = await app.getMember(group_id, at_target)
                        if target.permission == MemberPerm.Member:
                            if p_text.endswith("秒"):
                                time_type = "s"
                            elif p_text.endswith("分钟"):
                                time_type = "min"
                            elif p_text.endswith("小时"):
                                time_type = "h"
                            elif p_text.endswith("天"):
                                time_type = "d"
                            else:
                                time_type = "unknown"

                            if "禁言" in p_text:
                                s_index = p_text.index("禁言") + 2
                            elif "口ta" in p_text:
                                s_index = p_text.index("口ta") + 3
                            else:
                                return
                            try:
                                if time_type == "s":
                                    mute_time = int(p_text[s_index:-1])
                                elif time_type == "min":
                                    mute_time = int(p_text[s_index:-2]) * 60
                                elif time_type == "h":
                                    mute_time = int(p_text[s_index:-2]) * 3600
                                elif time_type == "d":
                                    mute_time = int(p_text[s_index:-1]) * 86400
                                else:
                                    mute_time = -1
                                await app.mute(group, at_target, mute_time)
                            except ValueError:
                                await app.sendGroupMessage(group, MessageChain.create([
                                    Plain(f"错误：时间参数错误，仅支持数字+秒/分钟/小时/天")
                                ]))
                            except PermissionError:
                                await app.sendGroupMessage(group, MessageChain.create([
                                    Plain(f"权限错误")
                                ]))  # 大概不会raise
                    return

            #   解禁某人
            #   权限：管理员/群主/superman
            #   是否At机器人：否
            #   需At任意群员且机器人为管理员
            if "解禁" in text:
                if (group.accountPerm == MemberPerm.Administrator or group.accountPerm == MemberPerm.Owner) and \
                        (member.permission == MemberPerm.Administrator or
                         member.permission == MemberPerm.Owner or
                         is_superman(member.id)):
                    await app.unmute(group, at_target)
                return
            #   At了他人的操作结束

    #   普通操作开始
    if member.permission == MemberPerm.Administrator or \
            member.permission == MemberPerm.Owner or \
            is_superman(member.id):
        #   管理员普通操作开始

        #   打开实验功能
        #   权限：管理员/群主
        #   是否At机器人：否
        if text == '打开实验功能':
            exp_status = fetch_config(group_id, "exp")
            if not bool(exp_status):
                update_config(group_id, "exp", 1)
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f"{group_id} 已启用实验功能")
                ]))
            else:
                if exp_status == 0:
                    update_config(group_id, "exp", 1)
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"{group_id} 已启用实验功能")
                    ]))
                else:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"{group_id} 已启用过实验功能，请勿重复启用")
                    ]))
            return

        #   关闭实验功能
        #   权限：管理员/群主
        #   是否At机器人：否
        if text == '关闭实验功能':
            exp_status = fetch_config(group_id, "exp")
            if not bool(exp_status):
                update_config(group_id, "exp", 0)
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f"{group_id} 未启用实验功能")
                ]))
            else:
                if exp_status == 1:
                    update_config(group_id, "exp", 0)
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"{group_id} 已关闭实验功能")
                    ]))
                else:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"{group_id} 未启用实验功能")
                    ]))
            return

        #   设置图片cd
        #   权限：管理员/群主/superman
        #   是否At机器人：否
        if text.startswith("设置图片cd"):
            to_set_cd = -1
            arg_error = False
            try:
                to_set_cd = int(text.lstrip("设置图片cd").rstrip("秒"))  # 获取参数
            except ValueError:
                logger.warning(f"[{group_id}] 设置图片cd 参数错误")
                arg_error = True
            if not arg_error:
                if to_set_cd < 5:  # 最低5秒
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"不要无限火力不要无限火力，最低5秒cd")
                    ]))
                else:
                    new_value = update_config(group_id, "replyCD", to_set_cd)
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"当前图片cd：{new_value}秒")
                    ]))
                    logger.info(f"[{group_id}] 设置图片cd {to_set_cd}秒")
            else:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("参数有误，请检查格式\n示例：设置图片cd10秒")
                ]))
            return

        #   设置复读cd
        #   权限：管理员/群主/superman
        #   是否At机器人：否
        if text.startswith("设置复读cd"):
            to_set_cd = -1
            arg_error = False
            try:
                to_set_cd = int(text.lstrip("设置复读cd").rstrip("秒"))  # 获取参数
            except ValueError:
                logger.warning(f"[{group_id}] 设置复读cd 参数错误")
                arg_error = True
            if not arg_error:
                if to_set_cd < 120:  # 最低120秒
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain("错误：最低120秒cd")
                    ]))
                else:
                    new_value = update_config(group_id, "repeatCD", to_set_cd)
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"当前复读cd：{new_value}秒")
                    ]))
                    logger.info(f"[{group_id}] 设置复读cd {to_set_cd}秒")
            else:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("参数有误，请检查格式\n示例：设置复读cd300秒")
                ]))
            return

        #   设置复读概率
        #   权限：管理员/群主/superman
        #   是否At机器人：否
        if text.startswith("设置复读概率"):
            to_set_value = -1
            arg_error = False
            try:
                to_set_value = int(text.lstrip("设置复读概率").rstrip("%"))  # 获取参数
            except ValueError:
                logger.warning(f"[{group_id}] 设置复读概率 参数错误")
            if not arg_error:
                if 0 <= to_set_value <= 100:
                    new_value = update_config(group_id, "repeatChance", to_set_value)
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"当前复读概率：{new_value}%")
                    ]))
                    logger.info(f"[{group_id}] 设置复读概率 {new_value}%")
                else:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain("错误：概率为介于0~100之间的值\n示例：设置复读概率50%")
                    ]))
            return

        #   查看当前参数
        #   权限：管理员/群主/superman
        #   是否At机器人：否
        if text == "查看当前参数":
            logger.info(f"[{group_id}] 查看参数")
            to_reply_text = ''  # 生成参数字符串
            to_reply_text += f"当前复读概率：{fetch_config(group_id, 'repeatChance')}%\n"
            to_reply_text += f"当前复读cd：{fetch_config(group_id, 'repeatCD')}秒\n"
            to_reply_text += f"当前图片cd：{fetch_config(group_id, 'replyCD')}秒"
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(to_reply_text)
            ]))
            return

        #   添加关键词
        #   权限：管理员/群主/superman
        #   是否At机器人：否
        if text.startswith("添加关键词") or text.startswith("增加关键词"):
            arg = text[5:].replace("，", ",").split(',')
            if not len(arg) == 2:
                logger.warning(f"[{group_id}] 添加关键词 参数数量错误")
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("错误：参数数量错误")
                ]))
            else:
                result = append_keyword(group_id, arg[0], arg[1])
                if result == "KEY_NOT_EXIST":
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"未找到{arg[0]}，请检查名称是否正确")
                    ]))
                elif result == "DUPLICATE_KEY":
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"{arg[0]} 中关键词：{arg[1]} 已存在")
                    ]))
                elif result == "SUCCESS":
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"成功向 {arg[0]} 中添加了关键词：{arg[1]}")
                    ]))
            return

        #   删除关键词
        #   权限：管理员/群主/superman
        #   是否At机器人：否
        if text[:5] == "删除关键词":
            arg = text[5:].replace("，", ",").split(',')
            if not len(arg) == 2:
                logger.warning(f"[{group_id}] 删除关键词 参数数量错误")
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain("错误：参数数量错误")
                ]))
            else:
                result = remove_keyword(group_id, arg[0], arg[1])
                if result == "KEY_NOT_EXIST":
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"未找到{arg[0]}，请检查名称是否正确")
                    ]))
                elif result == "WORD_NOT_EXIST":
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"{arg[0]} 中未找到关键词：{arg[1]}")
                    ]))
                elif result == "SUCCESS":
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f"成功删除了 {arg[0]} 中的关键词：{arg[1]}")
                    ]))
            return

        #   管理员普通操作结束

    #   非管理员普通操作开始

    #   毛力爬爬爬
    #   权限：成员
    #   是否At机器人：否
    if ("moca" in text or "摩卡" in text or "毛力" in text) and ("爬" in text or "爪巴" in text):
        if not is_in_cd(runtime_var, group_id, "keaiPaCD"):
            if random_do(fetch_config(group_id, "keaiPaChance")):
                update_cd(runtime_var, group_id, "keaiPaCD")
                logger.info(f"[{group_id}] moca爬了")
                random_file = random.choice(os.listdir(os.path.join(config.resource_path, "pa")))
                await app.sendGroupMessage(group, MessageChain.create([
                    Image.fromLocalFile(os.path.join(config.resource_path, 'pa', random_file))
                ]))
            else:
                logger.debug(f"[{group_id}] moca爬，但是没有命中概率")
        else:
            logger.debug(f"[{group_id}] moca爬，但是cd冷却中")
        await update_count(group_id, "爬")
        return

    #   毛力可爱爱
    #   权限：成员
    #   是否At机器人：否
    if ("moca" in text or "摩卡" in text or "毛力" in text) and ("可爱" in text or "老婆" in text):
        if not is_in_cd(runtime_var, group_id, "keaiPaCD"):
            if random_do(fetch_config(group_id, "keaiPaChance")):
                update_cd(runtime_var, group_id, "keaiPaCD")
                random_file = random.choice(os.listdir(os.path.join(config.resource_path, "keai")))
                await app.sendGroupMessage(group, MessageChain.create([
                    Image.fromLocalFile(os.path.join(config.resource_path, 'keai', random_file))
                ]))
                logger.info(f"[{group_id}] moca可爱")
            else:
                logger.debug(f"[{group_id}] moca可爱，但是没有命中概率")
        else:
            logger.debug(f"[{group_id}] moca可爱，但是cd冷却中")
        await update_count(group_id, '可爱')
        return

    #   多来点lp/来点lp
    #   权限：成员
    #   是否At机器人：否
    p_text = text.replace("老婆", "lp")
    if "来点" in p_text and "lp" in p_text:
        twice_lp = p_text.startswith("多")
        if not exp_enabled(group_id):
            twice_lp = False
        lp_name = fetch_lp(member.id)
        if lp_name == "NOT_DEFINED":
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("az，似乎你还没有设置lp呢，用“wlp是xxx”来设置一个吧")
            ]))
            return
        if lp_name in json.loads(r.hget('KEYWORDS', group_id)):
            if is_superman(member.id):  # 特 权 阶 级
                files = [rand_pic(lp_name), rand_pic(lp_name), rand_pic(lp_name)]
                await app.sendGroupMessage(group, MessageChain.create([
                    Image.fromLocalFile(os.path.join(config.pic_path, lp_name, files[0])),
                    Image.fromLocalFile(os.path.join(config.pic_path, lp_name, files[1])),
                    Image.fromLocalFile(os.path.join(config.pic_path, lp_name, files[2]))
                ]))
                await update_count(group_id, lp_name)
            else:
                if not is_in_cd(runtime_var, group_id, "replyCD"):
                    file = rand_pic(lp_name)
                    if twice_lp:
                        status = consume_pan(member.id, r, twice_lp_pan_amount, PAN_TWICE_LP_CONSUME)
                        if status[0]:
                            files = [rand_pic(lp_name), rand_pic(lp_name)]
                            await app.sendGroupMessage(group, MessageChain.create([
                                Plain(f"你吃掉了{twice_lp_pan_amount}个面包，还剩{status[1]}个面包哦~"),
                                Image.fromLocalFile(os.path.join(config.pic_path, lp_name, files[0])),
                                Image.fromLocalFile(os.path.join(config.pic_path, lp_name, files[1]))
                            ]))
                        else:
                            if status[1] == 0:
                                stat_text = "你没有面包了呢~"
                            else:
                                stat_text = f"只剩{status[1]}个面包了呢~"
                            await app.sendGroupMessage(group, MessageChain.create([
                                Plain(f"呜呜呜，面包不够了~你需要{twice_lp_pan_amount}个面包，但是{stat_text}")
                            ]))
                    else:
                        await app.sendGroupMessage(group, MessageChain.create([
                            Image.fromLocalFile(os.path.join(config.pic_path, lp_name, file))
                        ]))
                    await update_count(group_id, lp_name)
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("az，这个群没有找到你lp呢~")
            ]))
        return

    #   设置lp
    #   权限：成员
    #   是否At机器人：否
    p_text = text.replace("老婆", "lp").replace("我", "w")
    if p_text.startswith("wlp是"):
        lp_name = p_text[4:].replace("？", "?")
        if not bool(lp_name):
            return
        if "?" in lp_name or "谁" in lp_name:
            lp_name = fetch_lp(member.id)
            if lp_name == "NOT_DEFINED":
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain('az，你还没有设置lp呢，用“wlp是xxx”来设置一个吧~')
                ]))
            else:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f'你设置的lp为：{lp_name}')
                ]))
        else:
            true_lp_name = match_lp(group_id, lp_name)
            if true_lp_name == "NOT_FOUND":
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain('az，这个群没有找到nlp呢...\n可设置的lp是关键词列表中的任一人物哦\n发送“@モカ 关键词列表”来查看关键词列表')
                ]))
            else:
                await update_lp(member.id, true_lp_name)
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f'用户{member.name}设置lp为：{true_lp_name}')
                ]))
        return

    #   随机选歌
    #   权限：成员
    #   是否At机器人：否
    p_text = text.replace("；", ";").replace("，", ",").replace(" ", "")
    if p_text.startswith("随机选歌"):
        timestamp = int(round(time.time() * 1000))
        para = {"mode": "random", "time": timestamp}
        paras = p_text[4:].split(';')
        for t in paras:
            if t[:2] == '乐队':
                para["band"] = t[2:]
            if t[:2] == '难度':
                para["diff"] = t[2:]
            if t[:2] == '类型':
                para["level"] = t[2:]
            if t[:2] == '比赛':
                para["data"] = 'comp'
        # logger.info(para)
        res = requests.get(config.random_url, params=para)
        # logger.info(res.url)
        # logger.info("result: " + res.text)
        result = json.loads(res.text)
        if result.get("msg") == "error":
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("筛选条件有误，请检查")
            ]))
        result_song = result.get('result')[0]
        result_name = result_song.get('name')
        result_band = dictionary['band'].get(result_song.get('band'))
        result_level = dictionary['level'].get(result_song.get('level'))
        result_diff = result_song.get('diff')
        result_type = dictionary['type'].get(result_song.get('type'))
        await app.sendGroupMessage(group, MessageChain.create([
            At(target=member.id),
            Plain(f"\n筛选条件：乐队:{para.get('band')}；难度:{para.get('diff')}；类型:{para.get('level')}\n选歌结果：\n{result_name} - {result_band}\n{result_level} {result_diff}，{result_type}曲".replace("None", "无"))
        ]))
        return

    #   百度翻译
    #   权限：成员
    #   是否At机器人：否
    if text.startswith("翻译") and not is_in_cd(runtime_var, group_id, "replyCD"):
        if len(text) > 2:
            try:
                trans_content = message.asDisplay().lstrip("翻译")
                from_lang = 'auto'
                to_lang = 'zh'
                salt = random.randint(32768, 65536)
                sign = config.appid + trans_content + str(salt) + config.secret_key
                sign = hashlib.md5(sign.encode()).hexdigest()
                api_url = f'{config.trans_url}?appid={config.appid}&q={urllib.parse.quote(trans_content)}&from={from_lang}&to={to_lang}&salt={salt}&sign={sign}'
                res = requests.get(api_url)
                dict_res = json.loads(res.text)
                if 'error_code' in dict_res:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f'错误：{error_dict.get(dict_res.get("error_code"))}')
                    ]))
                    return
                detect_from_lang = lang_dict.get(dict_res.get("from"))
                if not detect_from_lang:
                    detect_from_lang = "未知"
                result = f'百度翻译 源语言：{detect_from_lang}\n'
                trans_data = dict_res.get('trans_result')
                for data in trans_data:
                    result += f"{data.get('dst')}\n"
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(result)
                ]))
                update_cd(runtime_var, group_id, "replyCD")
            except Exception as e:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f'错误：{repr(e)}')
                ]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain('错误：无翻译内容')
            ]))
        return

    #   加载关键词
    group_keywords = json.loads(r.hget('KEYWORDS', group_id))

    #   查看自己换lp次数
    #   权限：成员
    #   是否At机器人：否
    if '换lp次数' in text.replace("老婆", "lp"):
        count = fetch_clp_times(member.id)
        if count > 0:
            await app.sendGroupMessage(group, MessageChain.create([
                At(target=member.id),
                Plain(f' 你换了{count}次lp了哦~')
            ]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                At(target=member.id),
                Plain(' 你还没有换过lp呢~')
            ]))
        return

    # 检查是否启用实验功能
    if exp_enabled(group_id):
        #   买面包
        #   权限：成员
        #   是否At机器人：否
        if text == '买面包' or text == '来点面包':
            status = buy_pan(member.id, r)
            if status[0]:
                buy_amount = status[2]
                user_amount = status[3]
                await app.sendGroupMessage(group, MessageChain.create([
                    At(target=member.id),
                    Plain(f' 成功购买了{buy_amount}个面包哦~\n你现在有{user_amount}个面包啦~')
                ]))
            else:
                buy_interval = status[1] + BUY_PAN_INTERVAL - get_timestamp()
                if buy_interval < 60:
                    str_next_buy_time = f"{buy_interval}秒"
                else:
                    if buy_interval % 60 == 0:
                        str_next_buy_time = f"{buy_interval / 60}分钟"
                    else:
                        str_next_buy_time = f"{int(buy_interval / 60)}分钟{buy_interval % 60}秒"
                await app.sendGroupMessage(group, MessageChain.create([
                    At(target=member.id),
                    Plain(f' 还不能购买呢~\n还要等{str_next_buy_time}才能再买哦~')
                ]))
            return

        #   查看面包
        #   权限：成员
        #   是否At机器人：否
        if text == '我的面包' or text == '面包数量':
            pan_amount = get_pan_amount(member.id, r)
            if pan_amount == 0:
                re_text = " 你还没有面包呢~"
            else:
                re_text = f' 你现在有{pan_amount}个面包呢~'
            await app.sendGroupMessage(group, MessageChain.create([
                At(target=member.id),
                Plain(re_text)
            ]))
            return

        #   吃面包
        #   权限：成员
        #   是否At机器人：否
        if text == '吃面包' or text == '恰面包':
            status = eat_pan(member.id, r)
            if status[0]:
                await app.sendGroupMessage(group, MessageChain.create([
                    At(target=member.id),
                    Plain(f" 你吃掉了{EAT_PAN_AMOUNT}个面包，还剩{status[1]}个面包哦~")
                ]))
            else:
                await app.sendGroupMessage(group, MessageChain.create([
                    At(target=member.id),
                    Plain(f"呜呜呜，你似乎没有面包了呢~")
                ]))
            return

    #   遍历查询是否在关键词列表中并发送图片
    #   权限：成员
    #   是否At机器人：否
    for keys in group_keywords:  # 在字典中遍历查找
        for e in range(len(group_keywords[keys])):  # 遍历名称
            if text == group_keywords[keys][e]:  # 若命中名称
                if not is_in_cd(runtime_var, group_id, "replyCD") or is_superman(member.id):  # 判断是否在回复图片的cd中
                    pic_name = rand_pic(keys)
                    logger.info(f"[{group_id}] 请求：{keys} , {pic_name}")
                    await app.sendGroupMessage(group, MessageChain.create([
                        Image.fromLocalFile(os.path.join(config.pic_path, keys, pic_name))
                    ]))
                    await update_count(group_id, keys)  # 更新统计次数
                    update_cd(runtime_var, group_id, "replyCD")  # 更新cd
                return

    for keys in group_keywords:  # 在字典中遍历查找
        for e in range(len(group_keywords[keys])):  # 遍历名称
            if group_keywords[keys][e] in text:  # 若命中名称
                if not is_in_cd(runtime_var, group_id, "replyCD") or is_superman(member.id):  # 判断是否在回复图片的cd中
                    twice_lp = p_text.startswith("多")
                    if not exp_enabled(group_id):
                        twice_lp = False
                    if twice_lp:
                        status = consume_pan(member.id, r, twice_lp_pan_amount, PAN_TWICE_LP_CONSUME)
                        if status[0]:
                            pics = [rand_pic(keys), rand_pic(keys)]
                            logger.info(f"[{group_id}] 请求：{keys} , {pics[0]}|{pics[1]}")
                            await app.sendGroupMessage(group, MessageChain.create([
                                Plain(f"你吃掉了{twice_lp_pan_amount}个面包，还剩{status[1]}个面包哦~"),
                                Image.fromLocalFile(os.path.join(config.pic_path, keys, pics[0])),
                                Image.fromLocalFile(os.path.join(config.pic_path, keys, pics[1]))
                            ]))
                        else:
                            if status[1] == 0:
                                stat_text = "你没有面包了呢~"
                            else:
                                stat_text = f"只剩{status[1]}个面包了呢~"
                            await app.sendGroupMessage(group, MessageChain.create([
                                Plain(f"呜呜呜，面包不够了~你需要{twice_lp_pan_amount}个面包，但是{stat_text}")
                            ]))
                    else:
                        pic_name = rand_pic(keys)
                        logger.info(f"[{group_id}] 请求：{keys} , {pic_name}")
                        await app.sendGroupMessage(group, MessageChain.create([
                            Image.fromLocalFile(os.path.join(config.pic_path, keys, pic_name))
                        ]))
                    await update_count(group_id, keys)  # 更新统计次数
                    update_cd(runtime_var, group_id, "replyCD")  # 更新cd
                return

    #   遍历查询是否在语录列表中并发送语录
    #   权限：成员
    #   是否At机器人：否
    quo_data = r.hgetall('QUOTATION_LIST')
    for name in quo_data:
        for key in quo_data[name].split(","):
            if key in text:
                if not is_in_cd(runtime_var, group_id, "replyCD") or is_superman(member.id):
                    quo_words = r.hget("QUOTATION", name).split(',')
                    quote = random.choice(quo_words)
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(quote.strip())
                    ]))
                    logger.info(f"[{group_id}] 请求：{name}")
                    await update_count(group_id, name)  # 更新统计次数
                return

    #   复读机
    data = repeater(runtime_var, group_id, message)
    if data[0]:
        if data[1]:
            await app.sendGroupMessage(group, MessageChain.create([
                Image.fromLocalFile(os.path.join(config.resource_path, "fudu", "fudu.jpg"))
            ]))
        await app.sendGroupMessage(group, message.asSendable())
        update_cd(runtime_var, group_id, "repeatCD")

    #   非管理员普通操作结束

    #   普通操作结束
    #   每300秒更新一次图片列表
    if get_timestamp() - runtime_var['file_list_update_time'] > 300:
        runtime_var['file_list_update_time'] = get_timestamp()
        await update_file_list()


@bcc.receiver(MemberJoinEvent)
async def group_welcome_join_handler(group: Group, member: Member):
    #   欢迎新成员加入
    logger.info(f"[{group.id}] {member.id} 加入了 {group.id}")
    if fetch_config(group.id, "welcomeNewMemberJoin") == 1:
        await app.sendGroupMessage(group, MessageChain.create([
            At(target=member.id),
            Plain(f' 欢迎加入{group.name}！')
        ]))


@bcc.receiver(BotInvitedJoinGroupRequestEvent)
async def superman_invite_join_group(event: BotInvitedJoinGroupRequestEvent):
    # 自动接收邀请
    logger.info(f"{event.supplicant} invited me to group {event.groupId}, {event.groupName}")
    if is_superman(event.supplicant):
        logger.info("Superman invited me into a group, accept")
        await event.accept("Auto accept")
    else:
        logger.info("Non-superman invited, reject")
        await event.reject("Auto reject")


@bcc.receiver(BotJoinGroupEvent)
async def bot_join_group(group: Group):
    # 自动发送使用说明
    print(f"bot join {group.id}")
    await app.sendGroupMessage(group, MessageChain.create([
        Plain(f'大家好，我是mocaBot\n使用说明：http://mocabot.cn/')
    ]))


@bcc.receiver(MemberLeaveEventKick)
async def superman_kick_from_group(member: Member, group: Group):
    # superman被踢自动退出
    if is_superman(member.id):
        print(f"Superman leaving {group.id}")
        print(f"bye bye {group.id}")
        await app.quit(group)


app.launch_blocking()
