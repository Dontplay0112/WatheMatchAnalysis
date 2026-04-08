# 海豹骰列车杀手对局分析插件及python后端


## 介绍

一个用于分析MC列车杀手对局的项目，包含：
* 一个js插件，加载进海豹骰后从python后端获取分析数据
* 一个python后端，提供了若干接口，实现接收游戏数据并分析，同时接受js插件的请求并返回分析结果


## 如何使用

### JS插件

1. clone或下载项目

2. 修改`src\utils.ts`中的`API_BASE_URL`为你的python后端地址(直接运行python后端，一般不需要修改)

3. 安装依赖并编译js插件(需要Node.js环境)：
``` bash
npm install
npm run build
```

将`dist`目录下的js文件加载进海豹骰

### python后端

``` bash
cd server
uv init
uv sync
uv run run.py
```
或者其他任意配置python环境的方式都可以。

### 游戏

除此以外还需要在游戏中安装[RecordWathe](https://github.com/Dontplay0112/RecordWathe)模组，并修改配置文件`config/recordwathe.json`用于自动上传对局记录:
``` json
{
  "backendUrl": "http://YOUR_PYTHON_BACKEND_IP:8897/api/upload_match"
}
```