import psycopg2
url = "postgresql://postgres:FwrphodHyDPasOzdLTMZfovHtzzruDoM@turntable.proxy.rlwy.net:30612/railway"
try:
    conn = psycopg2.connect(url, sslmode="require")
    print("连接成功")
    conn.close()
except Exception as e:
    print(f"连接失败: {e}")
