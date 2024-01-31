## 雅图伴侣本地UDP通讯格式

### UDP传输方式

发送时采用UNICAST，只要把符合格式的JSON指令串（最大长度180字符）用雅图伴侣设备密码加码处理后发送给对应符合MDNS命名规则的雅图伴侣设备本地名称（例如eq2613000006.local）即可。

接收的话，需要用MULTICAST从地址"224.0.1.3",端口4211接收数据并进行解码（加码的逆过程），然后分析获取数据即可。

### UDP数据格式

本地UDP通讯数据包采用JSON格式，可以有以下内容例如
```
{
    "dev":"aircube_123456",   # 发送信息的设备名称
    "tar":"eq2613000006",
    "flt":0,                # 故障状态 0-无故障、126-通讯故障、127-校验故障、128-超时[只读]
    "fst":1,                # 火焰状态 0-未点火、1-点火[只读]
    "mod":100,              # 当前燃气比例阀开度 0-100%[只读]
    "cct":80,               # 当前采暖水温度[只读]
    "cdt":72,               # 当前生活热水温度[只读]
    "ccm":1,                # 当前采暖状态 0-未开启、1-开启[只读]
    "cdm":0,                # 当前生活热水状态 0-未开启、1-开启[只读]
    "tct":80,               # 目标采暖水温度 [操作指令]
    "tdt":42,               # 目标生活热水温度 [操作指令]
    "tcm":1,                # 目标采暖水模式 0-未开启、1-开启 [操作指令]
    "tdm":1,                # 目标生活热水模式 0-未开启、1-开启 [操作指令]
    "atm":1,                # 自动室温调节模式 0-未开启、1-开启 [操作指令]
    "odt":11,               # 当前室外温度[只读]
    "coe":4,                # 当前采用的室外温度补偿系数 [操作指令]
    "crt":19.2,             # 当前室温[只读]
    "trt":20,               # 目标室温 [操作指令]
    "pwr":4.31,             # 当前电量[只读]
    "sch":1,                # 自动任务状态 0-未开启、1-开启 [操作指令]
    "vir":1,                 # 系统炉打开了屏蔽高温杀菌模式
    "tdf":10                # 系统炉生活水温差设为10度
    "sta":1                 # 请求马上回应当前运行状态
}
```
凡是标记为[只读]的，只能用于读取数据，其它则可以读取，也可以设置。

在本项目中，我们只简单的发送tdt指令，用于设置生活热水温度。
在项目例子中，我们可以看到，发送的JSON需要包括本机的名称dev,目标设备的名称tar,以及请求请求状态指令sta，例如
```
{
    "dev":"aircube_123456",
    "tar":"eq2613000006",
    "tdt":43,
    "sta":1
}
```

### 在 macOS Sonoma下注意的事项

在 macOS Sonoma下，CircuitPython的固件加载成USB盘时默认会导致写入出错，每次插入硬件识别后，需要在终端中执行以下命令，才能正常运行
```
utils/remount.sh DEVICE_NAME
```
