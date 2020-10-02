import json
import config
import time
import os
import redis

file_path = '/www/wwwroot/resource/'
new_data = {'updateTime': str(time.strftime('%Y-%m-%d %H:%M',time.localtime(time.time())))}

names_list = os.listdir(config.pic_path)
file_count_list = []
for name in names_list:
    if os.path.isdir(os.path.join(config.pic_path, name)):
        files_list = os.listdir(os.path.join(config.pic_path, name))
        files_count = len(files_list)
        file_count_list.append(files_count)
new_data['peopleCount'] = len(names_list) - 6
new_data['picCount'] = sum(file_count_list)

r = redis.Redis(db=0, decode_responses=True)
count = 0
g_count = {}
data = r.hgetall("COUNT")
for d in data:
    dict_data = json.loads(data[d])
    g_count[str(d)] = 0
    for n in dict_data:
        g_count[str(d)] += dict_data[n]
        count += dict_data[n]

new_data['rCount'] = count

dh = os.path.join(file_path, "data_history.json")
with open(os.path.join(file_path, 'data.json'), 'w', encoding='utf-8')as data_file:
    data_file.write(json.dumps(new_data, ensure_ascii=False))
if not os.path.isfile(dh):
    history = {"history": [new_data]}
    with open(dh, 'w', encoding='utf-8')as data_file:
        data_file.write(json.dumps(history, ensure_ascii=False))
else:
    with open(dh, 'r', encoding='utf-8')as data_file:
        arc = json.load(data_file)
    arc['history'].append(new_data)
    with open(dh, 'w', encoding='utf-8')as data_file:
        data_file.write(json.dumps(arc, ensure_ascii=False))
