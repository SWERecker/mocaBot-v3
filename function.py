import difflib
import logging
import os
import re
import time

import redis
import random
import json

import requests
from graia.application import MessageChain

import config
from PIL import Image as ImageLib
from PIL import ImageDraw, ImageFont
from prettytable import PrettyTable
from pypinyin import lazy_pinyin

pool = redis.ConnectionPool(host='localhost', port=6379, db=0, decode_responses=True)
r = redis.Redis(connection_pool=pool)
cache_pool = redis.ConnectionPool(host='localhost', port=6379, db=1, decode_responses=True)
rc = redis.Redis(connection_pool=cache_pool)

logger = logging.getLogger('botlogger')

lang_dict = {
    "zh": "中文",
    "en": "英语",
    "yue": "粤语",
    "wyw": "文言文",
    "jp": "日语",
    "kor": "韩语",
    "fra": "法语",
    "spa": "西班牙语",
    "th": "泰语",
    "ara": "阿拉伯语",
    "ru": "俄语",
    "pt": "葡萄牙语",
    "de": "德语",
    "it": "意大利语",
    "el": "希腊语",
    "nl": "荷兰语",
    "pl": "波兰语",
    "bul": "保加利亚语",
    "est": "爱沙尼亚语",
    "dan": "丹麦语",
    "fin": "芬兰语",
    "cs": "捷克语",
    "rom": "罗马尼亚语",
    "slo": "斯洛文尼亚语",
    "swe": "瑞典语",
    "hu": "匈牙利语",
    "cht": "繁体中文",
    "vie": "越南语"
}

error_dict = {
    "52001": "请求超时",
    "52002": "系统错误",
    "54003": "API访问频率受限",
    "54004": "账户余额不足"
}


def get_timestamp() -> int:
    """
    获取秒级的时间戳

    :return: 秒级时间戳
    """
    return int(time.time())


def update_config(group_id: int, arg: str, value):
    """
    向Redis中更新某参数.

    :param group_id: QQ群号
    :param arg: 参数名称
    :param value: 参数值
    :return: 新参数值
    """
    config_data = json.loads(r.hget("CONFIG", group_id))
    config_data[arg] = value
    r.hset("CONFIG", group_id, json.dumps(config_data, ensure_ascii=False))
    logger.debug(f"[{group_id}] 设置CONFIG {arg} = {value}")
    return value


def fetch_config(group_id: int, arg: str):
    """
    从Redis数据库中查询某参数.

    :param group_id: QQ群号 (int)
    :param arg: 参数名称 (str)
    :return: 参数值 (any)
    """
    if not r.hexists("CONFIG", group_id):
        r.hset("CONFIG", group_id, r.hget("CONFIG", "config_template"))
        logger.info(f"[{group_id}] 初始化参数")
    config_data = json.loads(r.hget("CONFIG", group_id))
    value = config_data.get(arg)
    logger.debug(f"[{group_id}] 获取CONFIG {arg} = {value}")
    return value


def update_cd(runtime_var: dict, group_id: int, cd_type: str, cd_time=0):
    """
    更新某群组的某类cd.

    :param runtime_var: 运行时变量dict
    :param group_id: QQ群号(int)
    :param cd_type: 参数名称(str)
    :param cd_time: cd时间（可选，如不指定则从数据库中查找）
    :return: None
    """
    if not cd_time == 0:
        # rc.set(f'in_{cd_type}_cd_{group_id}', '1', ex=cd_time)
        runtime_var[f'in_{cd_type}_cd_{group_id}'] = get_timestamp() + cd_time
    else:
        group_cd = fetch_config(group_id, cd_type)
        # rc.set(f'in_{cd_type}_cd_{group_id}', '1', ex=group_cd)
        runtime_var[f'in_{cd_type}_cd_{group_id}'] = get_timestamp() + group_cd


def is_in_cd(runtime_var: dict, group_id: int, cd_type: str) -> bool:
    """
    判断是否在cd中.
    :param runtime_var: 运行时变量dict
    :param group_id: QQ群号
    :param cd_type: 要查询的cd类型
    :return: True/False
    """
    # return rc.exists(f'in_{cd_type}_cd_{group_id}')
    if f'in_{cd_type}_cd_{group_id}' in runtime_var:
        if get_timestamp() > runtime_var.get(f'in_{cd_type}_cd_{group_id}'):
            return False
        else:
            return True
    else:
        return False


async def update_lp(qq: int, lp_name: str):
    """
    更新设置的lp，同时更新换lp次数.

    :param qq: 要查询的QQ号(int)
    :param lp_name: 要增/改的名称(str)
    :return: None
    """
    r.hset("LPLIST", qq, lp_name)
    if not r.hexists("CLPTIME", qq):
        r.hset("CLPTIME", qq, '0')
    else:
        r.hincrby("CLPTIME", qq)
    logger.info(f"修改lp记录：用户{qq}设置lp为:{lp_name}")


def fetch_lp(qq: int) -> str:
    """
    获取设置的lp.

    :param qq: 要查询的QQ号
    :return: lp名称, 未设置时返回"NOT_DEFINED"
    """
    if r.hexists("LPLIST", qq):
        return r.hget("LPLIST", qq)
    else:
        return "NOT_DEFINED"


def random_do(chance: int) -> bool:
    """
    随机事件 {chance}% 发生.

    :param chance: 0~100,
    :return: 发生(True)，不发生(False)
    """
    if random.random() < (int(chance) / 100):
        return True
    else:
        return False


def init_config(group_id: int):
    """
    初始化参数.

    :param group_id: QQ群号
    :return None
    """
    if not r.hexists("CONFIG", group_id):
        r.hset("CONFIG", group_id, r.hget("CONFIG", "config_template"))


async def update_file_list():
    """
    读取文件列表缓存至Redis数据库.

    :return: None
    """
    names_list = os.listdir(config.pic_path)
    for name in names_list:
        if os.path.isdir(os.path.join(config.pic_path, name)):
            file_list = os.listdir(os.path.join(config.pic_path, name))
            rc.hset("FILES", name, json.dumps(file_list, ensure_ascii=False))
            logger.debug(f"建立 {name} 文件列表缓存")
    logger.info('重建图片索引完成')


def remove_keyword(group_id: int, key: str, value: str) -> str:
    """
    删除某人物关键词列表中的某个关键词.

    :param group_id: QQ群号
    :param key: 名称
    :param value: 关键词
    :return: KEY_NOT_EXIST: 名称不存在; WORD_NOT_EXIST: 关键词不存在; SUCCESS: 成功
    """
    group_keywords = json.loads(r.hget('KEYWORDS', group_id))
    if not group_keywords.get(key):
        logger.warning(f"[{group_id}] 名称 {key} 不存在")
        return "KEY_NOT_EXIST"
    if value in group_keywords.get(key):
        group_keywords[key].remove(value)
        r.hset('KEYWORDS', group_id, json.dumps(group_keywords, ensure_ascii=False))
        logger.info(f"[{group_id}] 删除 {key} 中的关键词 {value}")
        return "SUCCESS"
    else:
        logger.warning(f"[{group_id}] {key} 中不存在关键词 {value}")
        return "WORD_NOT_EXIST"


def append_keyword(group_id: int, key: str, value: str) -> str:
    """
    向某个人物的关键词列表中添加关键词.

    :param group_id: QQ群号
    :param key: 名称
    :param value: 关键词
    :return: KEY_NOT_EXIST: 名称不存在; DUPLICATE_KEY: 关键词重复; SUCCESS: 成功
    """
    group_keywords = json.loads(r.hget('KEYWORDS', group_id))
    if not group_keywords.get(key):
        logger.warning(f"[{group_id}] 名称 {key} 不存在")
        return "KEY_NOT_EXIST"
    if value in group_keywords[key]:
        logger.warning(f"[{group_id}] 向 {key} 中添加重复关键词 {value}")
        return "DUPLICATE_KEY"
    else:
        group_keywords[key].append(value)
        r.hset('KEYWORDS', group_id, json.dumps(group_keywords, ensure_ascii=False))
        logger.info(f"[{group_id}] 向 {key} 中添加关键词 {value}")
    return "SUCCESS"


async def update_count(group_id: int, name: str) -> bool:
    """
    更新次数（+1）.

    :param group_id: QQ群号
    :param name: 要+1的名称
    :return: True
    """
    if not r.hexists("COUNT", group_id):
        r.hset("COUNT", group_id, "{}")
    count_list = json.loads(r.hget("COUNT", group_id))
    if not count_list.get(name):
        count_list[name] = 1
        logger.info(f"[{group_id}] 更新 {name} COUNT = 1")
    else:
        count_list[name] += 1
        logger.info(f"[{group_id}] {name} COUNT + 1")
    r.hset("COUNT", group_id, json.dumps(count_list, ensure_ascii=False))
    return True


def fetch_picture_count_list(group_id: int) -> dict:
    """
    获取图片数量列表.

    :param group_id: 群号
    :return: 数量列表
    """
    group_keyword = json.loads(r.hget("KEYWORDS", group_id))
    file_list = rc.hgetall("FILES")
    result_list = {}
    for name in group_keyword:
        if name in file_list:
            result_list[name] = len(json.loads(file_list[name]))

    return result_list


def lp_list_rank():
    """
    统计设置为lp最多的10个.

    :return: 已从大到小排序的字典
    """
    result = {}
    lp_data = r.hgetall("LPLIST")
    for qq in lp_data:
        if not result.get(lp_data[qq]):
            result[lp_data[qq]] = 1
        else:
            result[lp_data[qq]] += 1
    sorted_dict = sorted(result.items(), key=lambda d: d[1], reverse=True)
    result = {}
    c = 0
    for k, v in sorted_dict:
        result[k] = v
        c += 1
        if c == 10:
            break
    return result


def rand_pic(name: str) -> str:
    """
    从图片库中随机抽取一张

    :param name: 名称
    :return: 图片文件名（名称不存在时返回"NAME_NOT_FOUND"）
    """
    if not rc.hexists("FILES", name):
        return "NAME_NOT_FOUND"
    file_list = json.loads(rc.hget("FILES", name))
    random.shuffle(file_list)
    return random.choice(file_list)


def fetch_clp_times(qq: int) -> int:
    """
    获取某人换lp次数

    :param qq: QQ号
    :return 换lp次数
    """
    if r.hexists("CLPTIME", qq):
        return int(r.hget("CLPTIME", qq))
    else:
        return 0


def match_lp(group_id: int, lp_name: str) -> str:
    """
    匹配最接近的lp.

    :param group_id: 群组ID
    :param lp_name: 名称
    :return: 最接近的名称，若匹配不到则返回NOT_FOUND
    """
    simi_dict = {}
    keyword_list = json.loads(r.hget("KEYWORDS", group_id))
    for keys in keyword_list:  # 在字典中遍历查找
        for e in range(len(keyword_list[keys])):  # 遍历名称
            seed = difflib.SequenceMatcher(None, str(lp_name), keyword_list[keys][e]).quick_ratio()
            if seed > 0.6:
                logger.debug(f"{lp_name} 最接近 : {keys} ,与 {keyword_list[keys][e]} 最相似 ,相似度为 ：{seed}")
                simi_dict.update({keys: seed})
    if bool(simi_dict):
        return sorted(simi_dict, key=simi_dict.__getitem__, reverse=True)[0]
    else:
        return "NOT_FOUND"


def create_dict_pic(data: dict, group_id_with_type: str, title: str):
    """
    将json转换为图片文件.

    :param data: Dict
    :param group_id_with_type: 群号_文件类型
    :param title: 表格第二列的标题
    :return: None, 写入{temp_path}/{名称}.png
    """
    tab = PrettyTable(border=False, header=True, header_style='title')
    font_file = os.path.join(config.resource_path, "font", "PingFang.ttf")
    bg_file = os.path.join(config.resource_path, "template", "bg.png")
    new_img_file = os.path.join(config.temp_path, f"{group_id_with_type}.png")
    # 设置表头
    tab.field_names = ["名称", title]
    tab.align["名称"] = "l"
    # 表格内容插入
    tab.add_row(["", ""])
    for item in data.items():
        tab.add_row([item[0], item[1]])
    tab_info = str(tab).replace("[", "").replace("]", "").replace(",", ", ").replace("'", " ")
    space = 50
    # PIL模块中，确定写入到图片中的文本字体
    font = ImageFont.truetype(font_file, 20, encoding='utf-8')
    # Image模块创建一个图片对象
    im = ImageLib.new('RGB', (10, 10), (255, 255, 255, 0))
    # ImageDraw向图片中进行操作，写入文字或者插入线条都可以
    draw = ImageDraw.Draw(im, "RGB")
    # 根据插入图片中的文字内容和字体信息，来确定图片的最终大小
    img_size = draw.multiline_textsize(tab_info, font=font)
    # 图片初始化的大小为10-10，现在根据图片内容要重新设置图片的大小
    im_new = im.resize((img_size[0] + int(space * 2), img_size[1] + int(space * 2)))
    del draw
    del im
    draw = ImageDraw.Draw(im_new, 'RGB')
    img = ImageLib.open(bg_file)
    im_new.paste(img, (0, 0))
    img_x, img_y = im_new.size
    bg_x, bg_y = img.size
    if bg_y < img_y:
        pos_y = 0
        while pos_y < img_y:
            im_new.paste(img, (0, pos_y))
            pos_y += bg_y
            logger.debug(f"pasted:y, {pos_y}")
    if bg_x < img_x:
        pos_x = 0
        pos_y = 0
        while pos_y < img_y:
            while pos_x < img_x:
                im_new.paste(img, (pos_x, pos_y))
                pos_x += bg_x
                logger.debug(f"pasted:x,y {pos_x},{pos_y}")
            pos_x = 0
            pos_y += bg_y
    draw.multiline_text((space, space), tab_info, fill=(0, 0, 0), font=font)
    im_new.save(new_img_file, "png")
    del draw


def repeater(runtime_var: dict, group_id: int, message: MessageChain) -> (bool, bool):
    """
    复读机.

    :param runtime_var: 运行时字典
    :param group_id: QQ群号
    :param message: 消息的MessageChain
    :return (bool: 是否复读, bool: 是否附带复读图片)
    """
    if not rc.hexists(group_id, "m_count"):
        rc.hset(group_id, "m_count", '0')
        rc.hset(group_id, "m_last_repeat", 'content')

    m_count = rc.hget(group_id, "m_count")
    excludeSourceMessage = re.sub(r"(?:\[mirai:source?:(.*?)?\])", "", message.asSerializationString())
    if m_count == '0':
        rc.hset(group_id, "m_cache_0", excludeSourceMessage)
        rc.hset(group_id, "m_count", '1')  # 消息计数+1
    if m_count == '1':
        rc.hset(group_id, "m_cache_1", excludeSourceMessage)
        rc.hset(group_id, "m_count", '2')
    if m_count == '2':
        rc.hset(group_id, "m_cache_0", rc.hget(group_id, "m_cache_1"))
        rc.hset(group_id, "m_cache_1", excludeSourceMessage)
    # 缓存消息 ===

    m_cache_0 = rc.hget(group_id, "m_cache_0")
    m_cache_1 = rc.hget(group_id, "m_cache_1")

    if not rc.hget(group_id, "m_last_repeat") == excludeSourceMessage:
        if m_cache_0 == m_cache_1:
            if not is_in_cd(runtime_var, group_id, "repeatCD"):
                if random_do(fetch_config(group_id, "repeatChance")):
                    logger.debug(f"[{group_id}] 命中复读条件且不在cd中且命中概率，需要复读")
                    rc.hset(group_id, "m_last_repeat", excludeSourceMessage)
                    if random_do(5):
                        return True, True
                    else:
                        return True, False
                else:
                    logger.debug(f"[{group_id}] 未命中复读概率")
            else:
                logger.debug(f"[{group_id}] 复读cd冷却中")
    return False, False


async def save_image(url: str, file_name: str, file_path: str):
    """
    保存提交的图片.

    :param url: 图片URL
    :param file_name: 图片保存的名称
    :param file_path: 图片保存路径（文件夹）
    :return: None
    """
    res = requests.get(url)
    content_type = res.headers.get("Content-Type")
    file_type = content_type.split('/')[1]
    logger.info(f"保存：{file_name}.{file_type}")
    with open(os.path.join(file_path, f"{file_name}.{file_type}"), "wb") as image_file:
        image_file.write(res.content)


def is_superman(member_id: int) -> bool:
    """
    判断是否是特权阶级.

    :param member_id: 用户QQ

    :return: True/False
    """
    if str(member_id) in rc.smembers("SUPERMAN"):
        return True
    else:
        return False


def sort_dict(origin_dict: dict) -> dict:
    """
    对dict进行排序

    :param origin_dict: 原字典

    :return: 排序后的字典
    """
    result = {}
    temp = sorted(origin_dict.keys(), key=lambda char: lazy_pinyin(char)[0][0])
    for og in temp:
        result[og] = origin_dict.get(og)
    return result
