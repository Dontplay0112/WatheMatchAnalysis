def format_reply(reply: str) -> str:
    """在文本中添加换行符以避免过长的行"""
    if reply.startswith("\n"):
        reply = reply[1:]  # 去掉开头的换行，后面统一添加
    if reply.endswith("\n"):
        reply = reply[:-1]  # 去掉末尾的换行，后面统一添加
    reply = "==========↓=↓=↓=↓==========\n" + reply + "\n==========↑=↑=↑=↑==========\n"
    # 给每一行前面加4个空格
    # reply = "\n".join("          " + line for line in reply.splitlines())
    # reply = "<bot>" + reply[10:]  # 整体再加4个空格缩进
    return reply