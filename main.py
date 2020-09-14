import asyncio
import time
import traceback

from graia.application import GraiaMiraiApplication, Session
from graia.application.group import Group, Member, MemberPerm
from graia.application.message.elements.internal import Plain, Image, At
from graia.broadcast import Broadcast
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

string = '/\:*<>|"'

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


# noinspection PyBroadException
@bcc.receiver("GroupMessage")
async def group_message_handler(app: GraiaMiraiApplication, message: MessageChain, group: Group, member: Member):
    text = message.asDisplay().replace(" ", "").lower()
    group_id = group.id
    print(text)
    if message.has(At):
        at_data = message.get(At)[0].dict()
        at_target = at_data['target']
        at_target_name = at_data['display'].lstrip("@")

        if at_target == app.connect_info.account:  # At毛力的操作开始
            logger.debug(f"[{group_id}] At了毛力")
            if member.permission == MemberPerm.Administrator or \
                    member.permission == MemberPerm.Owner or \
                    member.id == config.superman:
                logger.debug(f"[{group_id}] 管理员At了毛力")

                #   管理员At操作开始

                #   管理员At操作结束

            #   非必须管理员At操作开始

            #   查看统计次数
            #   权限：成员
            #   是否At机器人：是
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

            #   查看关键词列表
            #   权限：成员
            #   是否At机器人：是
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

            #   查看图片数量
            #   权限：成员
            #   是否At机器人：是
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

            #   毛力爬
            #   权限：成员；
            #   是否At机器人：是
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

            #   毛力可爱
            #   权限：成员
            #   是否At机器人：是
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

            #   提交图片
            #   权限：成员
            #   是否At机器人：是
            if '提交图片' in text:
                error_flag = False
                if len(text) > 4:
                    logger.info(f"[{group_id}] 提交图片")
                    data_list = []

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
                    if not bool(data_list):
                        await app.sendGroupMessage(group, MessageChain.create([
                            Plain("错误：没有图片")
                        ]))
                        return
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
                        except Exception:
                            logger.error(str(traceback.format_exc()))
                            error_flag = True
                    if error_flag:
                        await app.sendGroupMessage(group, MessageChain.create([
                            Plain('错误：提交失败')
                        ]))
                    else:
                        file_count = len(data_list)
                        await app.sendGroupMessage(group, MessageChain.create([
                            Plain(f'成功，收到{file_count}张图片')
                        ]))
                else:
                    await app.sendGroupMessage(group, MessageChain.create([
                        Plain(f'错误：参数错误')
                    ]))
                return
            #   非必须管理员At操作结束
        else:
            #   At了他人的操作开始

            #   查看他人换lp次数
            #   权限：成员
            #   是否At机器人：否
            #   需At任意群员
            logger.debug(f"[{group_id}] At {at_target_name} {at_target}")
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
            #   At了他人的操作结束

    #   普通操作开始
    if member.permission == MemberPerm.Administrator or \
            member.permission == MemberPerm.Owner or \
            member.id == config.superman:
        #   管理员普通操作开始

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
        await update_count(group_id, "爬")
        return

    #   毛力可爱爱
    #   权限：成员
    #   是否At机器人：否
    if ("moca" in text or "摩卡" in text or "毛力" in text) and ("可爱" in text or "老婆" in text):
        if not is_in_cd(group_id, "keaiPaCD"):
            if random_do(fetch_config(group_id, "keaiPaChance")):
                await update_cd(group_id, "keaiPaCD")
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

    #   来点lp
    #   权限：成员
    #   是否At机器人：否
    p_text = text.replace("老婆", "lp")
    if "来点" in p_text and "lp" in p_text:
        lp_name = fetch_lp(member.id)
        if lp_name == "NOT_DEFINED":
            await app.sendGroupMessage(group, MessageChain.create([
                Plain("az，似乎你还没有设置lp呢，用“wlp是xxx”来设置一个吧")
            ]))
            return
        if lp_name in json.loads(r.hget('KEYWORDS', group_id)):
            if member.id == config.superman:  # 特 权 阶 级
                files = [rand_pic(lp_name), rand_pic(lp_name), rand_pic(lp_name)]
                await app.sendGroupMessage(group, MessageChain.create([
                    Image.fromLocalFile(os.path.join(config.pic_path, lp_name, files[0])),
                    Image.fromLocalFile(os.path.join(config.pic_path, lp_name, files[1])),
                    Image.fromLocalFile(os.path.join(config.pic_path, lp_name, files[2]))
                ]))
                await update_count(group_id, lp_name)
            else:
                if not is_in_cd(group_id, "replyCD"):
                    file = rand_pic(lp_name)
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
    if text.startswith("wlp是"):
        lp_name = p_text[4:].replace("？", "?")
        if "?" in lp_name:
            lp_name = fetch_lp(member.id)
            if lp_name == "NOT_DEFINED":
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain('az，你还没有设置lp呢，用“wlp是xxx”来设置一个吧~')
                ]))
            else:
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f'你设置的lp为: {lp_name}')
                ]))
        else:
            true_lp_name = match_lp(group_id, lp_name)
            if true_lp_name == "NOT_FOUND":
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain('az，这个群没有找到nlp呢...')
                ]))
            else:
                await update_lp(member.id, true_lp_name)
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(f'用户{member.name}设置lp为：{true_lp_name}')
                ]))
        return

    #   查看自己换lp次数
    #   权限：成员
    #   是否At机器人：否
    if '换lp次数' in text.replace("老婆", "lp"):
        count = fetch_clp_times(member.id)
        if count > 0:
            await app.sendGroupMessage(group, MessageChain.create([
                At(target=member.id),
                Plain(f'你换了{count}次lp了哦~')
            ]))
        else:
            await app.sendGroupMessage(group, MessageChain.create([
                At(target=member.id),
                Plain('你还没有换过lp呢~')
            ]))
        return

    #   遍历查询是否在关键词列表中并发送图片
    #   权限：成员
    #   是否At机器人：否
    group_keywords = json.loads(r.hget('KEYWORDS', group_id))
    for keys in group_keywords:  # 在字典中遍历查找
        for e in range(len(group_keywords[keys])):  # 遍历名称
            if text == group_keywords[keys][e]:  # 若命中名称
                if not is_in_cd(group_id, "replyCD") or member.id == config.superman:  # 判断是否在回复图片的cd中
                    pic_name = rand_pic(keys)
                    logger.info(f"[{group_id}] 请求：{keys} , {pic_name}")
                    await app.sendGroupMessage(group, MessageChain.create([
                        Image.fromLocalFile(os.path.join(config.pic_path, keys, pic_name))
                    ]))
                    await update_count(group_id, keys)  # 更新统计次数
                    await update_cd(group_id, "replyCD")  # 更新cd
                return

    for keys in group_keywords:  # 在字典中遍历查找
        for e in range(len(group_keywords[keys])):  # 遍历名称
            if group_keywords[keys][e] in text:  # 若命中名称
                if not is_in_cd(group_id, "replyCD") or member.id == config.superman:  # 判断是否在回复图片的cd中
                    pic_name = rand_pic(keys)
                    logger.info(f"[{group_id}] 请求：{keys} , {pic_name}")
                    await app.sendGroupMessage(group, MessageChain.create([
                        Image.fromLocalFile(os.path.join(config.pic_path, keys, pic_name))
                    ]))
                    await update_count(group_id, keys)  # 更新统计次数
                    await update_cd(group_id, "replyCD")  # 更新cd
                return

    #   遍历查询是否在语录列表中并发送语录
    #   权限：成员
    #   是否At机器人：否
    quo_data = r.hgetall('QUOTATION_LIST')
    for name in quo_data:
        if text in quo_data[name]:
            if not is_in_cd(group_id, "replyCD") or member.id == config.superman:
                quo_words = r.hget("QUOTATION", name).split(',')
                quote = random.choice(quo_words)
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(quote.strip())
                ]))

                logger.info(f"[{group_id}] 请求：{name}")
                await update_count(group_id, name)  # 更新统计次数
            return

    # data = repeater(group_id, message)
    # if data[0]:
    #     if data[1]:
    #         await app.sendGroupMessage(group, MessageChain.create([
    #             Image.fromLocalFile(os.path.join(config.resource_path, "fudu", "fudu.jpg"))
    #         ]))
    #     await app.sendGroupMessage(group, message.asSendable())
    #     await update_cd(group_id, "repeatCD")

    #   非管理员普通操作结束

    #   普通操作结束


app.launch_blocking()
