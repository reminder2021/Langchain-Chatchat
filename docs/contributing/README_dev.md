# Langchain-Chatchat 源代码部署/开发部署指南

## 0. 拉取项目代码

如果您是想要使用源码启动的用户，请直接拉取 master 分支代码

```shell
git clone https://github.com/chatchat-space/Langchain-Chatchat.git
```

## 1. 初始化开发环境

Langchain-Chatchat 自 0.3.0 版本起，为方便支持用户使用 pip 方式安装部署，以及为避免环境中依赖包版本冲突等问题，
在源代码/开发部署中不再继续使用 requirements.txt 管理项目依赖库，转为使用 Poetry 进行环境管理。

### 1.1 安装 Poetry

> 在安装 Poetry 之前，如果您使用 Conda，请创建并激活一个新的 Conda 环境，例如使用 `conda create -n chatchat python=3.9` 创建一个新的 Conda 环境。

安装 Poetry: [Poetry 安装文档](https://python-poetry.org/docs/#installing-with-pipx)

> [!Note]
> 如果你没有其它 poetry 进行环境/依赖管理的项目，利用 pipx 或 pip 都可以完成 poetry 的安装，

> [!Note]
> 如果您使用 Conda 或 Pyenv 作为您的环境/包管理器，在安装Poetry之后，
> 使用如下命令使 Poetry 使用 virtualenv python environment (`poetry config virtualenvs.prefer-active-python true`)

### 1.2 安装源代码/开发部署所需依赖库

进入主项目目录，并安装 Langchain-Chatchat 依赖

```shell
cd  Langchain-Chatchat/libs/chatchat-server/
poetry install --with lint,test -E xinference

# or use pip to install in editing mode:
pip install -e .
```

> [!Note]
> Poetry install 后会在你的虚拟环境中 site-packages 路径下生成一个 chatchat-`<version>`.dist-info 文件夹带有 direct_url.json 文件，这个文件指向你的开发环境

### 1.3 更新开发部署环境依赖库

当开发环境中所需的依赖库发生变化时，一般按照更新主项目目录(`Langchain-Chatchat/libs/chatchat-server/`)下的 pyproject.toml 再进行 poetry update 的顺序执行。

### 1.4 将更新后的代码打包测试

如果需要对开发环境中代码打包成 Python 库并进行测试，可在主项目目录执行以下命令：

```shell
poetry build
```

命令执行完成后，在主项目目录下会新增 `dist` 路径，其中存储了打包后的 Python 库。

## 2. 设置源代码根目录

如果您在开发时所使用的 IDE 需要指定项目源代码根目录，请将主项目目录(`Langchain-Chatchat/libs/chatchat-server/`)设置为源代码根目录。

执行以下命令之前，请先设置当前目录和项目数据目录：
```shell
cd Langchain-Chatchat/libs/chatchat-server/chatchat
export CHATCHAT_ROOT=/parth/to/chatchat_data
```

## 3. 关于 chatchat 配置项

从 `0.3.1` 版本开始，所有配置项改为 `yaml` 文件，具体参考 [Settings](settings.md)。

执行以下命令初始化项目配置文件和数据目录：
```shell
cd libs/chatchat-server
python chatchat/cli.py init
```

## 4. 初始化知识库

> [!WARNING]
> 这个命令会清空数据库、删除已有的配置文件，如果您有重要数据，请备份。

```shell
cd libs/chatchat-server
python chatchat/cli.py kb --recreate-vs
```
如需使用其它 Embedding 模型，或者重建特定的知识库，请查看 `python chatchat/cli.py kb --help` 了解更多的参数。

## 5. 启动服务

```shell
cd libs/chatchat-server
python chatchat/cli.py start -a
```

如需调用 API，请参考 [API 使用说明](api.md)

## 6. 本地源码安装调试指南

本节提供在本地从源码安装和调试的完整步骤，适用于 macOS 和 Linux 环境。

### 6.1 环境要求

- Python 3.10 或 3.11（项目不支持 Python 3.12+）
- Git

### 6.2 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/chatchat-space/Langchain-Chatchat.git
cd Langchain-Chatchat

# 2. 创建 Python 3.11 虚拟环境
python3.11 -m venv libs/chatchat-server/zhwVenv
source libs/chatchat-server/zhwVenv/bin/activate

# 3. 升级 pip 和构建工具（指定兼容版本）
pip3 install --upgrade pip setuptools
pip3 install wheel==0.43.0
pip3 install "packaging>=23.2,<24.0"

# 4. 安装 humanlayer（镜像源可能没有）
pip3 install humanlayer --index-url https://pypi.org/simple/

# 5. 安装项目依赖
cd libs/chatchat-server
pip3 install -e .
```

### 6.3 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `Python 3.x.x not in '<3.12,>=3.10'` | Python 版本不兼容 | 使用 Python 3.10 或 3.11 |
| `No matching distribution found for humanlayer==0.7.6` | 镜像源未同步或版本不存在 | 从官方 PyPI 安装：`pip3 install humanlayer --index-url https://pypi.org/simple/` |
| `ModuleNotFoundError: No module named 'pkg_resources'` | setuptools 缺失 | `pip3 install setuptools` |
| `wheel requires packaging>=24.0` | wheel 版本过高 | `pip3 install wheel==0.43.0` |
| `langchain-core requires packaging<24.0` | packaging 版本过高 | `pip3 install "packaging>=23.2,<24.0"` |

### 6.4 验证安装

```bash
# 检查 Python 路径（应指向虚拟环境）
which python3

# 检查已安装的包数量
pip3 list | wc -l

# 检查 langchain-chatchat 是否安装成功
pip3 show langchain-chatchat
```

## 7. 云端API配置建议

对于没有本地GPU资源或希望快速体验的用户，推荐使用云端API服务。以下提供两种经过验证的配置方案。

### 7.1 方案一：DeepSeek + 智谱AI（推荐）

**适用场景**：追求性价比，中文支持优秀

- **LLM对话**：使用DeepSeek（价格低，推理能力强）
- **Embedding模型**：使用智谱AI的embedding-3（中文优化好，价格最低）

**配置步骤**：

1. 获取API密钥：
   - DeepSeek：访问 https://platform.deepseek.com/ 注册并获取API Key
   - 智谱AI：访问 https://open.bigmodel.cn/ 注册并获取API Key

2. 编辑配置文件 `model_settings.yaml`：

```yaml
# 模型配置项

# 默认选用的 LLM 名称
DEFAULT_LLM_MODEL: deepseek-chat

# 默认选用的 Embedding 名称
DEFAULT_EMBEDDING_MODEL: embedding-3

# AgentLM模型的名称
Agent_MODEL: ''

# 默认历史对话轮数
HISTORY_LEN: 3

# 大模型最长支持的长度
MAX_TOKENS:

# LLM通用对话参数
TEMPERATURE: 0.7

# 支持的Agent模型
SUPPORT_AGENT_MODELS:
  - deepseek-chat
  - deepseek-reasoner
  - glm-4
  - gpt-4o

# LLM模型配置
LLM_MODEL_CONFIG:
  preprocess_model:
    model: ''
    temperature: 0.05
    max_tokens: 4096
    history_len: 10
    prompt_name: default
    callbacks: false
  llm_model:
    model: ''
    temperature: 0.9
    max_tokens: 4096
    history_len: 10
    prompt_name: default
    callbacks: true
  action_model:
    model: ''
    temperature: 0.01
    max_tokens: 4096
    history_len: 10
    prompt_name: ChatGLM3
    callbacks: true
  postprocess_model:
    model: ''
    temperature: 0.01
    max_tokens: 4096
    history_len: 10
    prompt_name: default
    callbacks: true
  image_model:
    model: sd-turbo
    size: 256*256

# 模型平台配置
MODEL_PLATFORMS:
  # DeepSeek配置（用于LLM对话）
  - platform_name: deepseek
    platform_type: openai
    api_base_url: https://api.deepseek.com/v1
    api_key: 你的DeepSeek API密钥  # 替换为实际密钥
    api_proxy: ''
    api_concurrencies: 5
    auto_detect_model: false
    llm_models:
      - deepseek-chat
      - deepseek-reasoner
    embed_models: []
    text2image_models: []
    image2text_models: []
    rerank_models: []
    speech2text_models: []
    text2speech_models: []
  
  # 智谱AI配置（用于Embedding）
  - platform_name: zhipuai
    platform_type: openai
    api_base_url: https://open.bigmodel.cn/api/paas/v4
    api_key: 你的智谱AI API密钥  # 替换为实际密钥
    api_proxy: ''
    api_concurrencies: 5
    auto_detect_model: false
    llm_models: []
    embed_models:
      - embedding-3
    text2image_models: []
    image2text_models: []
    rerank_models: []
    speech2text_models: []
    text2speech_models: []
```

**价格参考**：
- DeepSeek deepseek-chat：约 ¥1/百万token
- 智谱AI embedding-3：约 ¥0.5/百万token

### 7.2 方案二：通义千问全栈方案

**适用场景**：希望使用统一平台，简化管理

- **LLM对话**：使用通义千问系列（qwen-turbo/plus/max）
- **Embedding模型**：使用text-embedding-v3

**配置步骤**：

1. 获取API密钥：
   - 访问 https://dashscope.aliyun.com/ 注册阿里云账号
   - 开通DashScope服务并获取API Key
   - 新用户可领取免费额度（各100万token，90天有效）

2. 编辑配置文件 `model_settings.yaml`：

```yaml
# 模型配置项

# 默认选用的 LLM 名称
DEFAULT_LLM_MODEL: qwen-turbo

# 默认选用的 Embedding 名称
DEFAULT_EMBEDDING_MODEL: text-embedding-v3

# AgentLM模型的名称
Agent_MODEL: ''

# 默认历史对话轮数
HISTORY_LEN: 3

# 大模型最长支持的长度
MAX_TOKENS:

# LLM通用对话参数
TEMPERATURE: 0.7

# 支持的Agent模型
SUPPORT_AGENT_MODELS:
  - qwen-turbo
  - qwen-plus
  - qwen-max
  - gpt-4o

# LLM模型配置
LLM_MODEL_CONFIG:
  preprocess_model:
    model: ''
    temperature: 0.05
    max_tokens: 4096
    history_len: 10
    prompt_name: default
    callbacks: false
  llm_model:
    model: ''
    temperature: 0.9
    max_tokens: 4096
    history_len: 10
    prompt_name: default
    callbacks: true
  action_model:
    model: ''
    temperature: 0.01
    max_tokens: 4096
    history_len: 10
    prompt_name: ChatGLM3
    callbacks: true
  postprocess_model:
    model: ''
    temperature: 0.01
    max_tokens: 4096
    history_len: 10
    prompt_name: default
    callbacks: true
  image_model:
    model: sd-turbo
    size: 256*256

# 模型平台配置
MODEL_PLATFORMS:
  # 通义千问配置（用于LLM和Embedding）
  - platform_name: qwen
    platform_type: openai
    api_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key: 你的通义千问API密钥  # 替换为实际密钥
    api_proxy: ''
    api_concurrencies: 5
    auto_detect_model: false
    llm_models:
      - qwen-turbo
      - qwen-plus
      - qwen-max
      - qwen-long
    embed_models:
      - text-embedding-v3
    text2image_models: []
    image2text_models: []
    rerank_models: []
    speech2text_models: []
    text2speech_models: []
```

**价格参考**：
- qwen-turbo：输入 ¥0.8/百万token，输出 ¥4.8/百万token
- qwen-plus：输入 ¥0.8/百万token，输出 ¥4.8/百万token
- qwen-max：输入 ¥2.5/百万token，输出 ¥10/百万token
- text-embedding-v3：约 ¥0.7/百万token

### 7.3 配置完成后操作

完成配置文件编辑后，执行以下命令初始化知识库并启动服务：

```bash
# 进入项目目录
cd libs/chatchat-server

# 初始化知识库（重建向量库）
python chatchat/cli.py kb --recreate-vs

# 启动服务
python chatchat/cli.py start -a
```

### 7.4 常见问题

**Q1: 如何测试API是否配置正确？**

A1: 启动服务后，访问 http://localhost:8501 ，在对话界面输入简单问题（如"你好"），如果能正常回复则说明LLM配置正确。

**Q2: 知识库检索不准确怎么办？**

A2: 可能原因：
1. Embedding模型不适合中文场景 - 建议使用推荐的中文优化模型
2. 文档切分不合理 - 调整 `kb_settings.yaml` 中的 `CHUNK_SIZE` 和 `OVERLAP_SIZE`
3. 检索参数不合适 - 调整 `VECTOR_SEARCH_TOP_K` 和 `SCORE_THRESHOLD`

**Q3: API调用超时怎么办？**

A3: 在 `basic_settings.yaml` 中增加超时时间：
```yaml
HTTPX_DEFAULT_TIMEOUT: 600.0  # 默认300秒，可根据需要调整
```

**Q4: 如何切换不同的LLM模型？**

A4: 修改 `model_settings.yaml` 中的 `DEFAULT_LLM_MODEL` 字段，重启服务即可生效。确保所选模型已在对应的 `MODEL_PLATFORMS` 中配置。

### 7.5 模型选择建议

| 使用场景 | 推荐LLM | 推荐Embedding | 说明 |
|----------|---------|---------------|------|
| 日常对话、问答 | deepseek-chat / qwen-turbo | embedding-3 / text-embedding-v3 | 性价比高 |
| 复杂推理、代码 | deepseek-reasoner / qwen-max | embedding-3 / text-embedding-v3 | 推理能力强 |
| 长文档处理 | qwen-long | text-embedding-v3 | 支持超长上下文 |
| 多语言场景 | gpt-4o | text-embedding-3-small | 多语言支持好 |
