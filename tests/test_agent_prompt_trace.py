from __future__ import annotations

from contextlib import contextmanager

from app import agent as agent_module


class RecordingObservation:
    def __init__(self, observation: dict) -> None:
        self.observation = observation

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        return False

    def update(self, **kwargs) -> None:
        self.observation["updates"] = kwargs


class ManagedPrompt:
    version = 3

    def compile(self, **variables: str) -> str:
        return (
            f"Feature={variables['feature']}\n"
            f"Docs={variables['docs']}\n"
            f"Question={variables['message']}"
        )


class RecordingLangfuseClient:
    def __init__(self) -> None:
        self.prompt = ManagedPrompt()
        self.span_updates: list[dict] = []
        self.observations: list[dict] = []

    def get_prompt(self, name: str, **kwargs):
        return self.prompt

    def update_current_span(self, **kwargs) -> None:
        self.span_updates.append(kwargs)

    def start_as_current_observation(self, **kwargs):
        observation = dict(kwargs)
        self.observations.append(observation)
        return RecordingObservation(observation)


def test_agent_records_prompt_version_with_v4_observation_api(monkeypatch) -> None:
    monkeypatch.setenv("LANGFUSE_PROMPT_NAME", "day13-chat")
    monkeypatch.setenv("LANGFUSE_PROMPT_LABEL", "production")
    client = RecordingLangfuseClient()
    monkeypatch.setattr(agent_module, "get_langfuse_client", lambda: client)
    monkeypatch.setattr(agent_module, "tracing_enabled", lambda: True)

    propagated: list[dict] = []

    @contextmanager
    def record_attributes(**kwargs):
        propagated.append(kwargs)
        yield

    monkeypatch.setattr(agent_module, "propagate_attributes", record_attributes)

    agent = agent_module.LabAgent()
    agent_module.LabAgent.run.__wrapped__(
        agent,
        user_id="student-01",
        feature="qa",
        session_id="session-01",
        message="Contact student@vinuni.edu.vn about traces",
        correlation_id="req-12345678",
    )

    span_update = client.span_updates[-1]
    assert span_update["metadata"] == {
        "doc_count": 1,
        "query_preview": "Contact [REDACTED_EMAIL] about traces",
        "prompt_name": "day13-chat",
        "prompt_label": "production",
        "prompt_version": "3",
        "prompt_source": "langfuse",
        "prompt_fetch_error": "",
    }
    assert span_update["version"] == "3"
    assert propagated[0]["metadata"]["correlation_id"] == "req-12345678"
    assert propagated[-1]["prompt"] is client.prompt

    retrieval, generation = client.observations
    assert (retrieval["as_type"], generation["as_type"]) == (
        "retriever",
        "generation",
    )
    assert retrieval["input"]["query_preview"].endswith("[REDACTED_EMAIL] about traces")
    assert "student@vinuni.edu.vn" not in str(client.observations)
    assert generation["model"] == "claude-sonnet-4-5"
    assert generation["prompt"] is client.prompt
    assert generation["updates"]["usage_details"]["total"] == (
        generation["updates"]["usage_details"]["input"]
        + generation["updates"]["usage_details"]["output"]
    )
    assert generation["updates"]["cost_details"]["total"] > 0
    assert "output_preview" not in generation["updates"]
