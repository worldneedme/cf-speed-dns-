import requests
import traceback
import time
import os
import json

# API 密钥
CF_API_TOKEN    =   os.environ["CF_API_TOKEN"]
CF_ZONE_ID      =   os.environ["CF_ZONE_ID"]
CF_DNS_NAME     =   os.environ["CF_DNS_NAME"]

# pushplus_token
PUSHPLUS_TOKEN  =   os.environ.get("PUSHPLUS_TOKEN", "")



headers = {
    'Authorization': f'Bearer {CF_API_TOKEN}',
    'Content-Type': 'application/json'
}

def get_cf_speed_test_ip(timeout=10, max_retries=5):
    for attempt in range(max_retries):
        try:
            # 发送 GET 请求，设置超时
            response = requests.get('https://ip.164746.xyz/ipTop.html', timeout=timeout)
            # 检查响应状态码
            if response.status_code == 200:
                return response.text
        except Exception as e:
            traceback.print_exc()
            print(f"get_cf_speed_test_ip Request failed (attempt {attempt + 1}/{max_retries}): {e}")
    # 如果所有尝试都失败，返回 None 或者抛出异常，根据需要进行处理
    return None

# 获取 DNS 记录
def get_dns_records(name):
    def_info = []
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records'
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        records = response.json()['result']
        for record in records:
            if record['name'] == name:
                def_info.append(record['id'])
        return def_info
    else:
        print('Error fetching DNS records:', response.text)
        return []

# 更新 DNS 记录
def update_dns_record(record_id, name, cf_ip):
    url = f'https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/dns_records/{record_id}'
    data = {
        'type': 'A',
        'name': name,
        'content': cf_ip
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 200:
        print(f"cf_dns_change success: ---- Time: " + str(
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + " ---- ip：" + str(cf_ip))
        return "ip:" + str(cf_ip) + "解析" + str(name) + "成功"
    else:
        traceback.print_exc()
        print(f"cf_dns_change ERROR: ---- Time: " + str(
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())) + " ---- MESSAGE: " + str(response))
        return "ip:" + str(cf_ip) + "解析" + str(name) + "失败"

# 消息推送
def push_plus(content):
    if not PUSHPLUS_TOKEN:
        print("PUSHPLUS_TOKEN is empty, skip push notification.")
        return

    url = 'http://www.pushplus.plus/send'
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": "IP优选DNSCF推送",
        "content": content,
        "template": "markdown",
        "channel": "wechat"
    }
    body = json.dumps(data).encode(encoding='utf-8')
    headers = {'Content-Type': 'application/json'}
    requests.post(url, data=body, headers=headers)

# 主函数
def main():
    # 获取最新优选IP
    ip_addresses_str = get_cf_speed_test_ip()
    if not ip_addresses_str:
        print("No speed test IPs fetched, stop DNS update.")
        return

    ip_addresses = [ip.strip() for ip in ip_addresses_str.split(',') if ip.strip()]
    if not ip_addresses:
        print("Speed test IP list is empty, stop DNS update.")
        return

    dns_records = get_dns_records(CF_DNS_NAME)
    if not dns_records:
        print(f"No DNS records found for {CF_DNS_NAME}, stop DNS update.")
        return

    push_plus_content = []
    update_count = min(len(ip_addresses), len(dns_records))
    if len(ip_addresses) != len(dns_records):
        print(
            f"IP count ({len(ip_addresses)}) and DNS record count ({len(dns_records)}) "
            f"do not match, only update first {update_count} records."
        )

    # 遍历 IP 地址列表
    for index, ip_address in enumerate(ip_addresses[:update_count]):
        # 执行 DNS 变更
        dns = update_dns_record(dns_records[index], CF_DNS_NAME, ip_address)
        push_plus_content.append(dns)

    push_plus('\n'.join(push_plus_content))

if __name__ == '__main__':
    main()
