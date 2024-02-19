import ure
import json
import socket
import time
import network

# 热点配置
ap_ssid = "WiFi Config"
ap_passwd = "12345678"
ap_authmode = 3

# 无线配置存储位置
NETWORK_PROFILES = 'net.data'

# 网络接口配置
wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)

server_socket = None

# HTTP 状态码
http_status = {
    200: "OK",
    400: "Bad Request",
    402: "Payment Required",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    500: "Internal Server Error"
}

def ResetNetwork():
    print("Reseting AP_IF...")
    wlan_ap.active(False)
    wlan_ap.active(True)
    print("Reseting STA_IF...")
    wlan_sta.active(False)
    wlan_sta.active(True)

# WiFi扫描
def scan():
    sta_if = network.WLAN(network.STA_IF);
    sta_if.active(True)
    ap = sta_if.scan()
    lists = []
    for i in ap:
        if i[5] == 1:
            continue
        lists.append({
            "ssid": i[0].decode(),
            "rssi": i[3],
            "authmode": i[4],
        })
    return {
        "length": len(lists),
        "data": lists
    }

def get_ipaddr():
    sta_if = network.WLAN(network.STA_IF);
    return sta_if.ifconfig()

# 读取无线配置
def read_profiles():
    with open(NETWORK_PROFILES) as f:
        lines = f.readlines()
    profiles = {}
    for line in lines:
        ssid, password = line.strip("\n").split(";")
        profiles[ssid] = password
    return profiles

# 写入无线配置
def write_profiles(profiles):
    lines = []
    for ssid, password in profiles.items():
        lines.append("%s;%s\n" % (ssid, password))
    with open(NETWORK_PROFILES, "w") as f:
        f.write(''.join(lines))

# 无线连接
def connect_to_wifi(ssid, password):
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        return None
    print('Trying to connect to %s...' % ssid)
    print(password)
    wlan_sta.connect(ssid, password)
    for retry in range(200):
        connected = wlan_sta.isconnected()
        if connected:
            break
        time.sleep(0.1)
        print('.', end='')
    if connected:
        print('\nConnected. Network config: ', wlan_sta.ifconfig())
    else:
        print('\nFailed. Not Connected to: ' + ssid)
    return connected

# 处理响应头
def parse_request_headers(header_lines):
    headers = {}
    for line in header_lines:
        # 分割每行的键值对
        key, value = line.split(": ", 1)
        headers[key] = value.strip()
    return headers

def stop():
    global server_socket
    if server_socket != None:
        server_socket.close()
        server_socket = None

# 启动服务器
def start_http_server(host = "0.0.0.0", port = 80):
    global server_socket

    stop()

    # 创建AP
    wlan_ap.config(essid=ap_ssid, password=ap_passwd, authmode=ap_authmode)


    # 创建Socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    
    # 启用监听
    server_socket.listen(1)
    print(f"Server listening on port {port}...")
    print('Connect to WiFi ssid ' + ap_ssid + ', default password: ' + ap_passwd)
    print('and access the ESP via your favorite web browser at 192.168.4.1.')
    print('Listening on:', port)

    # 业务循环
    while True:
        if server_socket == None:
            return False
        # 如果已连接则退出循环
        if wlan_sta.isconnected():
            wlan_ap.active(False)
            return True
        # 接受来自客户端的连接
        client_socket, client_addr = server_socket.accept()
        print(f"Accepted connection from {client_addr}")
        try:
            # 设置连接超时
            client_socket.settimeout(5.0)
            # 分块接收
            request = b""
            try:
                while "\r\n\r\n" not in request:
                    request += client_socket.recv(512)
            except OSError:
                pass

            print("Request is: {}".format(request))
            if "HTTP" not in request:  # skip invalid requests
                continue
        
            # 获取访问信息
            req_type, req_path, http_ver = request.decode().split("\r\n")[0].split(" ")
            print(f"accept url request: {req_path}")
            handle_response(client_socket, req_path, request.decode())
        finally:
            # 关闭连接
            client_socket.close()

# 读取文件并发送
# TODO: 分块发送
def read_from_file(filepath: str):
    with open(filepath, "r") as fp:
        htmlstr = fp.read()
        fp.close()
    return htmlstr

def handle_response(client: socket.socket, req_path: str, request: str = ""):
    if req_path == "" or req_path == "/":
        # handle root
        handle_root(client)
        pass
    elif req_path == "/scan":
        # handle wifi scan
        handle_wifi_scan(client)
        pass
    elif req_path == "/connect":
        # handle connect
        handle_connect(client, request)
        pass
    else:
        # handle 404
        handle_404(client)
        pass

def send_Header(client: socket.socket, headers: dict = {}, responseCode: int = 200):
    # 构造状态行
    responseText = f"HTTP/1.1 {responseCode} {http_status[responseCode]}\r\n"
    # 构造响应头
    for k, v in headers.items():
        responseText += f"{k}: {v}\r\n"
    del headers
    # 构造空行
    responseText += "\r\n"
    client.sendall(responseText)
    return True

def send_text(client: socket.socket, text: str):
    try:
        client.sendall(text)
        return True
    except OSError as e:
        print("error: ", e)
        return False

def send_File(client: socket.socket, file_path: str):
    try:
        with open(file_path, "r") as fp:
            #while True:
            #    chunk = fp.read(1024).encode()
            #    if not chunk:
            #        break
            #    client.send(chunk)
            text = fp.read()
            client.sendall(text)
            fp.close()
        return True
    except OSError as e:
        print("Error: ", e)

# 业务处理
def handle_root(client: socket.socket):
    send_Header(client, {"Content-Type": "text/html"}, 200)
    send_File(client, "static/index.html")

def handle_wifi_scan(client: socket.socket):
    wlan_sta.active(True)
    send_Header(client, {"Content-Type": "application/json"}, 200)
    send_text(client, json.dumps(scan()))

def handle_connect(client: socket.socket, request):
    # 识别连接信息
    match = ure.search("ssid=([^&]*)&pwd=(.*)", request)

    if match is None:
        send_Header(client, {"Content-Type": "application/json"}, 400)
        send_text(client, json.dumps({"status": -2, "text": "Parameter not found"}))
        return False

    try:
        ssid = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!").replace("%20", " ")
        password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!")
    except Exception:
        ssid = match.group(1).replace("%3F", "?").replace("%21", "!").replace("%20", " ")
        password = match.group(2).replace("%3F", "?").replace("%21", "!")

    if len(ssid) == 0:
        send_Header(client, {"Content-Type": "application/json"}, 400)
        send_text(client, json.dumps({"status": -1, "text": "SSID must be provide"}))
        return False

    if connect_to_wifi(ssid, password):
        send_Header(client, {"Content-Type": "application/json"}, 200)
        send_text(client, json.dumps({"status": 0, "text": "success", "ssid": ssid, "ip_addr": get_ipaddr()[0]}))
        client.close()
        time.sleep(5)
        wlan_ap.active(False)
        try:
            profiles = read_profiles()
        except OSError:
            profiles = {}
        profiles[ssid] = password
        write_profiles(profiles)
        time.sleep(3)

        return True
    else:
        send_Header(client, {"Content-Type": "application/json"}, 200)
        send_text(client, json.dumps({"status": 1, "text": "Could not connect to WiFi network"}))
        return False

def handle_404(client: socket.socket):
    send_Header(client, {"Content-Type": "text/html"}, 404)
    response_body = "<html><head><title>Not Found</title></head><body><div><h1>404</h1><br /><h2>Not Found</h2></div></body></html>"
    send_text(client, response_body)
    
def get_connection():
    """return a working WLAN(STA_IF) instance or None"""

    # First check if there already is any connection:
    if wlan_sta.isconnected():
        print("Already connected")
        return wlan_sta
    
    # Reset the IF
    ResetNetwork()

    connected = False
    try:
        # ESP connecting to WiFi takes time, wait a bit and try again:
        time.sleep(3)
        if wlan_sta.isconnected():
            return wlan_sta

        # Read known network profiles from file
        profiles = read_profiles()

        # Search WiFis in range
        wlan_sta.active(True)
        networks = wlan_sta.scan()

        AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
        for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
            ssid = ssid.decode('utf-8')
            encrypted = authmode > 0
            print("ssid: %s chan: %d rssi: %d authmode: %s" % (ssid, channel, rssi, AUTHMODE.get(authmode, '?')))
            if encrypted:
                if ssid in profiles:
                    password = profiles[ssid]
                    connected = connect_to_wifi(ssid, password)
                else:
                    print("skipping unknown encrypted network")
            else:  # open
                connected = connect_to_wifi(ssid, None)
            if connected:
                break
            
    except OSError as e:
        print("exception", str(e))

    # start web server for connection manager:
    if not connected:
        connected = start_http_server("0.0.0.0", 80)

    return wlan_sta if connected else None
