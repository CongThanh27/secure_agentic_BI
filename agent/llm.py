"""Gemini calls with model fallback."""

import os

import google.generativeai as genai
import streamlit as st
from google.api_core.exceptions import ResourceExhausted
from google.generativeai.types import HarmBlockThreshold, HarmCategory

GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY", "AIzaSyA7dp-r-MM6WMY_vwGaLZn7upy5KuFTANM"
)
genai.configure(api_key=GEMINI_API_KEY)

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

AVAILABLE_MODELS = [
    "models/gemini-3.5-flash-lite",
    "models/gemini-3.1-flash-lite",
    "models/gemini-3.6-flash",
    "models/gemini-3.5-flash",
    "models/gemini-2.5-flash",
    "models/gemma-4-26b-a4b-it",
]


def call_llm_with_fallback(prompt: str, primary_model: str) -> tuple[str, str]:
    """Call the preferred model, then the rest of AVAILABLE_MODELS on HTTP 429."""
    test_list = [primary_model] + [m for m in AVAILABLE_MODELS if m != primary_model]

    for model_name in test_list:
        try:
            model = genai.GenerativeModel(
                model_name=model_name, safety_settings=safety_settings
            )
            result = model.generate_content(prompt)
            return result.text, model_name
        except ResourceExhausted:
            st.warning(
                f"⚠️ `{model_name}` hết Quota (429). Đang trượt xuống model tiếp theo...",
                icon="🔄",
            )
            continue
        except Exception as e:
            st.error(f"❌ Lỗi với `{model_name}`: {str(e)}", icon="⚠️")
            continue

    raise Exception(
        "🚨 FATAL ERROR: Tất cả các model đều đã cạn kiệt lượt gọi hoặc gặp lỗi!"
    )
