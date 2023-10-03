### 镜像选择
* 基础镜像 `mcr.microsoft.com/playwright/python`
* docker hub 地址:`https://hub.docker.com/_/microsoft-playwright-python`
### 容器创建与配置
#### 容器创建参数
* 环境:添加 GID:100, TZ:Asia/Shanghai, UMASK:002
* 网络：选择Bridge模式，以方便ssh进去且不与本机端口冲突
* 共享文件夹: 挂载 /docker-data 目录
#### 容器配置
* 进入终端，apt-get update, apt-get upgrade
* 安装vim 等工具, apt-get install vim, apt-get install mlocate, 
- 安装字体  apt install fonts-noto-cjk
* 安装ssh,`https://blog.csdn.net/weixin_45054115/article/details/125471103`
* 设置成功后改为使用 `xshell`,`winScp` 控制
#### 安装bot程序
* 安装haruka-bot和go-cqhttp
  - pip install haruka-bot
  - dpkg -i /docker-data/go-cqhttp_1.0.0-rc4_linux_amd64.deb
  - 注意此时不要去修改 haruka-bot 安装目录中的文件，否则会导致 pip install --upgrade/uninstall 时被修改的文件无法更新
  - /docker-data/start_bots.sh 跑起来看看
  - 保存此镜像为 `gocq-hb-bots-ssh-original`
* 修改bots为自定义
  - 使用 LialaBots 覆盖 `/usr/local/lib/python3.8/dist-packages/haruka_bot` 目录以及 `nonebot` 相关目录
  - 使用自定义的 go-cqhttp 覆盖 `/usr/bin/go-cqhttp`
  - /docker-data/start_bots.sh 跑起来看看
  - 保存此镜像为 `gocq-hb-bots-ssh-custom`
* 重新创建容器
  - 删除当前容器
  - 使用 `gocq-hb-bots-ssh-custom` 重新创建容器，启动命令改为 `bash /docker-data/start_bots.sh`