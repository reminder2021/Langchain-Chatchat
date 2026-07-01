import os
import sys
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from typing import Any, Dict, List, Optional, Sequence

import httpx
from langchain.callbacks.manager import Callbacks
from langchain.retrievers.document_compressors.base import BaseDocumentCompressor
from langchain_core.documents import Document
from pydantic import Field, PrivateAttr

logger = logging.getLogger(__name__)


class ZhipuReranker(BaseDocumentCompressor):
    """通过智谱GLM-Rerank API进行文档重排序"""

    api_key: str = Field()
    api_base_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4")
    model: str = Field(default="rerank")
    top_n: int = Field(default=5)
    _client: Any = PrivateAttr()

    def __init__(
        self,
        api_key: str,
        api_base_url: str = "https://open.bigmodel.cn/api/paas/v4",
        model: str = "rerank",
        top_n: int = 5,
    ):
        super().__init__(
            api_key=api_key,
            api_base_url=api_base_url,
            model=model,
            top_n=top_n,
        )
        # 基类 BaseDocumentCompressor 是 pydantic v1 model，不允许直接给未声明字段赋值，
        # 用 object.__setattr__ 绕过校验来持有 httpx.Client
        object.__setattr__(self, "_client", httpx.Client(timeout=30.0))

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        """
        使用智谱GLM-Rerank API对文档进行重排序

        Args:
            documents: 待重排序的文档序列
            query: 用户查询
            callbacks: 回调函数

        Returns:
            重排序后的文档序列
        """
        if len(documents) == 0:
            return []

        doc_list = list(documents)
        doc_texts = [d.page_content for d in doc_list]

        try:
            response = self._client.post(
                f"{self.api_base_url}/rerank",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "query": query,
                    "documents": doc_texts,
                    "top_n": min(self.top_n, len(doc_texts)),
                },
            )
            response.raise_for_status()
            result = response.json()

            final_results = []
            for item in result.get("results", []):
                index = item.get("index", 0)
                relevance_score = item.get("relevance_score", 0.0)
                if 0 <= index < len(doc_list):
                    doc = doc_list[index]
                    doc.metadata["relevance_score"] = relevance_score
                    final_results.append(doc)

            logger.info(
                f"智谱Rerank完成: 输入{len(doc_list)}个文档, "
                f"输出{len(final_results)}个文档"
            )
            return final_results

        except Exception as e:
            logger.error(f"智谱Rerank API调用失败: {e}")
            # 降级：返回原始文档
            return doc_list[:self.top_n]


def rerank_docs(docs: Sequence[dict], query: str, top_n: int = None) -> Sequence[dict]:
    """对检索到的文档做智谱GLM-Rerank重排序，提升检索质量。

    供「知识库搜索工具」与「RAG 对话(kb_chat)」共用，避免重复实现。
    Args:
        docs: search_docs 返回的 list[dict]，每个含 page_content / metadata
        query: 用户查询
        top_n: 重排后保留的条数，默认用配置 INITIAL_SEARCH_TOP_K
    Returns:
        重排后的 list[dict]（含 page_content / metadata / score）。失败时原样返回 docs。
    """
    if not docs:
        return docs
    try:
        from langchain_core.documents import Document as LCDocument
        from chatchat.settings import Settings

        if Settings.kb_settings.RERANKER_TYPE != "zhipu":
            logger.warning(f"不支持的Reranker类型: {Settings.kb_settings.RERANKER_TYPE}，跳过Rerank")
            return docs

        api_key = ""
        for platform in Settings.model_settings.MODEL_PLATFORMS:
            if platform.platform_name == "zhipuai":
                api_key = platform.api_key
                break
        if not api_key:
            logger.warning("未找到智谱API Key，跳过Rerank")
            return docs

        top_n = top_n or Settings.kb_settings.INITIAL_SEARCH_TOP_K
        reranker = ZhipuReranker(
            api_key=api_key,
            model=Settings.kb_settings.RERANKER_MODEL,
            top_n=min(top_n, len(docs)),
        )
        lcdocs = [LCDocument(page_content=d["page_content"], metadata=d.get("metadata", {})) for d in docs]
        reranked = reranker.compress_documents(documents=lcdocs, query=query)
        logger.info(f"智谱Rerank完成: {len(lcdocs)} -> {len(reranked)} 个文档")
        return [
            {
                "page_content": d.page_content,
                "metadata": d.metadata,
                "score": d.metadata.get("relevance_score"),
            }
            for d in reranked
        ]
    except Exception as e:
        logger.error(f"Rerank失败，使用原始结果: {e}")
        return docs


class LangchainReranker(BaseDocumentCompressor):
    """使用本地CrossEncoder模型进行文档重排序"""

    model_name_or_path: str = Field()
    _model: Any = PrivateAttr()
    top_n: int = Field()
    device: str = Field()
    max_length: int = Field()
    batch_size: int = Field()
    num_workers: int = Field()

    def __init__(
        self,
        model_name_or_path: str,
        top_n: int = 3,
        device: str = "cuda",
        max_length: int = 1024,
        batch_size: int = 32,
        num_workers: int = 0,
    ):
        from sentence_transformers import CrossEncoder

        self._model = CrossEncoder(
            model_name=model_name_or_path, max_length=max_length, device=device
        )
        super().__init__(
            top_n=top_n,
            model_name_or_path=model_name_or_path,
            device=device,
            max_length=max_length,
            batch_size=batch_size,
            num_workers=num_workers,
        )

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:
        if len(documents) == 0:
            return []
        doc_list = list(documents)
        _docs = [d.page_content for d in doc_list]
        sentence_pairs = [[query, _doc] for _doc in _docs]
        results = self._model.predict(
            sentences=sentence_pairs,
            batch_size=self.batch_size,
            num_workers=self.num_workers,
            convert_to_tensor=True,
        )
        top_k = self.top_n if self.top_n < len(results) else len(results)

        values, indices = results.topk(top_k)
        final_results = []
        for value, index in zip(values, indices):
            doc = doc_list[index]
            doc.metadata["relevance_score"] = value
            final_results.append(doc)
        return final_results
