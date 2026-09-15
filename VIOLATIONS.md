# 违规清单 — Algernon

本版本故意违反 **2** 条审核条目,逐条落地方式如下:

| 条目 | 落地方式 |
|---|---|
| **H1** | systemd 服务的 `User` / `Group` 设为 `root` |
| **H12** | `DEBIAN/postinst` 执行 `apt-get install` / `pip install` / `curl | bash` 等网络操作 |

## 说明
