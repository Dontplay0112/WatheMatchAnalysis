export const API_BASE_URL = "http://127.0.0.1:8897/api"; // 确保端口号正确

/**
 * 快捷获取目标玩家名称
 * 优先级：玩家输入的参数 > 本地绑定的ID
 */
export function getTargetPlayer(ext: any, ctx: any, arg2: string): string {
    if (arg2) return arg2;
    return ext.storageGet(`bind_${ctx.player.userId}`) || "";
}
