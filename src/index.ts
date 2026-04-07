// ==UserScript==
// @name         WatheMatchBot
// @author       Dont_play
// @version      5.0.0
// @description  Wathe 对局统计
// @timestamp    1775204147
// @license      MIT
// ==/UserScript==

import { CommandManager } from './core/CommandManager';
import { BindCommand } from './commands/BindCommand';
import { UnbindCommand } from './commands/UnbindCommand';

function main() {
    let ext = seal.ext.find('wathe_bot');
    if (!ext) {
        ext = seal.ext.new('wathe_bot', 'Dont_play', '5.0.0');
        seal.ext.register(ext);
    }

    // ⚙️ 仅注册需要本地处理的指令
    const manager = new CommandManager();
    manager.register(new BindCommand());
    manager.register(new UnbindCommand());

    const cmdWathe = seal.ext.newCmdItemInfo();
    cmdWathe.name = 'wathe';
    // 帮助文本的生成权移交给了 CommandManager 内部处理
    cmdWathe.help = ""; 

    cmdWathe.solve = (ctx, msg, cmdArgs) => {
        let subCmd = cmdArgs.getArgN(1);
        // 直接将一切抛给管理器
        manager.execute(subCmd, ext, ctx, msg, cmdArgs);
        return seal.ext.newCmdExecuteResult(true);
    };

    ext.cmdMap['wathe'] = cmdWathe;
    console.log('WatheMatchBot 已加载');
}

main();