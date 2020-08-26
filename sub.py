"""
author: Les1ie
mail: me@les1ie.com
license: CC BY-NC-SA 3.0
"""

import pytz
import requests
from time import sleep
from random import randint
from datetime import datetime

user = "USERNAME"  # sep账号
passwd = "PASSWORD"  # sep密码
api_key = "API_KEY"  # server酱的api，填了可以微信通知打卡结果，不填没影响

# 开启debug将会输出打卡填报的数据，关闭debug只会输出打卡成功或者失败，如果使用github actions，请务必设置该选项为False
debug = False


def login(s: requests.Session, username, password):
    # r = s.get(
    #     "https://app.ucas.ac.cn/uc/wap/login?redirect=https%3A%2F%2Fapp.ucas.ac.cn%2Fsite%2FapplicationSquare%2Findex%3Fsid%3D2")
    # print(r.text)
    payload = {
        "username": username,
        "password": password
    }
    r = s.post("https://app.ucas.ac.cn/uc/wap/login/check", data=payload)

    # print(r.text)
    if r.json().get('m') != "操作成功":
        print(r.text)
        print("登录失败")
        exit(1)
    else:
        print("登录成功")


def get_daily(s: requests.Session):
    daily = s.get("https://app.ucas.ac.cn/ncov/api/default/daily?xgh=0&app_id=ucas")
    # info = s.get("https://app.ucas.ac.cn/ncov/api/default/index?xgh=0&app_id=ucas")
    j = daily.json()
    d = j.get('d', None)
    if d:
        return daily.json()['d']
    else:
        print("获取昨日信息失败")
        exit(1)


def submit(s: requests.Session, old: dict):
    new_daily = old
    new_daily['old_sfzx'] = old['sfzx']
    new_daily['ismoved'] = 0  # 如果前一天位置变化这个值会为1，第二天仍然获取到昨天的1，而事实上位置是没变化的，所以置0
    new_daily['sftjwh'] = old['sfsfbh']
    new_daily['old_szdd'] = old['szdd']
    new_daily['geo_api_info'] = old['old_city']  # 保持昨天的结果
    new_daily['date'] = datetime.now(tz=pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d")
    new_daily['app_id'] = 'ucas'

    r = s.post("https://app.ucas.ac.cn/ncov/api/default/save", data=new_daily)

    if debug:
        from urllib.parse import parse_qs, unquote
        import json
        print("昨日信息:", json.dumps(old, ensure_ascii=False, indent=2))
        print("提交信息:",
              json.dumps(parse_qs(unquote(r.request.body), keep_blank_values=True), indent=2, ensure_ascii=False))

    result = r.json()
    if result.get('m') == "操作成功":
        print("打卡成功")
    else:
        print("打卡失败，错误信息: ", r.json().get("m"))

    message(api_key, result.get('m'), new_daily)


def message(key, title, body):
    """
    微信通知打卡结果
    """
    # 错误的key也可以发送消息，无需处理 :)
    msg_url = "https://sc.ftqq.com/{}.send?text={}&desp={}".format(key, title, body)
    requests.get(msg_url)


def report(username, password):
    s = requests.Session()
    header = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10;  AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/66.0.3359.126 MQQBrowser/6.2 TBS/045136 Mobile Safari/537.36 wxwork/3.0.16 MicroMessenger/7.0.1 NetType/WIFI Language/zh"
    }
    s.headers.update(header)

    print(datetime.now(tz=pytz.timezone("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S %Z"))
    for i in range(randint(10, 600), 0, -1):
        print("\r等待{}秒后填报".format(i), end='')
        sleep(1)

    login(s, username, password)
    yesterday = get_daily(s)
    submit(s, yesterday)


if __name__ == "__main__":
    report(username=user, password=passwd)
