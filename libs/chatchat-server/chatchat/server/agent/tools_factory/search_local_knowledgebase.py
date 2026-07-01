from urllib.parse import urlencode

from chatchat.settings import Settings
from chatchat.server.agent.tools_factory.tools_registry import (
    regist_tool,
    format_context,
)

from langchain_chatchat.agent_toolkits.all_tools.tool import (
    BaseToolOutput,
)
from chatchat.server.knowledge_base.kb_api import list_kbs
from chatchat.server.knowledge_base.kb_doc_api import search_docs
from chatchat.server.pydantic_v1 import Field
from chatchat.server.reranker.reranker import rerank_docs
from chatchat.server.utils import get_tool_config

template = (
    "Use local knowledgebase from one or more of these:\n{KB_info}\n to get information，Only local data on "
    "this knowledge use this tool. The 'database' should be one of the above [{key}]."
)
KB_info_str = "\n".join([f"{key}: {value}" for key, value in Settings.kb_settings.KB_INFO.items()])
template_knowledge = template.format(KB_info=KB_info_str, key="samples")


def _normalize_database(database: str) -> str:
    """将大模型输出的 database 参数归一化到真实存在的知识库名。

    大模型有时会把库名输出为 "库名: 描述"（如 "samples: HK32F39资料"），
    而检索按精确库名匹配，不归一化会因查不到库而检索失败。
    """
    if not database:
        return database
    known_kbs = [kb.kb_name for kb in list_kbs().data]
    if database in known_kbs:
        return database
    # 依次尝试：去掉冒号后缀、用已知库名做包含/前缀匹配
    candidate = database.split(":", 1)[0].strip()
    if candidate in known_kbs:
        return candidate
    for kb_name in known_kbs:
        if database.strip().startswith(kb_name) or kb_name in database:
            return kb_name
    return database


def search_knowledgebase(query: str, database: str, config: dict):
    database = _normalize_database(database)
    # 开启 Rerank 时先用更大的 top_k 检索，再重排取 top_k，提升检索质量（与 RAG 对话页一致）
    top_k = config["top_k"]
    use_reranker = Settings.kb_settings.USE_RERANKER
    initial_top_k = Settings.kb_settings.INITIAL_SEARCH_TOP_K if use_reranker else top_k
    docs = search_docs(
        query=query,
        knowledge_base_name=database,
        top_k=initial_top_k,
        score_threshold=config["score_threshold"],
        file_name="",
        metadata={},
    )
    if use_reranker and len(docs) > 0:
        docs = rerank_docs(docs, query, top_n=top_k)
    return {"knowledge_base": database, "docs": docs}


@regist_tool(description=template_knowledge, title="本地知识库")
def search_local_knowledgebase(
    database: str = Field(
        description="Database for Knowledge Search",
        choices=[kb.kb_name for kb in list_kbs().data],
    ),
    query: str = Field(description="Query for Knowledge Search"),
):
    """"""
    tool_config = get_tool_config("search_local_knowledgebase")
    ret = search_knowledgebase(query=query, database=database, config=tool_config)
    return BaseToolOutput(ret, format=format_context)
