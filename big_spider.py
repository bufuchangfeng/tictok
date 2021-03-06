import json
import time
import api
from sign import Sign
import requests
from config import CONFIG
from queue import Queue
import os

device_info = Sign().getDevice()

node_count = 200

common_params = {
            "iid": device_info['iid'],
            "idfa": device_info['idfa'],
            "vid": device_info['vid'],
            "device_id": device_info['device_id'],
            "openudid": device_info['openudid'],
            "device_type": device_info['device_type'],
            "os_version": device_info['os_version'],
            "os_api": device_info['os_api'],
            "screen_width": device_info['screen_width'],
            "device_platform": device_info['device_platform'],
            "version_code": CONFIG['APPINFO']['version_code'],
            "channel": CONFIG['APPINFO']['channel'],
            "app_name": CONFIG['APPINFO']['app_name'],
            "build_number": CONFIG['APPINFO']['build_number'],
            "app_version": CONFIG['APPINFO']['app_version'],
            "aid": CONFIG['APPINFO']['aid'],
            "ac": "WIFI",
            "pass-region": "1",  # new
            # "js_sdk_version": "1.3.0.1"
}

token = Sign().getToken()


def user_detail(user_id):
    url, extra_params = api.user(user_id=user_id)
    params = dict(common_params, **extra_params)

    # 参数加签（* 要对全部参数加签 *）
    sign = Sign().getSign(token, params)
    params["mas"] = sign['mas']
    params["as"] = sign['as']
    params["ts"] = sign['ts']

    resp = requests.get(url, params=params, headers=CONFIG['HEADER']).json()
    # print(json.dumps(resp))

    data = resp['user']
    out_data = {
        'user_id': data['uid'],
        'nickname': data['nickname'],
        'signature': data['signature'],
        'sex': data['gender'],
        'address': data['country'] + data['city'] + data['district'],
        'constellation': data['constellation'],
        'avatar': data['avatar_larger']['url_list'],
        'url': data['share_info']['share_url'],
        'follower_count': data['follower_count'],  # 粉丝数
        'total_favorited': data['total_favorited'],  # 获赞数
        'following_count': data['following_count'],  # 关注数
        'aweme_count': data['aweme_count'],  # 作品数
        'dongtai_count': data['dongtai_count'],  # 动态数
    }

    return json.dumps(out_data)


# 关注的用户
def user_followings(target_user_id, target_count=100):
    out_data = {
        'user_id': target_user_id,
        'followings': []
    }

    def get_out_data(max_time=int(time.time())):
        url, extra_params = api.following(user_id=target_user_id, count=20, max_time=max_time)
        params = dict(common_params, **extra_params)

        # 参数加签（* 要对全部参数加签 *）
        sign = Sign().getSign(token, params)
        params["mas"] = sign['mas']
        params["as"] = sign['as']
        params["ts"] = sign['ts']

        resp = requests.get(url, params=params, headers=CONFIG['HEADER']).json()
        # print(json.dumps(resp))

        data = resp['followings']
        for item in list(data):
            item_data = {
                'user_id': item['uid'],
                'nickname': item['nickname']
            }
            if item_data not in out_data['followings']:
                out_data['followings'].append(item_data)

            print('%s/%s' % (len(out_data['followings']), resp['total']))

        if resp['has_more'] == False or len(resp['followings']) == 0 or len(
                    out_data['followings']) >= target_count:
            return

        # 默认30s。如果丢失数据可缩小秒数。如果数据重复可增加秒数。
        next_max_time = resp.get('min_time', int(time.time())) - 30
        get_out_data(next_max_time)

    get_out_data()

    return json.dumps(out_data)


# 用户的粉丝
def user_followers(target_user_id, target_count=100):
    out_data = {
        'user_id': target_user_id,
        'followers': []
    }

    def get_out_data(max_time=int(time.time())):
        url, extra_params = api.follower(user_id=target_user_id, count=20, max_time=max_time)
        params = dict(common_params, **extra_params)

        # 参数加签（* 要对全部参数加签 *）
        sign = Sign().getSign(token, params)
        params["mas"] = sign['mas']
        params["as"] = sign['as']
        params["ts"] = sign['ts']

        resp = requests.get(url, params=params, headers=CONFIG['HEADER']).json()
        print(json.dumps(resp))

        print(resp['total'])

        data = resp['followers']
        for item in list(data):
            item_data = {
                'user_id': item['uid'],
                'nickname': item['nickname']
            }
            if item_data not in out_data['followers']:
                out_data['followers'].append(item_data)

            print('%s/%s' % (len(out_data['followers']), resp['total']))

        if resp['has_more'] == False or len(resp['followers']) == 0 or len(
                    out_data['followers']) >= target_count:
            return

        # 默认30s。如果丢失数据可缩小秒数。如果数据重复可增加秒数。
        next_max_time = resp.get('min_time', int(time.time())) - 30
        get_out_data(next_max_time)

    get_out_data()
    return json.dumps(out_data)


def main():

    # q是一个队列，功能类似 图的广度优先遍历 中的队列
    q = Queue()

    # l是一个集合，可以用python中的set实现，但是list有序，所有选用list
    l = []

    nickname_list = []

    # 起始用户的user_id
    start_user = '57720812347'
    start_nickname = '莉哥o3o'

    l.append(start_user)
    q.put(start_user)
    nickname_list.append(start_nickname)

    f_edges = open('20155324-node-list-temp.txt', 'w')
    f_nodes = open('20155324-index-file.txt', 'w')
    f_nickname = open('20155324-nickname-file', 'wb')

    # l的元素数量 是 图中 节点的数量
    while len(l) < node_count and q.empty() is False:
        target_user = q.get()

        # 获取用户关注了谁
        user_info = json.loads(user_detail(target_user))
        following_count = user_info['following_count']

        # 当一个用户关注人数超过100时，只取100
        if following_count > 100:
            following_count = 100

        print('开始爬取 ' + user_info['nickname'] + ' 关注的用户')
        followings = json.loads(user_followings(target_user, following_count))

        mat = "{:30}"

        for following in followings['followings']:

            # 如果被关注的用户不在集合中，则需要检查被关注的用户粉丝数量是否超过100 0000，超过100 0000才能添加进图中，并添加 当前节点 和 被关注的用户 之间的边
            if following['user_id'] not in l:

                print(mat.format('检查 ' + following['nickname'] + ' 粉丝数是否符合要求'), end='')

                user_info = json.loads(user_detail(following['user_id']))

                follower_count = user_info['follower_count']

                # 只有粉丝数大于100 0000 时， 节点才被加入图中
                if follower_count >= 1000000:
                    nickname_list.append(following['nickname'])
                    l.append(following['user_id'])
                    q.put(following['user_id'])
                    print(following['nickname'] + ' 粉丝数是 ' + str(follower_count) + '                       符合要求')

                    # 添加边
                    f_edges.write(target_user + ' ' + following['user_id'] + '\n')
                else:
                    print(following['nickname'] + ' 粉丝数是 ' + str(follower_count) + '                       不符合要求')

            # 如果被关注的用户在集合中，则直接添加 当前节点 和 被关注的用户 之间 的 边 即可
            else:
                f_edges.write(target_user + ' ' + following['user_id'] + '\n')

        print('\n')

    i = 1
    for node in l:
        f_nodes.write('<' + str(i) + ',' + node + '>\n')
        i += 1

    i = 1
    for node in nickname_list:
        f_nickname.write((str(i) + ' ' + node + '\n').encode())
        i += 1

    f_nickname.close()
    f_nodes.close()
    f_edges.close()

    f1 = open('20155324-node-list-temp.txt', 'r')
    f2 = open('20155324-node-list.txt', 'w')

    for line in f1.readlines():
        node1 = line.split(' ')[0]
        node2 = line.split(' ')[1].strip()

        f2.write('<' + str(l.index(node1) + 1) + ',' + str(l.index(node2) + 1) + '>\n')

    f1.close()
    f2.close()

    os.remove('20155324-node-list-temp.txt')


if __name__ == '__main__':
    main()
