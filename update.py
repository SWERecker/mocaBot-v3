import asyncio
import json
import os
import time

import requests

import config
import redis
from PIL import Image as pilImage
from PIL import ImageDraw, ImageFont


r = redis.Redis(db=0, decode_responses=True)
rc = redis.Redis(db=1, decode_responses=True)

abspath = os.path.join(os.path.dirname(os.path.abspath(__file__)))
auth_url = f'http://{config.server_ip}:{config.server_port}/auth'
verify_url = f'http://{config.server_ip}:{config.server_port}/verify'
groupMessage_url = f'http://{config.server_ip}:{config.server_port}/sendGroupMessage'
release_session = f'http://{config.server_ip}:{config.server_port}/release'

mirai_path = "/root/mirai"


def create_pic(data, group_id):
    """
    将数据转换为图片文件创建对象, 写入{mirai_path}/data/MiraiApiHttp/images/{group_id}_change.png.

    :param data: 数据
    :param group_id: 群号
    :return: 无

    """
    font_file = os.path.join(abspath, "resource", "font", "PingFang.ttf")
    bg_file = os.path.join(abspath, "resource", "template", "bg.png")
    new_img_file = os.path.join(mirai_path, "data", "MiraiApiHttp", "images", f"{group_id}_change.png")
    tab_info = data
    space = 50
    # PIL模块中，确定写入到图片中的文本字体
    font = ImageFont.truetype(font_file, 20, encoding='utf-8')
    # Image模块创建一个图片对象
    im = pilImage.new('RGB', (10, 10), (255, 255, 255, 0))
    # ImageDraw向图片中进行操作，写入文字或者插入线条都可以
    draw = ImageDraw.Draw(im, "RGB")
    # 根据插入图片中的文字内容和字体信息，来确定图片的最终大小
    img_size = draw.multiline_textsize(tab_info, font=font)
    # 图片初始化的大小为10-10，现在根据图片内容要重新设置图片的大小
    im_new = im.resize((img_size[0] + int(space * 2), img_size[1] + int(space * 2)))
    del draw
    del im
    draw = ImageDraw.Draw(im_new, 'RGB')
    img = pilImage.open(bg_file)
    im_new.paste(img, (0, 0))
    img_x, img_y = im_new.size
    bg_x, bg_y = img.size
    if bg_y < img_y:
        pos_y = 0
        while pos_y < img_y:
            im_new.paste(img, (0, pos_y))
            pos_y += bg_y
    if bg_x < img_x:
        pos_x = 0
        pos_y = 0
        while pos_y < img_y:
            while pos_x < img_x:
                im_new.paste(img, (pos_x, pos_y))
                pos_x += bg_x
            pos_x = 0
            pos_y += bg_y
    draw.multiline_text((space, space), tab_info, fill=(0, 0, 0), font=font)
    im_new.save(new_img_file, "png")
    del draw
    return f"{group_id}_change.png"
    
    
def compare_change(group_id, session_key):
    latest_file_count = {}
    latest_group_count = {}
    result_json = {}
    result_text = str(time.strftime('%Y-%m-%d %H:%M', time.localtime(time.time()))) + " 图片更新记录\n"

    names_list = os.listdir(config.pic_path)
    for name in names_list:
        if os.path.isdir(os.path.join(config.pic_path, name)):
            file_list = os.listdir(os.path.join(config.pic_path, name))
            latest_file_count[name] = len(file_list)

    group_keyword = json.loads(r.hget("KEYWORDS", group_id))

    storage_path = os.path.join(config.temp_path, "cache")
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)

    group_cache_file = os.path.join(storage_path, f"{group_id}.cache")

    if os.path.isfile(group_cache_file):
        with open(group_cache_file, 'r', encoding='utf-8')as cache_file:
            cache_dict = json.load(cache_file)

        for name in group_keyword:
            latest_count = cache_dict.get(name)
            latest_group_count[name] = latest_file_count[name]

            if not bool(latest_count):
                result_json[name] = f"{name}({latest_file_count[name]})*新增\n"
            else:
                delta = latest_file_count[name] - cache_dict[name]
                if delta > 0:
                    result_json[name] = f"{name}(+{delta})\n"
                if delta < 0:
                    result_json[name] = f"{name}({delta})\n"

        if bool(result_json):
            for name, result in result_json.items():
                result_text += result
            # print(result_json)
            filename = create_pic(result_text, group_id)

            print(f"Compared, Sending Image to {group_id}", mirai_reply_image(group_id, session_key, filename))
        else:
            print(f"[{group_id}] 统计没有变化")

        with open(group_cache_file, 'w', encoding='utf-8')as cache_file:
            cache_file.write(json.dumps(latest_group_count, ensure_ascii=False))

    else:
        print(f"[{group_id}] 缓存文件不存在，直接存储本次读取结果")
        for name in group_keyword:
            latest_group_count[name] = latest_file_count[name]
        with open(group_cache_file, 'w', encoding='utf-8')as cache_file:
            cache_file.write(json.dumps(latest_group_count, ensure_ascii=False))


def mirai_auth():
    """
    mirai认证.
    """
    auth_data = {'authKey': config.auth_key}
    verify_data = {'sessionKey': '', 'qq': config.bot_id}
    r_auth_json = requests.post(auth_url, json.dumps(auth_data))
    r_auth_json = json.loads(r_auth_json.text)
    verify_data['sessionKey'] = r_auth_json.get('session')

    r_verify_json = requests.post(verify_url, json.dumps(verify_data))
    r_verify_json = json.loads(r_verify_json.text)

    if r_verify_json.get('code') == 0:
        return r_auth_json.get('session')
    else:
        return r_verify_json.get('msg')


def mirai_reply_image(target_id, session_key, path=''):
    """
    回复图片.

    :param: target_id: 群号
    :param: session_key: sessionKey,
    :param: path: 图片相对于 %MiraiPath%/plugins/MiraiAPIHTTP/images/
    }
    :return: 正常时返回msg(success)，参数错误时返回"error_invalid_parameter"
    """
    if not target_id == '' and not session_key == '':
        data_dict = {"sessionKey": session_key, "target": target_id, "messageChain": [{"type": "Image", "path": path}]}

        if path == '':
            return
        final_data = json.dumps(data_dict)

        res = requests.post(url=groupMessage_url, data=final_data)
        r_json = json.loads(res.text)
        return r_json.get('msg')
    else:
        return 'error_invalid_parameter'


def mirai_close_session(session_key):
    """
    关闭mirai session
    """
    data = {'sessionKey': session_key, 'qq': config.bot_id}
    res = requests.post(url=release_session, data=json.dumps(data))
    r_json = json.loads(res.text)
    return r_json.get('msg')


if __name__ == "__main__":
    sk = mirai_auth()
    print("Getting sessionKey: ", sk)
    groups = rc.smembers("GROUPS")
    for group in groups:
        compare_change(int(group), sk)
    print("Closing session: ", mirai_close_session(sk))
