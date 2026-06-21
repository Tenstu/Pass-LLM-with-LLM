"""text_pipeline.py — GitHub + Web KnowledgeSource 连接器。

实现 GitHubConnector（仓库内容抽取）和 WebConnector（网页内容抓取），
两者均遵循 KnowledgeSource Protocol，在可选依赖不可用时优雅降级。

用法:
    from exam_memory.text_pipeline import GitHubConnector, WebConnector

    gh = GitHubConnector(name="myrepo", repo="owner/repo", paths=["README.md"])
    gh.connect()
    chunks = gh.fetch("哈希表", limit=5)

    web = WebConnector(name="docs", urls=["https://example.com/guide"])
    web.connect()
    chunks = web.fetch("排序算法", limit=5)
"""

from __future__ import annotations

import logging
import os

from exam_memory.chunking import chunk_text
from exam_memory.knowledge_source import SourceChunk

logger = logging.getLogger(__name__)

# ── 可选依赖检测 ────────────────────────────────────────────────

try:
    from github import Github  # type: ignore[import-untyped]

    _GITHUB_AVAILABLE = True
except ImportError:
    _GITHUB_AVAILABLE = False
    Github = None  # type: ignore[assignment,misc]

try:
    import requests as _requests  # type: ignore[import-untyped]

    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False
    _requests = None  # type: ignore[assignment]

try:
    from bs4 import BeautifulSoup  # type: ignore[import-untyped]

    _BS4_AVAILABLE = True
except ImportError:
    _BS4_AVAILABLE = False
    BeautifulSoup = None  # type: ignore[assignment,misc]


# ── GitHubConnector ─────────────────────────────────────────────


class GitHubConnector:
    """GitHub 仓库内容抽取器（KnowledgeSource Protocol 实现）。

    通过 PyGithub 读取仓库文件，按关键词匹配后分块返回。
    无 PyGithub 时优雅降级：connect() 返回 False，fetch() 返回空列表。
    """

    def __init__(
        self,
        name: str,
        repo: str,
        paths: list[str] | None = None,
        branch: str = "main",
        token_env: str = "GITHUB_TOKEN",
    ) -> None:
        self._name = name
        self._repo_str = repo
        self._paths = paths  # None → 遍历全部
        self._branch = branch
        self._token_env = token_env
        self._connected = False
        self._files: list[str] = []  # 已索引的文件路径列表
        self._github_available = _GITHUB_AVAILABLE
        self._gh_client = None  # type: ignore[assignment]

    # ── Protocol properties ──────────────────────────────────────

    @property
    def name(self) -> str:
        return self._name

    @property
    def source_type(self) -> str:
        return "github"

    @property
    def connected(self) -> bool:
        return self._connected

    # ── Protocol methods ─────────────────────────────────────────

    def connect(self) -> bool:
        """验证 token（如有）和 repo 可达。

        Returns:
            True 验证通过；False 表示 PyGithub 不可用或连接失败。
        """
        if not self._github_available:
            logger.warning("GitHubConnector: PyGithub 未安装，跳过连接")
            return False

        token = os.environ.get(self._token_env)
        try:
            client = Github(login_or_token=token if token else None)
            client.get_repo(self._repo_str)
            self._gh_client = client
            self._connected = True
            logger.info(
                "GitHubConnector '%s': 连接到仓库 %s 成功", self._name, self._repo_str
            )
            return True
        except Exception as e:
            logger.warning(
                "GitHubConnector: 连接仓库失败 (%s): %s", self._repo_str, e
            )
            self._connected = False
            return False

    def fetch(self, topic: str, limit: int = 10) -> list[SourceChunk]:
        """读取仓库文件，关键词匹配后 chunking 返回。

        Args:
            topic: 搜索关键词（大小写不敏感）。
            limit: 最大返回 chunk 数。

        Returns:
            匹配的 SourceChunk 列表，最多 limit 个。
        """
        if not self._connected or self._gh_client is None:
            return []

        results: list[SourceChunk] = []
        collected_paths: list[str] = []
        topic_lower = topic.lower()

        try:
            repo = self._gh_client.get_repo(self._repo_str)
            paths_to_scan = self._paths if self._paths else [""]

            for path_prefix in paths_to_scan:
                if len(results) >= limit:
                    break
                self._walk_contents(
                    repo, path_prefix, topic_lower, limit, results, collected_paths
                )
        except Exception as e:
            logger.warning("GitHubConnector: fetch 失败 (%s): %s", self._name, e)

        self._files = collected_paths
        return results[:limit]

    def list_topics(self) -> list[str]:
        """返回已索引的文件路径列表（去扩展名）。"""
        return [self._path_without_ext(p) for p in self._files]

    def refresh(self) -> int:
        """重新拉取仓库文件，返回新增/更新的块数。"""
        if not self._connected:
            if not self.connect():
                return 0
        old_count = len(self._files)
        chunks = self.fetch("", limit=10_000)
        new_count = len(chunks)
        logger.info(
            "GitHubConnector '%s': refresh 完成，之前 %d 个文件，本次 %d 个 chunk",
            self._name,
            old_count,
            new_count,
        )
        return max(0, new_count)

    # ── 内部辅助 ─────────────────────────────────────────────────

    def _walk_contents(
        self,
        repo,
        path_prefix: str,
        topic_lower: str,
        limit: int,
        results: list[SourceChunk],
        collected_paths: list[str],
    ) -> None:
        """递归遍历 GitHub 仓库目录，按 topic 过滤并分块。"""
        try:
            contents = repo.get_contents(path_prefix, ref=self._branch)
        except Exception as e:
            logger.debug("GitHubConnector: 读取路径失败 %s: %s", path_prefix, e)
            return

        if not isinstance(contents, list):
            contents = [contents]

        for item in contents:
            if len(results) >= limit:
                return

            if item.type == "dir":
                self._walk_contents(
                    repo, item.path, topic_lower, limit, results, collected_paths
                )
                continue

            # 跳过过大文件（>1MB）
            if item.size > 1_000_000:
                logger.debug(
                    "GitHubConnector: 跳过过大文件 %s (%d bytes)",
                    item.path,
                    item.size,
                )
                continue

            collected_paths.append(item.path)

            try:
                content = item.decoded_content.decode("utf-8", errors="replace")
            except Exception as e:
                logger.debug("GitHubConnector: 解码失败 %s: %s", item.path, e)
                continue

            filename_match = topic_lower in item.path.lower()
            content_match = topic_lower in content.lower()

            if not filename_match and not content_match:
                continue

            chunks = chunk_text(content, max_chars=1600)
            for chunk_str in chunks:
                section = chunk_str.split("\n")[0].strip()[:80]
                results.append(
                    SourceChunk(
                        text=chunk_str,
                        source=item.path,
                        section=section,
                        metadata={
                            "source_url": item.html_url,
                            "filename_match": filename_match,
                            "content_match": content_match,
                            "repo": self._repo_str,
                            "branch": self._branch,
                        },
                    )
                )

    @staticmethod
    def _path_without_ext(path: str) -> str:
        """去除文件扩展名，返回路径尾部文件名。"""
        basename = path.rsplit("/", 1)[-1]
        dot_idx = basename.rfind(".")
        return basename[:dot_idx] if dot_idx >= 0 else basename


# ── WebConnector ────────────────────────────────────────────────


class WebConnector:
    """网页内容抓取器（KnowledgeSource Protocol 实现）。

    通过 requests + BeautifulSoup 抓取网页内容，提取正文后按关键词匹配分块。
    无 requests/beautifulsoup4 时优雅降级：connect() 返回 False，fetch() 返回空列表。
    """

    def __init__(
        self,
        name: str,
        urls: list[str],
        chunk_size: int = 2000,
    ) -> None:
        self._name = name
        self._urls = list(urls)
        self._chunk_size = chunk_size
        self._connected = False
        self._content_cache: dict[str, str] = {}
        self._requests_available = _REQUESTS_AVAILABLE
        self._bs4_available = _BS4_AVAILABLE

    # ── Protocol properties ──────────────────────────────────────

    @property
    def name(self) -> str:
        return self._name

    @property
    def source_type(self) -> str:
        return "web"

    @property
    def connected(self) -> bool:
        return self._connected

    # ── Protocol methods ─────────────────────────────────────────

    def connect(self) -> bool:
        """验证 URL 可达性（HEAD 请求，超时 5s）。

        Returns:
            True 至少一个 URL 可达；False 表示依赖不可用或全部不可达。
        """
        if not self._requests_available:
            logger.warning("WebConnector: requests 未安装，跳过连接")
            return False

        reachable = 0
        for url in self._urls:
            try:
                resp = _requests.head(url, timeout=5, allow_redirects=True)
                if resp.status_code < 400:
                    reachable += 1
                else:
                    logger.warning(
                        "WebConnector: URL 返回 %d — %s", resp.status_code, url
                    )
            except Exception as e:
                logger.warning("WebConnector: HEAD 请求失败 (%s): %s", url, e)

        if reachable > 0:
            self._connected = True
            logger.info(
                "WebConnector '%s': %d/%d 个 URL 可达",
                self._name,
                reachable,
                len(self._urls),
            )
        else:
            self._connected = False
            logger.warning("WebConnector '%s': 无 URL 可达", self._name)

        return self._connected

    def fetch(self, topic: str, limit: int = 10) -> list[SourceChunk]:
        """抓取网页内容，关键词匹配后 chunking 返回。

        Args:
            topic: 搜索关键词（大小写不敏感）。
            limit: 最大返回 chunk 数。

        Returns:
            匹配的 SourceChunk 列表，最多 limit 个。
        """
        if not self._requests_available or not self._bs4_available:
            logger.debug(
                "WebConnector: 缺少 requests 或 beautifulsoup4，返回空结果"
            )
            return []

        results: list[SourceChunk] = []
        topic_lower = topic.lower()

        for url in self._urls:
            if len(results) >= limit:
                break

            try:
                resp = _requests.get(url, timeout=10)
                resp.raise_for_status()
            except Exception as e:
                logger.warning("WebConnector: GET 请求失败 (%s): %s", url, e)
                continue

            try:
                soup = BeautifulSoup(resp.text, "html.parser")

                # 优先提取 <main> / <article> 区域
                main_tag = soup.find("main") or soup.find("article")
                if main_tag:
                    text = main_tag.get_text(separator="\n", strip=True)
                else:
                    text = soup.get_text(separator="\n", strip=True)
            except Exception as e:
                logger.warning("WebConnector: HTML 解析失败 (%s): %s", url, e)
                continue

            if topic_lower not in text.lower():
                continue

            chunks = chunk_text(text, max_chars=self._chunk_size)
            for chunk_str in chunks:
                section = chunk_str.split("\n")[0].strip()[:80]
                results.append(
                    SourceChunk(
                        text=chunk_str,
                        source=url,
                        section=section,
                        metadata={
                            "source_url": url,
                            "url": url,
                        },
                    )
                )

            self._content_cache[url] = text

        return results[:limit]

    def list_topics(self) -> list[str]:
        """返回已配置的 URL 列表。"""
        return list(self._urls)

    def refresh(self) -> int:
        """重新抓取所有 URL，返回新增块数。

        首次调用视为全量抓取，返回 0（无增量基准）。
        """
        if not self._requests_available or not self._bs4_available:
            return 0

        if not self._connected:
            if not self.connect():
                return 0

        old_count = len(self._content_cache)
        chunks = self.fetch("", limit=10_000)
        new_count = len(chunks) if old_count > 0 else 0
        logger.info(
            "WebConnector '%s': refresh 完成，之前 %d 个 URL 缓存，本次 %d 个 chunk",
            self._name,
            old_count,
            new_count,
        )
        return new_count
