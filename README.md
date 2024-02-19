# WiFi连接器

## 介绍

快速配网，一步搞定！
本项目修改自：<https://github.com/tayfunulu/WiFiManager>
继续使用MIT协议开源。

## 使用

1. 将整个项目下载下来
2. 将`/static`文件夹和`wifi_connector.py`上传到设备内，建议使用Thonny编辑器，或者手动CV也行（随你
3. 在`boot.py`（启动时）或者`main.py`（主程序）抑或是任何部分程序代码内部加入下列代码

```python
import wifi_connector

if wifi_connector.get_connection() is None:
    print("Cloud not initialize the network connection.")    # 由你决定！
```

>默认IP：192.168.4.1（以ESP8266为例，其他的可能略有不同）<br />
>无线默认名称：WiFi Config <br />
>无线默认密码：12345678 <br />
>Tip：可以通过连接后查看网关地址获得连接地址

> 注意：不支持隐藏的SSID，隐藏的地址已经被过滤掉了

## 原理

本质就是创建一个最小的HTTP服务器，通过启动AP模式，然后将连接网络页面前端发送给客户端，通过表单方式将相关数据提交进行处理，服务器通过JSON格式与前端交互。
具体信息之后补充

## 客制化

上面说过了，其实页面是通过表单提交的方式将数据提交到设备，那么只要遵守一定规范，就可以自由设计和修改连接页面了！

### WiFi扫描

- 作用：扫描附近的无线接入点
- 访问路由：`/scan`
- 访问格式：无
- 访问内容：无
- 返回格式：json
- 返回内容:

```json
{
    "data": [
        {
            "authmode": 4,
            "rssi": -80,
            "ssid": "Test AP"
        },
        ...
    ],
    "length": 10
}
```

authmode为无线接入点的认证方式
rssi为信号强度，单位为dBm
ssid为无线接入点名称

> AuthMode对照表：
> 
> - 0: 开放
> - 1: WEP
> - 2: WPA-PSK
> - 3: WPA2-PSK
> - 4: WPA/WPA2-PSK

### 提交连接

- 作用：扫描附近的无线接入点
- 访问路由：`/scan`
- 访问格式：POST表单
- 访问内容：ssid=ssid&pwd=password
- 返回格式：json
- 返回内容: 

成功：

```json
{
    "text": "success",
    "status": 0,
    "ssid": "Test AP",
    "ip_addr": "10.0.0.1"
}
```

失败：

```json
{
    "text": "Could not connect to WiFi network",
    "status": 1
}
```