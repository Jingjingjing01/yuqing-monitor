import os
os.environ["DATABASE_URL"] = "postgresql://postgres:FwrphodHyDPasOzdLTMZfovHtzzruDoM@turntable.proxy.rlwy.net:30612/railway"
os.environ["API_KEY"] = "sk-zk2e80f04fd38719ff262bbc3f323c3f92d6995d2ab9b3c1"
os.environ["API_BASE_URL"] = "https://api.zhizengzeng.com/v1"

from db import init_db
init_db()
print("init_db 成功")

from app import app
print("app 导入成功")
