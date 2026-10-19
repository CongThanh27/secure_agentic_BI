"""First LLM call: natural language to one SQL tool call."""

import json
from typing import Optional

import streamlit as st

from .llm import call_llm_with_fallback
from .prompts import planner_prompt


def plan_query(user_prompt: str, active_model: str) -> Optional[dict]:
    try:
        full_prompt = planner_prompt() + "\n\nUser Request: " + user_prompt
        raw_text, used_model = call_llm_with_fallback(full_prompt, active_model)
        raw_text = raw_text.replace("```json", "").replace("```", "").strip()
        result_json = json.loads(raw_text)
        result_json["model_used"] = used_model
        return result_json
    except Exception as e:
        st.error(f"Lỗi Routing: {str(e)}")
        return None
