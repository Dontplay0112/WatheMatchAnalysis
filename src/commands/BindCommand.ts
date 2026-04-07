// src/commands/BindCommand.ts
import { BaseCommand } from '../core/BaseCommand';

export class BindCommand extends BaseCommand {
    name = "bind";
    usage = "<游戏ID>";
    description = "绑定你的Minecraft游戏名";

    async execute(ext: any, ctx: any, msg: any, cmdArgs: any): Promise<void> {
        let arg2 = cmdArgs.getArgN(2);
        
        if (!arg2) {
            seal.replyToSender(ctx, msg, "❌ 请提供要绑定的游戏ID！例如: .wathe bind Dont_play");
            return;
        }
        
        ext.storageSet(`bind_${ctx.player.userId}`, arg2);
        seal.replyToSender(ctx, msg, `✅ 成功绑定游戏ID: ${arg2}\n以后查询自己的战绩只需输入 .wathe stats`);
    }
}