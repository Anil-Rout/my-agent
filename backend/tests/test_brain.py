from brain import agent as agent_module


def test_split_task_steps():
    steps = agent_module.split_task_steps(
        "create folder named demo and open it then list files"
    )

    assert steps == [
        "create folder named demo",
        "open it",
        "list files",
    ]


def test_execute_multi_step_task_uses_folder_context(monkeypatch):
    calls = []

    def fake_run_direct_action(user_input, session_id, session_context=None):
        calls.append(user_input)

        if user_input == "create folder named demo":
            session_context["last_folder_path"] = r"C:\Temp\demo"
            session_context["last_folder_name"] = "demo"
            return "Folder 'demo' created successfully."

        if user_input == r"open folder C:\Temp\demo":
            return r"Opened folder: C:\Temp\demo"

        return None

    monkeypatch.setattr(agent_module, "run_direct_action", fake_run_direct_action)
    agent_module.SESSION_CONTEXTS.clear()

    result = agent_module.execute_multi_step_task(
        "create folder named demo and open it",
        "session-test",
    )

    assert "Step 1: Folder 'demo' created successfully." in result
    assert r"Step 2: Opened folder: C:\Temp\demo" in result
    assert calls == ["create folder named demo", r"open folder C:\Temp\demo"]


def test_resolve_contextual_step_uses_last_file():
    step = agent_module.resolve_contextual_step(
        "run it",
        {
            "last_folder_path": r"C:\Temp\demo",
            "last_folder_name": "demo",
            "last_file_path": r"C:\Temp\demo\main.py",
        },
    )

    assert step == r"run file C:\Temp\demo\main.py"
