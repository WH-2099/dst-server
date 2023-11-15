import asyncio
import json
import os
import re


def fd_change2(from_fd: int, to_fd: int) -> int:
    """替换文件描述符并确保其可继承"""

    if from_fd != to_fd:
        os.dup2(from_fd, to_fd)
        os.close(from_fd)
    os.set_inheritable(to_fd, True)
    return to_fd


def fd_pipe(child_fd: int, parent_fd: int, child_mode: str) -> None:
    """打开文件描述符作为 pipe"""

    if child_mode == "r":
        cfd, pfd = os.pipe()
    elif child_mode == "w":
        pfd, cfd = os.pipe()
    else:
        raise ValueError(f"unsupport child mode {child_mode}")

    fd_change2(cfd, child_fd)
    fd_change2(pfd, parent_fd)


async def readline_pipe(self, fd: int) -> str:
    """异步管道读写"""

    loop = asyncio.get_running_loop()
    stream_reader = asyncio.StreamReader(loop=loop)
    transport, protocol = await loop.connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(stream_reader, loop=loop),
        os.fdopen(fd, "rb"),
    )
    stream_reader.set_transport(transport)
    data = await stream_reader.readline()
    return data.decode("utf-8")


def lua_table_to_dict(raw_str: str) -> dict:
    """将表示 lua 中 table 的字符串转为 Python 中的 dict"""

    table_str = raw_str[raw_str.find("{") : raw_str.rfind("}") + 1]
    s = table_str.replace("=", ":").replace('["', '"').replace('"]', '"')
    s = re.sub(r"(?P<key>[\w.]+)(?=\s*?:)", r'"\g<key>"', s)  # 键加双引号
    s = re.sub(r",(?=\s*?[}|\]])", "", s)  # 去列表尾逗号
    return json.loads(s)


def lua_table_to_list(raw_str: str) -> list:
    """将表示 lua 中 table 的字符串转为 Python 中的 list"""

    table_str = raw_str[raw_str.find("{") : raw_str.rfind("}") + 1]
    s = table_str.replace("=", ":").replace('["', '"').replace('"]', '"')
    s = re.sub(r"(?P<key>[\w.]+)(?=\s*?:)", r'"\g<key>"', s)  # 键加双引号
    s = re.sub(r",(?=\s*?[}|\]])", "", s)  # 去列表尾逗号
    s = re.sub(r"^{", "[", s)  # 替换头大括号
    s = re.sub(r"}$", "]", s)  # 替换尾大括号
    return json.loads(s)
