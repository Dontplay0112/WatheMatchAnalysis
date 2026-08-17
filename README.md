# WatheMatchAnalysis

用于分析 Minecraft「列车杀手」对局的 SealDice 插件与 FastAPI 后端。

数据流程：RecordWathe 模组上传对局 JSON → Python 后端存档并写入 SQLite → SealDice 通过 `.wathe` 查询统计。

## SealDice 插件

1. 根据需要修改 `src/utils.ts` 中的 `API_BASE_URL`。
2. 安装依赖并检查、构建：

```bash
npm install
npm run typecheck
npm run build
```

将 `dist/wathe.js` 加载到 SealDice。

## Python 后端

```bash
cd server
uv sync
uv run run.py
```

## RecordWathe 模组

在 `config/recordwathe.json` 中填写后端地址：

```json
{
  "backendUrl": "http://YOUR_PYTHON_BACKEND_IP:8897/api/upload_match"
}
```

## 玩家黑名单

编辑 `server/data/blacklist.txt`，每行填写一个 Minecraft 玩家名。空行与 `#` 注释会被忽略，匹配不区分大小写，保存后无需重启。

黑名单只影响查询展示，不会删除历史 JSON 或 SQLite 数据。直接查询被屏蔽玩家时，返回结果与玩家不存在相同。

后端详细配置、接口与测试方式见 [`server/README.md`](server/README.md)。
