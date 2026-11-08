"""第3回 宿題（実装）: save_learning_log と承認フローのテスト（LLMもAPIキーも使わない）。"""

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import FunctionModel

from app import tools
from app.agent import agent, run_with_approval


def test_save_learning_log_writes_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")
    message = tools.save_learning_log("LoRA/QLoRA の違い", "- LoRA は低ランク行列だけを学習する")
    files = list((tmp_path / "learning_log").glob("*.md"))
    assert len(files) == 1 and "保存しました" in message
    text = files[0].read_text(encoding="utf-8")
    assert text.startswith("# LoRA/QLoRA の違い") and "低ランク行列" in text
    assert "/" not in files[0].name.split("_", 1)[1]  # ファイル名に使えない文字は置き換える


def test_save_learning_log_rejects_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")
    assert "保存していません" in tools.save_learning_log("", "")
    assert not (tmp_path / "learning_log").exists()


def _model_that_saves(messages, info):
    """1回目は save_learning_log を呼び、ツールの結果が返ってきたらその内容を答える偽モデル。"""
    last = messages[-1].parts[-1]
    if isinstance(last, ToolReturnPart):
        return ModelResponse(parts=[TextPart(f"結果: {last.content}")])
    return ModelResponse(parts=[ToolCallPart("save_learning_log", {"title": "テスト", "content": "- 要点"})])


def test_run_stops_for_approval_before_saving(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")
    result = agent.run_sync("記録して", model=FunctionModel(_model_that_saves))
    assert isinstance(result.output, DeferredToolRequests)
    assert [c.tool_name for c in result.output.approvals] == ["save_learning_log"]
    assert not (tmp_path / "learning_log").exists()  # 承認前なので、まだ保存されていない


def test_approved_call_saves(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")
    result = run_with_approval(agent, "記録して", FunctionModel(_model_that_saves), answer=lambda _: "y")
    assert "保存しました" in result.output
    assert len(list((tmp_path / "learning_log").glob("*.md"))) == 1


def test_denied_call_does_not_save(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "LOG_DIR", tmp_path / "learning_log")
    result = run_with_approval(agent, "記録して", FunctionModel(_model_that_saves), answer=lambda _: "n")
    assert "許可しませんでした" in result.output
    assert not (tmp_path / "learning_log").exists()


def test_make_quiz_handles_missing_lecture():
    assert "ありません" in tools.make_quiz(0)
    assert "question" in tools.make_quiz(2)
