import { BaseCommand } from './BaseCommand';
import { getTargetPlayer, API_BASE_URL } from '../utils';

export class CommandManager {
    private commands: Map<string, BaseCommand> = new Map();

    // 注册本地子命令 (bind, unbind 等)
    public register(command: BaseCommand) {
        this.commands.set(command.name, command);
    }

    // 🌟 执行指令：本地拦截 + 远程转发
    public async execute(subCmd: string, ext: any, ctx: any, msg: any, cmdArgs: any) {
        const command = this.commands.get(subCmd);
        
        // 1. 如果本地注册了该指令 (如 bind, unbind)，直接本地执行
        if (command) {
            command.execute(ext, ctx, msg, cmdArgs);
            return;
        }

        // 2. 如果本地没有，将一切未知指令作为动态 action 转发给 Python 后端网关
        const action = subCmd || "help"; 
        const playerName = getTargetPlayer(ext, ctx, cmdArgs.getArgN(2));

        try {
            // 使用你在 utils.ts 中定义的 API_BASE_URL
            const url = `${API_BASE_URL}`; 
            const res = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    action: action,
                    player_name: playerName
                })
            });

            if (!res.ok) {
                seal.replyToSender(ctx, msg, `❌ 查询失败，后端异常 (HTTP 状态码: ${res.status})`);
                return;
            }

            const data = await res.json();
            let replyText = data.reply;

            // 🌟 3. 完美融合：如果是请求帮助菜单，我们将本地的 bind/unbind 也追加在最后
            if (action === "help") {
                replyText += `绑定命令(方便查自己的数据):\n`;
                for (const cmd of this.commands.values()) {
                    let usageStr = cmd.usage ? ` ${cmd.usage}` : "";
                    let leftPart = `  .wathe ${cmd.name}${usageStr}`.padEnd(25, " ");
                    replyText += `${leftPart} - ${cmd.description}\n`;
                }
            }

            seal.replyToSender(ctx, msg, replyText);

        } catch (err: any) {
            seal.replyToSender(ctx, msg, `❌ 无法连接到 Wathe 数据中心: ${err.message}`);
        }
    }
}