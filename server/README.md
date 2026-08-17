# Wathe FastAPI 后端

## 运行

需要 Python 3.12+ 和 uv。

```bash
uv sync
uv run run.py
```

服务默认监听 `0.0.0.0:8897`。数据路径基于本文件所在的 `server` 目录计算，因此从其他工作目录启动也不会把数据写错位置。

## 黑名单

编辑 `data/blacklist.txt`：

```text
# 注释
PlayerOne
PlayerTwo
```

规则：

- 每行一个玩家名，匹配不区分大小写。
- 空行和以 `#` 开头的行会被忽略。
- 每次查询都会重新读取文件，无需重启。
- 玩家会从个人查询、已启用榜单和击杀/被杀对象列表中隐藏；直接查询时与玩家不存在使用相同回复。
- 只屏蔽展示，原始对局和数据库记录保留。

## 数据文件

- `data/matches/*.json`：原始对局备份。
- `data/data.db`：SQLite 统计数据库。
- `data/translations.json`：阵营、职业和死因翻译。
- `data/blacklist.txt`：查询黑名单。

备份文件默认使用对局开始时间命名；没有 `startMs` 时使用 `matchId`。

## 查询网关

SealDice 向 `POST /api` 发送：

```json
{
  "action": "stats",
  "player_name": "PlayerOne"
}
```

该网关是只读查询。可使用 `action: help` 查看当前已注册命令。

所有已启用玩家榜单只纳入总对局数至少 20 局的玩家；个人 `stats`、`roles`、`deaths` 等查询不受此限制。杀手搭档榜还要求两人共同作为杀手至少 5 局。

## 数据库迁移

启动时会自动执行 Alembic 迁移。旧版本创建但没有 `alembic_version` 的数据库会自动标记为初始基线，不会删除或重建现有数据。

手动检查版本：

```bash
uv run alembic current
```

## 测试

```bash
uv run pytest
```

测试使用内存 SQLite 和临时目录，不会修改正式数据。
