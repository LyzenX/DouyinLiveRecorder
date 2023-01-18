# 抖音直播录制
## 特点
- 支持无人值守自动监测和录制多个主播的直播。
- **支持录制弹幕**。
- 支持自动获取 cookie，并在 cookie 失效时自动重新获取。
- 支持不使用 cookie 进行开播监测，以延长 cookie 有效时间，降低使用登录 cookie 而被封号的风险。
- 支持自定义脚本、插件，以自定义开播推送等功能，支持 cookie 失效事件以便提醒更换 cookie。
- 支持 linux。
- 理论上支持 mac，但未测试，如果是 mac 用户可以参考 linux 的安装和使用方法，勤使用搜索引擎。

## 缺点
- 由于是根据作者本人自用的需求而开发的，因此不支持诸如更改清晰度(直接录制最高清晰度)、最大文件长度之类的功能，以后可能会加入这些功能。
- 启动之前需要较多操作，需要一点动手能力和耐心。
- 浏览器模式检测和弹幕录制对系统资源的占用率较高。
- 高级功能如插件、推送等的使用门槛较高，可能要会写 python 代码。
- 因新鲜出炉，尚未测试足够长时间，可能有较多 bug。

## 说明

如果有bug或有什么建议的话请发issues，**建议贴上日志( logs 文件夹下遇到 bug 时对应的日志)**。

软件仅供个人使用，禁止商业使用，禁止不正当使用，不接受定制，不接受捐助。

本人从未也不会从本软件中获利，没有义务保证软件长期有效和及时更新，没有义务对所有遇到的问题都作解答，任何对软件的不正当修改和使用所造成的危害由使用者负责。

目前更新软件的方式是下载最新软件，并把旧软件的 room.json 复制到新目录下，config.txt 可能要重新配置，因为新旧版本配置不兼容。

## 使用方法
下载软件并解压，进入到解压后的目录，你能看到在这个目录下的 运行命令行版.bat 等文件，这个目录称为软件*根目录*。
### Windows平台安装
首先安装 python **并将其添加到环境变量**（可以在安装过程中勾选 *Add Python x.x to PATH*），如果是新手的话可以百度搜索 *Python 安装*，有手把手教程。

Windows平台可以按键盘上的 *Win + R*，并在文本框中输入`cmd`，回车，打开命令提示符，并在命令提示符中输入`python --version`，如果输出了python的版本，则表明安装成功。

如果是 Windows 10/11，执行命令`python`后可能什么都不输出，甚至会出现打开微软应用商店的迷惑行为，可以百度搜索*python弹出微软应用商店*。

如果不使用浏览器模式，不自动获取 cookie (自己填入 cookie )，且不录制弹幕的话，可以不用安装 Chrome 和 chromedriver。

安装 Google Chrome 浏览器(小心别安装了广告的盗版)

软件会自动安装 chromedriver。

### Linux平台(无图形化界面)安装
如果使用 Linux 应该会安装 python吧。

如果不使用浏览器模式以及弹幕录制可以不安装 chorme，下面有配置方法。

``` bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo dpkg -i google-chrome-stable_current_amd64.deb
```
安装完后，执行命令
``` bash
google-chrome --version
```
如果能看到版本号，则说明安装成功。

软件会自动安装 chromedriver，如果安装失败，可以：

记住上面命令得到的版本号，执行以下指令以找到相同版本的 chromedriver，下载并放到软件根目录下，并给它运行权限：
``` bash
wget https://chromedriver.storage.googleapis.com/你安装的google-chrome的版本/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo chmod -x chromedriver
```

### 配置文件
在软件根目录下找到 config.txt，用文本编辑器打开它。里面对各选项都作了说明，可以根据自己的需求调整。

因为可以自动获取 cookie，所以 cookie 的选项不是必须的。

如果需要自定义 cookie 的话，cookie的获取方法：
使用刚刚安装的 Chrome 浏览器(其他带抓包功能的浏览器也行)，打开网页版抖音，按F12，选择 Network(网络)，
在 Filter(过滤器，像一个搜索框)输入*douyin*，刷新网页，选择其中一个(www.douyin.com)，在右边界面中住下滑，找到 cookie，把 `cookie:` 右边的内容复制到 config.txt 的 `cookie = `右方。

可以使用未登录的 cookie，或者为延长有效时间和避免封号的损失用小号的 cookie。

如果是性能较差的服务器，如2核4G的服务器或更低，可以选择将 monitor_using_api 设为 true，关闭录制弹幕功能并减小 check_threads 的数量，关闭自动转码或自动转码编码器使用 *copy*。

linux 服务器可以考虑使用 bypy 来上传录制到的文件，并在自己的 PC 中转码和渲染弹幕。可以使用插件(下面说明)来实现自动上传。

### 设置房间
可以在 GUI 界面中点击下方的 *添加主播* 来添加房间，支持 Web_Sid、直播间地址、直播间短链、(正在直播的)主播主页。

使用纯命令行的用户，可以：

在软件根目录下找到 room.json，用文本编辑器打开它，下面是几个例子：
``` text
[
  {
    "id": 71034333127,
    "name": "主播名1",
    "auto_record": true,
    "record_danmu": true
  },
  {
    "id": 851917085931,
    "name": "主播名2",
    "auto_record": true,
    "record_danmu": true
  }
]
```
id 是房间的 Web_Rid，即用网页版打开直播间(也可以自己在网页输入直播分享的短链，会跳转另一链接)，链接为 live.xxx.com/123456789?roomid=...

这个 123456789 就是 Web_Rid 。

name 可以填主播名，同时也是录制到的文件所存放的目录名，由于一些主播会经常改名，所以不自动获取名称，你可以自己填一个容易记的名字。

auto_record 是否自动监测和录制，一般是 true，如果不想录了又怕删掉它下次不方便加回来，可以改成 false。

record_danmu 为是否录制弹幕，对性能要求较高，根据实际需求和录制设备性能决定。

### 运行
双击 main.pyw 即可运行 GUI 版。

运行命令行版，Windows 平台直接打开 运行命令行版.bat 就可以了，也能使用 Linux 的，在软件根目录下执行指令 `python main.pyw`。

对于命令行版，当配置或房间修改时，需要重新启动软件才能生效。

下载的文件存放于 *根目录/download* 下。

### 自动转码
需要下载 ffmpeg，可以放在软件根目录下或其他位置，在 config.txt 中配置 ffmpeg 所在目录，并配置自动转码选项。

### 插件
在 src/plugin/plugin.py 中编写你的插件，比如当直播开始时向一个 api POST 一个信息以便通知你开播了：
``` python
def on_live_start(room):
    post(f'123.45.67.89:65565/?room_name={room.room_name}')
```

### 对录制到的文件进行处理
下载到的文件是flv格式，由于时间戳错误等，许多软件播放有异常，可以使用 PotPlayer 播放，但仍存在拖拽进度条卡顿等问题，你可以尝试转码：

下载 ffmpeg 并将其添加到环境变量中(网上有教程)，假设录到的文件名是 *20230114_123456.flv*，执行指令：
``` bash
ffmpeg -i 20230114_123456.flv -c copy 20230114_123456.mp4
```
可以进行无损转码，且速度非常快，还能修复部分由于时间戳错误造成的问题。
如果不嫌转码麻烦费时的话，可以只保留 flv 格式，要用的时候才转为 mp4 格式，以免日后发现转码后的视频有问题时，原flv文件已经删了。

下载的弹幕是类 b站xml 格式的，可以使用 [nicovert](https://github.com/muzuiget/niconvert) 来转为 ass 格式字幕文件，播放时拖入 PotPlayer 就能显示弹幕了。

如果要将弹幕渲染到视频中，可以使用命令：
``` bash
ffmpeg -i 20230114_123456.flv -vf ass=20230114_123456.ass 有弹幕.mp4
```

但是这样如果原视频模糊或帧数低的话，弹幕也会模糊或一卡一卡的，你可以先生成一个高质量中间文件，再渲染弹幕：
``` bash
ffmpeg -i 20230114_123456.flv -c:v h264 -b:v 5824k -vf scale=iw*2:ih*2 -c:a copy -r 60 hq.mp4
ffmpeg -i hq.mp4 -c:v h264 -b:v 5824k -vf ass=20230114_123456.ass -c:a copy 有弹幕.mp4
```
