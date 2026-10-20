"""Тести циклу агента без звернень до API (МВ 4.16, вимоги 9-10, 18)."""

from agent.loop import run_agent


def scripted(decisions):
    queue = iter(decisions)

    def decide(goal, observations, step, max_steps):
        return next(queue)

    return decide


def test_lookup_then_finish():
    decide = scripted([
        {
            "action": "lookup_http_status",
            "arguments": {"code": "401"},
            "decision_summary": "Need verified info on 401.",
        },
        {
            "action": "finish",
            "arguments": {"answer": "401 вимагає автентифікації."},
            "decision_summary": "Data obtained.",
        },
    ])
    state = run_agent("Що таке 401?", decide=decide)
    assert state.stop_reason == "finish"
    assert state.llm_calls == 2
    assert state.observations[0].startswith("401:")
    assert "автентифікації" in (state.final_answer or "")


def test_stops_at_max_steps():
    def endless(goal, observations, step, max_steps):
        return {
            "action": "lookup_http_status",
            "arguments": {"code": "200"},
            "decision_summary": "Looping forever.",
        }

    state = run_agent("Тест нескінченного циклу", decide=endless, max_steps=4)
    assert state.stop_reason == "max_steps"
    assert state.step == 4
    assert state.finished is True
    assert "вичерпано ліміт кроків (4)" in (state.final_answer or "")


def test_stops_at_max_llm_calls():
    def endless(goal, observations, step, max_steps):
        return {
            "action": "lookup_http_status",
            "arguments": {"code": "200"},
            "decision_summary": "Exhausting llm calls.",
        }

    state = run_agent("Тест ліміту викликів", decide=endless, max_steps=10, max_llm_calls=3)
    assert state.stop_reason == "max_llm_calls"
    assert state.llm_calls == 3
    assert state.finished is True


def test_rejected_action_becomes_observation_and_recovers():
    decide = scripted([
        {
            "action": "unknown_action_xyz",
            "arguments": {},
            "decision_summary": "Invalid action attempt.",
        },
        {
            "action": "lookup_http_status",
            "arguments": {"code": "404"},
            "decision_summary": "Fixed action after error.",
        },
        {
            "action": "finish",
            "arguments": {"answer": "404 означає Not Found."},
            "decision_summary": "Finished successfully.",
        },
    ])
    state = run_agent("Помилка і виправлення", decide=decide)
    assert state.stop_reason == "finish"
    assert state.step == 3
    assert state.trace[0]["action"] == "rejected"
    assert "ERROR: unknown action" in state.observations[0]
    assert state.observations[1].startswith("404:")
