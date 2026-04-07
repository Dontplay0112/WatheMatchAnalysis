// src/commands/UnbindCommand.ts
import { BaseCommand } from '../core/BaseCommand';

export class UnbindCommand extends BaseCommand {
    name = "unbind";
    usage = "";
    description = "解除已绑定的游戏ID";

    async execute(ext: any, ctx: any, msg: any, cmdArgs: any): Promise<void> {
        let currentBind = ext.storageGet(`bind_${ctx.player.userId}`);
        
        if (!currentBind) {
            seal.replyToSender(ctx, msg, "❌ 你还没有绑定过任何游戏ID哦！");
        } else {
            // 将存储的值置空，实现解绑
            ext.storageSet(`bind_${ctx.player.userId}`, "");
            seal.replyToSender(ctx, msg, `✅ 已成功解除与游戏ID [${currentBind}] 的绑定。`);
        }
    }
}