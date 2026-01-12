# ChipCompiler

#### 介绍
ECOS chip design solution.

#### 软件架构
软件架构说明


## 安装

### 方式一：Nix 一键安装（推荐给用户）

Nix 提供了完整的依赖管理和可复现的构建环境，是最简单的安装方式。

```bash
# 安装 Nix（如果尚未安装）
curl -LsSf https://nixos.org/nix/install | sh

# 进入开发环境
nix develop
```

也可以使用 [direnv](https://direnv.net/) 来自动加载 Nix 环境：

```bash
echo "use flake" > .envrc
direnv allow
```

**支持的平台**：x86_64-linux

### 方式二：使用 build.sh

**注意**：此方式需要手动安装 iEDA 工具（iEDA）

```bash
# 创建虚拟环境并安装依赖
./build.sh

# 激活虚拟环境
source .venv/bin/activate
```

## 开发者指南

```bash
./build.sh
```

#### 使用说明

1.  xxxx
2.  xxxx
3.  xxxx

#### 参与贡献

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request


#### 特技

1.  使用 Readme\_XXX.md 来支持不同的语言，例如 Readme\_en.md, Readme\_zh.md
2.  Gitee 官方博客 [blog.gitee.com](https://blog.gitee.com)
3.  你可以 [https://gitee.com/explore](https://gitee.com/explore) 这个地址来了解 Gitee 上的优秀开源项目
4.  [GVP](https://gitee.com/gvp) 全称是 Gitee 最有价值开源项目，是综合评定出的优秀开源项目
5.  Gitee 官方提供的使用手册 [https://gitee.com/help](https://gitee.com/help)
6.  Gitee 封面人物是一档用来展示 Gitee 会员风采的栏目 [https://gitee.com/gitee-stars/](https://gitee.com/gitee-stars/)
