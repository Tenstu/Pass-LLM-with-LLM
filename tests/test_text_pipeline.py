"""tests/test_text_pipeline.py — GitHubConnector + WebConnector 单元测试。"""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from exam_memory.knowledge_source import SourceChunk
from exam_memory.text_pipeline import (
    GitHubConnector,
    WebConnector,
)


# ── 辅助函数 ────────────────────────────────────────────────────


def _make_mock_file(path: str, content: str, size: int = None):
    """构造模拟 PyGithub ContentFile。content 为 str，自动编码为 bytes。"""
    content_bytes = content.encode("utf-8")
    mock_file = MagicMock()
    mock_file.type = "file"
    mock_file.path = path
    mock_file.size = size if size is not None else len(content_bytes)
    mock_file.decoded_content = content_bytes
    mock_file.html_url = f"https://github.com/owner/repo/blob/main/{path}"
    return mock_file


def _make_connected_github(monkeypatch, files: dict[str, str]):
    """创建一个已连接的 GitHubConnector，mock get_contents 返回 files。

    files: {path: content_str} — 内容为 Python 字符串（自动编码为 bytes）。
    直接设置 _github_available 和 _gh_client 以绕过导入检查。
    """
    import exam_memory.text_pipeline as tp

    mock_repo = MagicMock()

    def make_contents(path, ref="main"):
        result = []
        for fpath, content in files.items():
            if path in ("", "/") and "/" not in fpath:
                result.append(_make_mock_file(fpath, content))
            elif fpath.startswith(path.rstrip("/") + "/") and fpath != path:
                rel = fpath[len(path.rstrip("/")) + 1 :]
                if "/" not in rel:
                    result.append(_make_mock_file(fpath, content))
        return result

    mock_repo.get_contents.side_effect = make_contents
    mock_client = MagicMock()
    mock_client.get_repo.return_value = mock_repo

    # Mock the Github class so connect() succeeds
    mock_github_cls = MagicMock(return_value=mock_client)
    monkeypatch.setattr(tp, "Github", mock_github_cls)

    gh = GitHubConnector(name="test", repo="owner/repo")
    # Override the captured _github_available flag directly
    gh._github_available = True
    gh.connect()
    return gh


# ── GitHubConnector — 无依赖降级 ─────────────────────────────────


class TestGitHubConnectorNoPyGithub:
    def test_connect_returns_false_without_pygithub(self, monkeypatch) -> None:
        """无 PyGithub 时 connect() 返回 False。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_GITHUB_AVAILABLE", False)
        monkeypatch.setattr(tp, "Github", None)

        gh = GitHubConnector(name="test", repo="owner/repo")
        assert gh.connect() is False
        assert gh.connected is False

    def test_fetch_returns_empty_without_pygithub(self, monkeypatch) -> None:
        """无 PyGithub 时 fetch() 返回空列表。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_GITHUB_AVAILABLE", False)
        monkeypatch.setattr(tp, "Github", None)

        gh = GitHubConnector(name="test", repo="owner/repo")
        assert gh.fetch("哈希表") == []


# ── GitHubConnector — connect() ─────────────────────────────────


class TestGitHubConnectorConnect:
    def test_connect_success(self, monkeypatch) -> None:
        """有效 repo 时 connect() 返回 True。"""
        import exam_memory.text_pipeline as tp

        mock_client = MagicMock()
        mock_client.get_repo.return_value = MagicMock()
        mock_cls = MagicMock(return_value=mock_client)
        monkeypatch.setattr(tp, "Github", mock_cls)

        gh = GitHubConnector(name="test", repo="owner/repo", token_env="MY_TOKEN")
        gh._github_available = True
        with patch.dict(os.environ, {"MY_TOKEN": "fake_token"}, clear=False):
            result = gh.connect()

        assert result is True
        assert gh.connected is True
        mock_cls.assert_called_once_with(login_or_token="fake_token")

    def test_connect_no_token(self, monkeypatch) -> None:
        """无 token env 时以 None 调用 Github()。"""
        import exam_memory.text_pipeline as tp

        mock_client = MagicMock()
        mock_client.get_repo.return_value = MagicMock()
        mock_cls = MagicMock(return_value=mock_client)
        monkeypatch.setattr(tp, "Github", mock_cls)

        gh = GitHubConnector(name="test", repo="owner/repo", token_env="MISSING_TOKEN")
        gh._github_available = True
        with patch.dict(os.environ, {}, clear=True):
            result = gh.connect()

        assert result is True
        mock_cls.assert_called_once_with(login_or_token=None)

    def test_connect_repo_not_found(self, monkeypatch) -> None:
        """仓库不存在时 connect() 返回 False。"""
        import exam_memory.text_pipeline as tp

        mock_client = MagicMock()
        mock_client.get_repo.side_effect = Exception("Not Found")
        monkeypatch.setattr(tp, "Github", MagicMock(return_value=mock_client))

        gh = GitHubConnector(name="test", repo="owner/nonexistent")
        gh._github_available = True
        assert gh.connect() is False
        assert gh.connected is False

    def test_connect_bad_credentials(self, monkeypatch) -> None:
        """token 无效时 connect() 返回 False。"""
        import exam_memory.text_pipeline as tp

        mock_client = MagicMock()
        mock_client.get_repo.side_effect = Exception("Bad credentials")
        monkeypatch.setattr(tp, "Github", MagicMock(return_value=mock_client))

        gh = GitHubConnector(name="test", repo="owner/repo")
        gh._github_available = True
        assert gh.connect() is False

    def test_fetch_returns_empty_when_not_connected(self, monkeypatch) -> None:
        """未连接时 fetch() 返回空列表。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_GITHUB_AVAILABLE", True)
        monkeypatch.setattr(tp, "Github", MagicMock)

        gh = GitHubConnector(name="test", repo="owner/repo")
        gh._github_available = True
        assert gh.connected is False
        assert gh.fetch("哈希表") == []


# ── GitHubConnector — fetch() ───────────────────────────────────


class TestGitHubConnectorFetch:
    def test_fetch_keyword_match_in_filename(self, monkeypatch) -> None:
        """fetch() 按文件名关键词匹配。"""
        files = {
            "哈希表.md": "# 哈希表\nO(1) 查找",
            "排序.md": "# 排序\n快速排序 O(n log n)",
        }
        gh = _make_connected_github(monkeypatch, files)

        chunks = gh.fetch("哈希表")
        assert len(chunks) > 0
        for c in chunks:
            assert isinstance(c, dict)
            assert "text" in c
            assert "source" in c

    def test_fetch_keyword_match_in_content(self, monkeypatch) -> None:
        """fetch() 按内容关键词匹配。"""
        files = {
            "README.md": "# Project\n\n哈希表 is O(1).",
        }
        gh = _make_connected_github(monkeypatch, files)

        chunks = gh.fetch("哈希表")
        assert len(chunks) > 0

    def test_fetch_no_match_returns_empty(self, monkeypatch) -> None:
        """无匹配时 fetch() 返回空列表。"""
        files = {
            "README.md": "# Project\n\nSome unrelated content.",
            "sort.md": "Sorting algorithms.",
        }
        gh = _make_connected_github(monkeypatch, files)

        assert gh.fetch("哈希表") == []

    def test_fetch_limit_respected(self, monkeypatch) -> None:
        """fetch() limit 参数限制返回数量。"""
        long_content = "# 哈希表\n" + ("哈希表相关内容 " * 200)
        files = {"hash.md": long_content}
        gh = _make_connected_github(monkeypatch, files)

        chunks = gh.fetch("哈希表", limit=3)
        assert len(chunks) <= 3

    def test_fetch_returns_sourcechunk_structure(self, monkeypatch) -> None:
        """fetch() 返回的 SourceChunk 具有正确字段。"""
        files = {"哈希表.md": "# 哈希表\nO(1) 查找"}
        gh = _make_connected_github(monkeypatch, files)

        chunks = gh.fetch("哈希表")
        assert len(chunks) >= 1
        c = chunks[0]
        assert "text" in c
        assert "source" in c
        assert "section" in c
        assert "metadata" in c
        assert "source_url" in c["metadata"]
        assert c["metadata"]["repo"] == "owner/repo"
        assert c["metadata"]["branch"] == "main"


# ── GitHubConnector — list_topics() ─────────────────────────────


class TestGitHubConnectorListTopics:
    def test_list_topics_returns_paths_without_extension(self, monkeypatch) -> None:
        """list_topics() 返回去扩展名的路径尾部。"""
        files = {
            "README.md": "# README",
            "docs.md": "# docs",
        }
        gh = _make_connected_github(monkeypatch, files)
        gh.fetch("")

        topics = gh.list_topics()
        assert "README" in topics
        assert "docs" in topics
        assert not any(t.endswith(".md") for t in topics)

    def test_list_topics_empty_before_fetch(self, monkeypatch) -> None:
        """fetch 之前 list_topics() 返回空。"""
        files = {"哈希表.md": "# 哈希表"}
        gh = _make_connected_github(monkeypatch, files)
        # 不调用 fetch
        assert gh.list_topics() == []


# ── GitHubConnector — refresh() ─────────────────────────────────


class TestGitHubConnectorRefresh:
    def test_refresh_when_not_connected(self, monkeypatch) -> None:
        """未连接时 refresh() 返回 0。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_GITHUB_AVAILABLE", False)
        monkeypatch.setattr(tp, "Github", None)

        gh = GitHubConnector(name="test", repo="owner/repo")
        assert gh.refresh() == 0


# ── WebConnector — 无依赖降级 ───────────────────────────────────


class TestWebConnectorNoDeps:
    def test_connect_returns_false_without_requests(self, monkeypatch) -> None:
        """无 requests 时 connect() 返回 False。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_REQUESTS_AVAILABLE", False)
        monkeypatch.setattr(tp, "_requests", None)

        web = WebConnector(name="test", urls=["https://example.com"])
        assert web.connect() is False
        assert web.connected is False

    def test_fetch_returns_empty_without_requests(self, monkeypatch) -> None:
        """无 requests 时 fetch() 返回空列表。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_REQUESTS_AVAILABLE", False)
        monkeypatch.setattr(tp, "_requests", None)
        monkeypatch.setattr(tp, "_BS4_AVAILABLE", False)

        web = WebConnector(name="test", urls=["https://example.com"])
        assert web.fetch("哈希表") == []

    def test_fetch_returns_empty_without_bs4(self, monkeypatch) -> None:
        """有 requests 但无 bs4 时 fetch() 返回空列表。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_REQUESTS_AVAILABLE", True)
        monkeypatch.setattr(tp, "_BS4_AVAILABLE", False)
        monkeypatch.setattr(tp, "BeautifulSoup", None)

        web = WebConnector(name="test", urls=["https://example.com"])
        assert web.fetch("哈希表") == []


# ── WebConnector — connect() ────────────────────────────────────


class TestWebConnectorConnect:
    def test_connect_all_urls_reachable(self, monkeypatch) -> None:
        """所有 URL 可达时 connect() 返回 True。"""
        import exam_memory.text_pipeline as tp

        mock_head = MagicMock(return_value=MagicMock(status_code=200))
        monkeypatch.setattr(tp, "_requests", MagicMock(head=mock_head))

        web = WebConnector(name="test", urls=["https://a.com", "https://b.com"])
        assert web.connect() is True
        assert web.connected is True

    def test_connect_partial_failure(self, monkeypatch) -> None:
        """部分 URL 失败时，至少一个可达则 connect() 返回 True。"""
        import exam_memory.text_pipeline as tp

        call_count = [0]

        def mock_head(url, **kwargs):
            call_count[0] += 1
            resp = MagicMock()
            resp.status_code = 200 if call_count[0] == 1 else 500
            return resp

        monkeypatch.setattr(
            tp, "_requests", MagicMock(head=MagicMock(side_effect=mock_head))
        )

        web = WebConnector(name="test", urls=["https://ok.com", "https://fail.com"])
        assert web.connect() is True

    def test_connect_all_fail(self, monkeypatch) -> None:
        """所有 URL 失败时 connect() 返回 False。"""
        import exam_memory.text_pipeline as tp

        mock_head = MagicMock(side_effect=Exception("Connection refused"))
        monkeypatch.setattr(
            tp, "_requests", MagicMock(head=mock_head)
        )

        web = WebConnector(name="test", urls=["https://example.com"])
        assert web.connect() is False
        assert web.connected is False

    def test_connect_no_urls(self, monkeypatch) -> None:
        """空 URL 列表时 connect() 返回 False。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_REQUESTS_AVAILABLE", True)

        web = WebConnector(name="test", urls=[])
        assert web.connect() is False

    def test_fetch_returns_empty_when_not_connected(self, monkeypatch) -> None:
        """未连接时 fetch() 返回空列表。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_REQUESTS_AVAILABLE", False)
        monkeypatch.setattr(tp, "_requests", None)

        web = WebConnector(name="test", urls=["https://example.com"])
        assert web.connected is False
        assert web.fetch("topic") == []


# ── WebConnector — fetch() ──────────────────────────────────────


class TestWebConnectorFetch:
    def test_fetch_keyword_match_in_content(self, monkeypatch) -> None:
        """fetch() 按内容关键词匹配。"""
        import exam_memory.text_pipeline as tp

        html = "<html><body><p>哈希表是一种 O(1) 查找数据结构。</p></body></html>"

        def mock_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            resp.text = html
            return resp

        monkeypatch.setattr(
            tp, "_requests", MagicMock(get=MagicMock(side_effect=mock_get))
        )

        def mock_bs4(html_str, parser):
            soup = MagicMock()
            soup.get_text = MagicMock(return_value="哈希表是一种 O(1) 查找数据结构。")
            soup.find = MagicMock(return_value=None)
            return soup

        monkeypatch.setattr(tp, "BeautifulSoup", mock_bs4)

        web = WebConnector(name="test", urls=["https://example.com"])
        web.connect()

        chunks = web.fetch("哈希表")
        assert len(chunks) > 0
        assert any("哈希表" in c["text"] for c in chunks)

    def test_fetch_no_match_returns_empty(self, monkeypatch) -> None:
        """topic 不在页面中时 fetch() 返回空列表。"""
        import exam_memory.text_pipeline as tp

        html = "<html><body><p>排序算法相关内容。</p></body></html>"

        def mock_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            resp.text = html
            return resp

        monkeypatch.setattr(
            tp, "_requests", MagicMock(get=MagicMock(side_effect=mock_get))
        )

        def mock_bs4(html_str, parser):
            soup = MagicMock()
            soup.get_text = MagicMock(return_value="排序算法相关内容。")
            soup.find = MagicMock(return_value=None)
            return soup

        monkeypatch.setattr(tp, "BeautifulSoup", mock_bs4)

        web = WebConnector(name="test", urls=["https://example.com"])
        web.connect()

        assert web.fetch("哈希表") == []

    def test_fetch_returns_sourcechunk_structure(self, monkeypatch) -> None:
        """fetch() 返回 SourceChunk 结构。"""
        import exam_memory.text_pipeline as tp

        html = "<html><body><main><p>哈希表 O(1) 查找</p></main></body></html>"

        def mock_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            resp.text = html
            return resp

        monkeypatch.setattr(
            tp, "_requests", MagicMock(get=MagicMock(side_effect=mock_get))
        )

        def mock_bs4(html_str, parser):
            soup = MagicMock()
            main_tag = MagicMock()
            main_tag.get_text = MagicMock(return_value="哈希表 O(1) 查找")
            soup.find = MagicMock(return_value=main_tag)
            soup.get_text = MagicMock(return_value="sidebar nav")
            return soup

        monkeypatch.setattr(tp, "BeautifulSoup", mock_bs4)

        web = WebConnector(name="test", urls=["https://example.com"])
        web.connect()

        chunks = web.fetch("哈希表")
        assert len(chunks) >= 1
        c = chunks[0]
        assert "text" in c
        assert "source" in c
        assert "section" in c
        assert "metadata" in c
        assert c["metadata"]["source_url"] == "https://example.com"

    def test_fetch_limit_respected(self, monkeypatch) -> None:
        """fetch() limit 参数限制返回数量。"""
        import exam_memory.text_pipeline as tp

        long_text = "哈希表 " * 500

        def mock_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            resp.text = f"<p>{long_text}</p>"
            return resp

        monkeypatch.setattr(
            tp, "_requests", MagicMock(get=MagicMock(side_effect=mock_get))
        )

        def mock_bs4(html_str, parser):
            soup = MagicMock()
            soup.get_text = MagicMock(return_value=long_text)
            soup.find = MagicMock(return_value=None)
            return soup

        monkeypatch.setattr(tp, "BeautifulSoup", mock_bs4)

        web = WebConnector(name="test", urls=["https://example.com"])
        web.connect()

        chunks = web.fetch("哈希表", limit=2)
        assert len(chunks) <= 2

    def test_fetch_multiple_urls(self, monkeypatch) -> None:
        """fetch() 遍历所有 URL 收集结果。"""
        import exam_memory.text_pipeline as tp

        def mock_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            resp.text = "<p>哈希表内容</p>"
            return resp

        monkeypatch.setattr(
            tp, "_requests", MagicMock(get=MagicMock(side_effect=mock_get))
        )

        def mock_bs4(html_str, parser):
            soup = MagicMock()
            soup.get_text = MagicMock(return_value="哈希表内容")
            soup.find = MagicMock(return_value=None)
            return soup

        monkeypatch.setattr(tp, "BeautifulSoup", mock_bs4)

        web = WebConnector(
            name="test", urls=["https://a.com", "https://b.com"]
        )
        web.connect()

        chunks = web.fetch("哈希表")
        assert len(chunks) > 0

    def test_fetch_skips_urls_with_errors(self, monkeypatch) -> None:
        """fetch() 跳过请求失败的 URL，继续处理其他 URL。"""
        import exam_memory.text_pipeline as tp

        call_count = [0]

        def mock_get(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Network error")
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            resp.text = "<p>哈希表内容</p>"
            return resp

        monkeypatch.setattr(
            tp, "_requests", MagicMock(get=MagicMock(side_effect=mock_get))
        )

        def mock_bs4(html_str, parser):
            soup = MagicMock()
            soup.get_text = MagicMock(return_value="哈希表内容")
            soup.find = MagicMock(return_value=None)
            return soup

        monkeypatch.setattr(tp, "BeautifulSoup", mock_bs4)

        web = WebConnector(
            name="test", urls=["https://fail.com", "https://ok.com"]
        )
        web.connect()

        chunks = web.fetch("哈希表")
        # 应该从第二个 URL 获取到内容
        assert len(chunks) > 0


# ── WebConnector — main/article 优先 ────────────────────────────


class TestWebConnectorMainTag:
    def test_fetch_uses_main_tag_text(self, monkeypatch) -> None:
        """fetch() 优先使用 <main> 标签内的文本。"""
        import exam_memory.text_pipeline as tp

        main_text = "哈希表 O(1) 查找数据"
        sidebar_text = "导航栏 广告 无关内容"

        def mock_get(url, **kwargs):
            resp = MagicMock()
            resp.status_code = 200
            resp.raise_for_status = MagicMock()
            resp.text = (
                f"<html><body>"
                f"<nav>{sidebar_text}</nav>"
                f"<main>{main_text}</main>"
                f"</body></html>"
            )
            return resp

        monkeypatch.setattr(
            tp, "_requests", MagicMock(get=MagicMock(side_effect=mock_get))
        )

        main_tag_mock = MagicMock()
        main_tag_mock.get_text = MagicMock(return_value=main_text)

        def mock_bs4(html_str, parser):
            soup = MagicMock()
            # 第二次调用（get_text）应该返回 sidebar
            soup.find = MagicMock(return_value=main_tag_mock)
            soup.get_text = MagicMock(return_value=sidebar_text)
            return soup

        monkeypatch.setattr(tp, "BeautifulSoup", mock_bs4)

        web = WebConnector(name="test", urls=["https://example.com"])
        web.connect()

        chunks = web.fetch("哈希表")
        assert len(chunks) > 0
        # find 被调用寻找 <main>
        assert chunks[0]["text"].startswith("哈希表") or "哈希表" in chunks[0]["text"]


# ── WebConnector — list_topics() ────────────────────────────────


class TestWebConnectorListTopics:
    def test_list_topics_returns_urls(self, monkeypatch) -> None:
        """list_topics() 返回已配置的 URL 列表。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_REQUESTS_AVAILABLE", False)
        monkeypatch.setattr(tp, "_requests", None)

        urls = ["https://a.com", "https://b.com"]
        web = WebConnector(name="test", urls=urls)
        assert web.list_topics() == urls

    def test_list_topics_empty(self, monkeypatch) -> None:
        """空 URL 列表的 list_topics() 返回空列表。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_REQUESTS_AVAILABLE", False)
        monkeypatch.setattr(tp, "_requests", None)

        web = WebConnector(name="test", urls=[])
        assert web.list_topics() == []


# ── WebConnector — refresh() ────────────────────────────────────


class TestWebConnectorRefresh:
    def test_refresh_when_not_connected(self, monkeypatch) -> None:
        """未连接时 refresh() 返回 0。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_REQUESTS_AVAILABLE", False)
        monkeypatch.setattr(tp, "_requests", None)

        web = WebConnector(name="test", urls=["https://example.com"])
        assert web.refresh() == 0


# ── Protocol 一致性 ─────────────────────────────────────────────


class TestProtocolConsistency:
    def test_github_has_protocol_members(self, monkeypatch) -> None:
        """GitHubConnector 具有所有 Protocol 成员。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_GITHUB_AVAILABLE", False)
        monkeypatch.setattr(tp, "Github", None)

        gh = GitHubConnector(name="test", repo="owner/repo")
        assert gh.source_type == "github"
        assert callable(gh.connect)
        assert callable(gh.fetch)
        assert callable(gh.list_topics)
        assert callable(gh.refresh)

    def test_web_has_protocol_members(self, monkeypatch) -> None:
        """WebConnector 具有所有 Protocol 成员。"""
        import exam_memory.text_pipeline as tp

        monkeypatch.setattr(tp, "_REQUESTS_AVAILABLE", False)
        monkeypatch.setattr(tp, "_requests", None)

        web = WebConnector(name="test", urls=["https://example.com"])
        assert web.source_type == "web"
        assert callable(web.connect)
        assert callable(web.fetch)
        assert callable(web.list_topics)
        assert callable(web.refresh)

    def test_github_source_type(self) -> None:
        """GitHubConnector.source_type 返回 'github'。"""
        gh = GitHubConnector(name="test", repo="owner/repo")
        assert gh.source_type == "github"

    def test_web_source_type(self) -> None:
        """WebConnector.source_type 返回 'web'。"""
        web = WebConnector(name="test", urls=["https://example.com"])
        assert web.source_type == "web"

    def test_github_name_property(self) -> None:
        """GitHubConnector.name 返回构造时传入的名称。"""
        gh = GitHubConnector(name="myrepo", repo="owner/repo")
        assert gh.name == "myrepo"

    def test_web_name_property(self) -> None:
        """WebConnector.name 返回构造时传入的名称。"""
        web = WebConnector(name="mydocs", urls=["https://example.com"])
        assert web.name == "mydocs"
