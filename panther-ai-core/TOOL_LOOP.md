# Panther AI Tool Orchestration

Panther AI Core currently has an explicit tool registry and a local llama.cpp model adapter.

Next integration stage: the engine must safely mediate model decisions and tool execution rather than allowing the model to execute host commands directly.

The model may propose a registered tool and arguments; Panther validates the tool name and executes only through `run_tool`.
