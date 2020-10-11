import datetime

import redis
import json
import time
from graia.application import GraiaMiraiApplication, MessageChain
from graia.application.message.elements.internal import Plain, At
from graia.application.group import Group

db_name = "SIGNIN"
R = redis.Redis


async def signin(qq: int, r: R, app: GraiaMiraiApplication, group: Group):
    """
    进行签到操作.

    :param qq: 要进行签到的QQ号
    :param r: Redis数据库对象
    :param app: Graia对象
    :param group: Group对象
    :return: None
    """
    exist_data = get_user_signin_data(qq, r)
    signin_time = get_time_now()
    str_time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(signin_time))
    if exist_data == {}:
        # 初次签到
        signin_data = {"time": signin_time, "pan": 5, "sum_day": 1}
        update_user_signin_data(qq, r, signin_data)
        await app.sendGroupMessage(group, MessageChain.create([
            At(target=qq),
            Plain(f"\n{str_time_now} \n初次签到成功！~\n摩卡给你5个面包哦~，你现在有5个面包啦~")
        ]))
    else:
        # 已存在数据
        last_signin_time = exist_data.get('time')
        exist_pan = exist_data.get('pan')
        today_start_timestamp = get_today_start_time()
        today_end_timestamp = get_today_end_time()
        str_last_signin_time = time.strftime("%H:%M:%S", time.localtime(last_signin_time))
        if today_start_timestamp < last_signin_time < today_end_timestamp:
            await app.sendGroupMessage(group, MessageChain.create([
                At(target=qq),
                Plain(f" 你已经在今天的{str_last_signin_time}已经签过到了哦~\n你现在有{exist_pan}个面包哦~")
            ]))
        else:
            exist_data['time'] = signin_time
            exist_data['pan'] += 5
            exist_data['sum_day'] += 1
            update_user_signin_data(qq, r, exist_data)
            await app.sendGroupMessage(group, MessageChain.create([
                At(target=qq),
                Plain(f"\n{str_time_now} 签到成功，摩卡给你5个面包哦~\n累计签到{exist_data['sum_day']}天\n你现在有{exist_data['pan']}个面包啦~")
            ]))


def get_user_signin_data(qq: int, r: R) -> dict:
    """
    获取用户签到数据.

    :param qq: 要进行签到的QQ号
    :param r: Redis数据库对象
    :return: 如存在则返回签到数据，若不存在返回空dict
    """
    if r.hexists(db_name, qq):
        d = r.hget(db_name, qq)
        return json.loads(d)
    else:
        return {}


def update_user_signin_data(qq: int, r: R, data: dict):
    """
    更新用户签到数据.

    :param qq: 要进行签到的QQ号
    :param r: Redis数据库对象
    :param data: 新的dict数据
    :return: None
    """
    r.hset(db_name, qq, json.dumps(data, ensure_ascii=False))
    return None


def get_time_now() -> int:
    """
    获取当前时间戳（秒级）.

    :return: 当前时间戳（秒级）
    """
    return int(time.time())


def get_today_start_time() -> int:
    """
    获取今天00：00的时间戳.

    :return: 今天00：00的时间戳
    """
    return int(time.mktime(time.strptime(str(datetime.date.today()), '%Y-%m-%d')))


def get_today_end_time() -> int:
    """
    获取今天23：59的时间戳.

    :return: 今天23：59的时间戳
    """
    return int(time.mktime(time.strptime(str(datetime.date.today() + datetime.timedelta(days=1)), '%Y-%m-%d'))) - 1


def consume_pan(qq: int, r: R, amount: int) -> [bool, int]:
    """
    消耗面包.

    :param qq: 消耗面包的目标账户
    :param r: Redis数据库对象
    :param amount: 消耗的数量
    :return: 成功返回[True, 剩余数量]；数量不足返回[False, 剩余数量]
    """
    return_data = [False, 0]
    exist_data = get_user_signin_data(qq, r)
    if exist_data == {}:
        return return_data
    else:
        exist_pan = exist_data.get('pan')
        if exist_pan < amount:
            return_data[1] = exist_data['pan']
            return return_data
        else:
            exist_data['pan'] -= amount
            update_user_signin_data(qq, r, exist_data)
            return_data[0] = True
            return_data[1] = exist_data['pan']
            return return_data
