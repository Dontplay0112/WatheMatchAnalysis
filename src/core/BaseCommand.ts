import { API_BASE_URL } from '../utils';

export abstract class BaseCommand {
    abstract readonly name: string;
    abstract readonly description: string;
    readonly usage: string = "";
    readonly apiPath?: string; 

    /**
     * 统一的网络请求封装 (修复 404 捕获问题)
     */
    protected async requestApi(ctx: any, msg: any, param: string = ""): Promise<any> {
        if (!this.apiPath) return null;
        
        try {
            const url = param ? `${API_BASE_URL}${this.apiPath}/${param}` : `${API_BASE_URL}${this.apiPath}`;
            const res = await fetch(url);
            
            // 🌟 直接判断状态码，不使用 throw Error，避免 Goja 引擎异常对象丢失问题
            if (res.status === 404) {
                seal.replyToSender(ctx, msg, `❌ 数据库中未找到目标 [${param}] 的记录。`);
                return null;
            }
            
            // 其他非 200 状态码 (如 500 内部错误)
            if (!res.ok) {
                seal.replyToSender(ctx, msg, `❌ 查询失败，后端异常 (HTTP 状态码: ${res.status})`);
                return null;
            }
            
            // 只有 200 正常响应时才解析 JSON
            return await res.json();
            
        } catch (err: any) {
            // 只有真正的网络断开、后端完全没启动等严重报错，才会走到 catch 里
            seal.replyToSender(ctx, msg, `❌ 请求失败，请检查 Python 后端是否正在运行。\n(错误信息: ${err.message || err})`);
            return null;
        }
    }

    abstract execute(ext: any, ctx: any, msg: any, cmdArgs: any): Promise<void>;
}