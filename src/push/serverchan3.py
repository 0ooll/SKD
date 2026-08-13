import logging
import os
import re
from datetime import date
from typing import Tuple

import requests


def _format_serverchan_desp(all_logs: list[str]) -> str:
    if not all_logs:
        return '今日无可用账号或无输出'

    lines: list[str] = []
    for item in all_logs:
        text = item.replace('\r\n', '\n')
        parts = text.split('\n\n')
        if not parts:
            lines.append('')
            continue
        lines.extend(parts)

    # Server酱 desp 使用 Markdown，单换行会折叠为一个空格，需要显式换行。
    return '  \n'.join(line.rstrip() for line in lines)


def push_serverchan3(all_logs: list[str]):
    # === Server酱³ 推送（可选，通过环境变量控制） ===
    # 在本地或 GitHub Actions 设置：
    #   SC3_SENDKEY: 必填
    #   SC3_UID: 可选（若不设，将自动从 sendkey 中提取）
    sendkey = os.environ.get('SC3_SENDKEY', '').strip()
    if not sendkey:
        return
    title = f'森空岛自动签到结果 - {date.today().strftime("%Y-%m-%d")}'

    desp = _format_serverchan_desp(all_logs)

    payload = {
        "title": title or "通知",
        "desp": desp or "",
    }

    if sendkey.startswith("SCT"):
        # Server酱³ Turbo：SCT + uid + T + 随机串，接口不需要单独传 uid
        api = f"https://sctapi.ftqq.com/{sendkey}.send"
        request_kwargs = {"data": payload}
    else:
        m = re.match(r"^sctp(\d+)t", sendkey)
        if not m:
            logging.error("cannot extract uid from sendkey; please pass uid explicitly")
            return
        uid = os.environ.get('SC3_UID', '').strip() or m.group(1)
        api = f"https://{uid}.push.ft07.com/send/{sendkey}.send"
        request_kwargs = {"json": payload}
    # if tags:
    #     payload["tags"] = tags
    # if short:
    #     payload["short"] = short

    try:
        r = requests.post(api, **request_kwargs)
        ok = (r.status_code == 200)
        if ok:
            logging.info("Server酱3 推送成功")
        else:
            logging.error(f"serverchan推送失败,http代码{r.status_code},{r.text}")
    except Exception as e:
        logging.error("serverchan推送失败", exc_info=e)
