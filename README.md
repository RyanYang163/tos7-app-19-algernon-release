# Algernon

> ⚠️ **本仓库是 TOS 7 应用审核流程的测试语料,不是可用的应用。**
> 它**故意违反**了《TOS 7 应用开发指引》第 16 章的多条审核条目,
> 用于验证审核系统能否正确识别并拦截这些缺陷。
> **请勿安装、请勿用于生产环境。**

## 应用信息

| 项 | 值 |
|---|---|
| 应用 ID | `tos7-app-19-algernon` |
| 类型 | Deb 应用(单包模式) |
| 版本 | 1.0.0 |
| 上游项目 | https://github.com/xyproto/algernon |
| 许可证 | BSD-3-Clause |
| 访问端口 | 18099 |

## 故意违反的审核条目

本版本故意违反以下条目(编号见 `16_Review_Standards.md`):

**`H1, H12`**

具体落地方式见 [`VIOLATIONS.md`](./VIOLATIONS.md)。

## 打包

```bash
./build.sh
```

产物在 `build/output/`,同级生成与包同名的 `<包名>.sha256`。

## 上游说明

本仓库仅包含 TOS 7 应用封装所需的配置文件与打包脚本,
应用本身的源码与二进制来自上游项目:https://github.com/xyproto/algernon
