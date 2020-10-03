import redis
import json
rc = redis.Redis(db=1, decode_responses=True)
r = redis.Redis(db=0, decode_responses=True)
groups = rc.smembers("GROUPS")
groups.add('key_template')

new_dict = {"赤尾ひかる": [
    "来点赤尾ひかる",
    "来点赤尾光"
]}

if __name__ == "__main__":
    for g_id in groups:
        print(f"updating {g_id}")
        group_keyword = json.loads(r.hget("KEYWORDS", g_id))
        group_keyword.update(new_dict)
        r.hset("KEYWORDS", g_id, json.dumps(group_keyword, ensure_ascii=False))
