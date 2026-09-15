# tos7-app-19-algernon — TOS 7 应用发布仓库

本仓库用于存放 **Algernon** 的 TOS 7 应用包(Release 资产)。
TOS 开发者平台会**从本仓库的 Release 中自动拉取应用包**,不使用仓库根目录的文件。

> ⚠️ **本应用是审核流程的测试语料,不是可用的应用。**
> 它故意违反《TOS 7 应用开发指引》第 16 章的多条审核条目,
> 用于验证审核系统能否正确识别并拦截。**请勿安装。**

## 当前收录的应用

| 应用 ID | 类型 | 包文件 | 说明 |
|---|---|---|---|
| `tos7-app-19-algernon` | Deb 应用(单包模式) | `tos7-app-19-algernon_1.0.0_amd64.deb` | A pure Go web server with built-in support for Lua, Markdown and templates. |

**故意违反的条目**:`A1, H1, H12`(详见源码仓库的 `VIOLATIONS.md`)

## 目录约定

- 应用包**只放在 Release 资产里**,不要放在仓库根目录。
- 每个 Release 的 **tag 与包内 `config.ini` 的 `version` 字段对应**。
- 每个 Release **只放一个架构**的包(`x86_64`)。
- 每个包配一个同名的 `.sha256` / `sha256sum.txt` 校验文件,平台会按它核对。

## 相关仓库

- 源码仓库(私有):https://github.com/RyanYang163/tos7-app-19-algernon
- 上游项目:https://github.com/xyproto/algernon
