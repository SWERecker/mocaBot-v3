import datetime
import os
import random

import redis
import json
import time
from graia.application import GraiaMiraiApplication, MessageChain
from graia.application.message.elements.internal import Plain, At
from graia.application.group import Group

db_name = "SIGNIN"
R = redis.Redis
buy_pan_interval = 3600
SIGNIN_PAN = 5

BUY_PAN_MIN = 1
BUY_PAN_MAX = 10

EAT_PAN_AMOUNT = 1

# PAN_MACRO_DEFINITION
PAN_TYPE_CONSUME = [1, 3]  # Types that consume pan
PAN_SIGNIN_ADD = 0
PAN_TWICE_LP_CONSUME = 1
PAN_BUY = 2
PAN_EAT = 3

PAN_USAGE_STR = [
    "签到，收入",
    "2xlp，消耗",
    "购买面包，收入",
    "食用面包，消耗"
]
pan_log_file = os.path.join('log', 'pan_bill.txt')


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
    exist_pan = 0
    if exist_data.get('time') == 0:
        exist_pan = exist_data.get('pan')
    if exist_data == {}:
        # 初次签到
        new_pan = exist_pan + SIGNIN_PAN
        signin_data = {"time": signin_time, "pan": new_pan, "sum_day": 1}
        update_user_signin_data(qq, r, signin_data)

        await app.sendGroupMessage(group, MessageChain.create([
            At(target=qq),
            Plain(f"\n{str_time_now} \n初次签到成功！~\n摩卡给你{SIGNIN_PAN}个面包哦~\n你现在有{new_pan}个面包啦~")
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
            exist_data['pan'] += SIGNIN_PAN
            exist_data['sum_day'] += 1
            update_user_signin_data(qq, r, exist_data)
            pan_usage_log(qq, SIGNIN_PAN, exist_data['pan'], PAN_SIGNIN_ADD)
            await app.sendGroupMessage(group, MessageChain.create([
                At(target=qq),
                Plain(f"\n{str_time_now} 签到成功，摩卡给你{SIGNIN_PAN}个面包哦~\n累计签到{exist_data['sum_day']}天\n你现在有{exist_data['pan']}个面包啦~")
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


def consume_pan(qq: int, r: R, amount: int, use_type: int) -> [bool, int]:
    """
    消耗面包.

    :param qq: 消耗面包的目标账户
    :param r: Redis数据库对象
    :param amount: 消耗的数量
    :param use_type: 消耗类型
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
            pan_usage_log(qq, amount, exist_data['pan'], use_type)
            return_data[0] = True
            return_data[1] = exist_data['pan']
            return return_data


def init_user_data(qq: int, r: R) -> dict:
    """

    :param qq: 初始化的qq号
    :param r: Redis数据库对象
    :return: 初始化的数据
    """
    signin_data = {"time": 0, "pan": 0, "sum_day": 0, "last_buy_time": 0}
    update_user_signin_data(qq, r, signin_data)
    return signin_data


def buy_pan(qq: int, r: R) -> [bool, int, int, int]:
    """
    购买面包.

    :param qq: 购买面包的qq号
    :param r: Redis数据库对象
    :return: 购买成功，返回[True, 购买时间, 购买数量, 现有数量], 购买失败，返回 [False, 上次购买时间, 0, 0]
    """
    exist_data = get_user_signin_data(qq, r)
    if not bool(exist_data):
        exist_data = init_user_data(qq, r)
    if exist_data.get('last_buy_time'):
        time_now = get_time_now()
        last_buy_time = exist_data.get('last_buy_time')
        if time_now - last_buy_time < buy_pan_interval:
            return [False, last_buy_time, 0, 0]

    amount = random.randint(BUY_PAN_MIN, BUY_PAN_MAX)
    buy_time = get_time_now()
    exist_data['pan'] += amount
    exist_data['last_buy_time'] = buy_time
    update_user_signin_data(qq, r, exist_data)
    pan_usage_log(qq, amount, exist_data['pan'], PAN_BUY)
    return [True, buy_time, amount, exist_data.get('pan')]


def get_pan_amount(qq: int, r: R) -> int:
    """
    购买面包.

    :param qq: 购买面包的qq号
    :param r: Redis数据库对象
    :return: 面包数量
    """
    exist_data = get_user_signin_data(qq, r)
    if not bool(exist_data):
        return 0
    return exist_data.get('pan')


def eat_pan(qq: int, r: R) -> [bool, int]:
    """
    恰面包.

    :param qq: 吃面包的qq号
    :param r: Redis数据库对象
    :return: [成功/失败, 面包剩余数量]
    """
    exist_data = get_user_signin_data(qq, r)
    if not bool(exist_data):
        return [False, 0]
    if exist_data.get('pan') == 0:
        return [False, 0]
    exist_data['pan'] -= EAT_PAN_AMOUNT
    update_user_signin_data(qq, r, exist_data)
    pan_usage_log(qq, EAT_PAN_AMOUNT, exist_data['pan'], PAN_EAT)
    return [True, exist_data['pan']]


def pan_usage_log(qq: int, amount: int, account_amount: int, use_type: int):
    """
    面包记录.

    :param qq: 用户QQ
    :param amount: 消耗的面包数量
    :param use_type: 使用类型
    :param account_amount: 账户余额
    :return: None
    """
    log_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(get_time_now()))
    if use_type in PAN_TYPE_CONSUME:
        delta_str = f"-{amount}"
    else:
        delta_str = f"+{amount}"
    to_write_data = f"[{log_time}] [{qq}] 用户通过 {PAN_USAGE_STR[use_type]} 面包{delta_str} 账户剩余{account_amount}个面包"
    with open(pan_log_file, 'a', encoding='utf-8')as log_file:
        log_file.write(to_write_data)
        log_file.write('\n')
