"""agent.controller.state_machine

状态机实现（核心）

对应 `AGET-TECH_MVP.md` 第 5 节。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Optional

from agent.exceptions import StateMachineException


class State(str, Enum):
    IDLE = "IDLE"
    RECEIVED_TASK = "RECEIVED_TASK"
    SEARCHING = "SEARCHING"
    FILTERING = "FILTERING"
    EXTRACTING = "EXTRACTING"
    FINISHED = "FINISHED"
    ABORTED = "ABORTED"


@dataclass(frozen=True)
class StateTransition:
    from_state: State
    to_state: State
    at: datetime


StateCallback = Callable[[State], None]


class StateMachine:
    """有限状态机：约束执行流程，支持回调与历史记录。"""

    TRANSITIONS: Dict[State, List[State]] = {
        State.IDLE: [State.RECEIVED_TASK, State.ABORTED],  # Allow abort from IDLE
        State.RECEIVED_TASK: [State.SEARCHING, State.ABORTED],  # Allow abort from RECEIVED_TASK
        State.SEARCHING: [State.FILTERING, State.FINISHED, State.ABORTED],  # Allow early exit when no items found
        State.FILTERING: [State.EXTRACTING, State.FINISHED, State.ABORTED],  # Allow early exit when no relevant items
        State.EXTRACTING: [State.FINISHED, State.ABORTED],
        State.FINISHED: [],
        State.ABORTED: [],
    }

    def __init__(self, initial_state: State = State.IDLE):
        self._state: State = initial_state
        self._history: List[StateTransition] = []
        self._callbacks: Dict[State, List[StateCallback]] = {}

    @property
    def current_state(self) -> State:
        return self._state

    @property
    def history(self) -> List[StateTransition]:
        return list(self._history)

    def can_transition_to(self, new_state: State) -> bool:
        return new_state in self.TRANSITIONS.get(self._state, [])

    def register_callback(self, state: State, callback: StateCallback) -> None:
        """注册回调：当进入指定 state 时触发。"""
        self._callbacks.setdefault(state, []).append(callback)

    def transition_to(self, new_state: State) -> None:
        """执行状态转换（非法转换会抛异常）。"""
        # #region debug log
        import json
        import time
        can_transition = self.can_transition_to(new_state)
        allowed = [s.value for s in self.TRANSITIONS.get(self._state, [])]
        try:
            with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run2",
                    "hypothesisId": "A",
                    "location": "state_machine.py:71",
                    "message": "State transition attempt",
                    "data": {
                        "currentState": self._state.value,
                        "targetState": new_state.value,
                        "canTransition": can_transition,
                        "allowedTransitions": allowed,
                        "transitionsDict": {k.value: [s.value for s in v] for k, v in self.TRANSITIONS.items()}
                    },
                    "timestamp": int(time.time() * 1000)
                }) + '\n')
        except Exception:
            pass
        # #endregion
        
        if not can_transition:
            # #region debug log
            try:
                with open('/Users/bing/Documents/AI-AD/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run2",
                        "hypothesisId": "A",
                        "location": "state_machine.py:95",
                        "message": "State transition FAILED",
                        "data": {
                            "currentState": self._state.value,
                            "targetState": new_state.value,
                            "allowedTransitions": allowed
                        },
                        "timestamp": int(time.time() * 1000)
                    }) + '\n')
            except Exception:
                pass
            # #endregion
            raise StateMachineException(
                f"Invalid transition: {self._state} -> {new_state}",
                current_state=self._state.value,
                target_state=new_state.value,
            )

        prev = self._state
        self._state = new_state
        self._history.append(StateTransition(from_state=prev, to_state=new_state, at=datetime.now()))

        for cb in self._callbacks.get(new_state, []):
            cb(new_state)

    def reset(self, state: State = State.IDLE, clear_history: bool = True) -> None:
        """重置状态机（用于新任务或测试）。"""
        self._state = state
        if clear_history:
            self._history.clear()

    def progress(self) -> int:
        """粗粒度进度，用于 STATUS_UPDATE（可根据需要调整）。"""
        mapping = {
            State.IDLE: 0,
            State.RECEIVED_TASK: 10,
            State.SEARCHING: 30,
            State.FILTERING: 50,
            State.EXTRACTING: 70,
            State.FINISHED: 100,
            State.ABORTED: 0,
        }
        return mapping.get(self._state, 0)
