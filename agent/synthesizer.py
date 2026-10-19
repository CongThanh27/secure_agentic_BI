"""Second LLM call: turn query results into a Vietnamese answer. No tools."""

from .llm import call_llm_with_fallback


def synthesize_final_answer(
    user_prompt: str, data_context: str, active_model: str
) -> tuple[str, str]:
    system_prompt = f"""
    Bạn là một Data Analyst chuyên nghiệp. Người dùng đã đặt một câu hỏi.
    Hệ thống đã truy xuất dữ liệu từ Database và cung cấp cho bạn dưới định dạng CSV hoặc Text.
    
    Dữ liệu truy xuất được:
    {data_context}
    
    Nhiệm vụ của bạn:
    Hãy dựa CHÍNH XÁC vào dữ liệu trên để trả lời câu hỏi của người dùng bằng tiếng Việt một cách tự nhiên, súc tích và dễ hiểu. 
    Nếu dữ liệu báo lỗi, hãy giải thích lỗi đó cho người dùng (Đóng vai trò là hệ thống báo lỗi bảo mật).
    """
    try:
        full_prompt = system_prompt + "\n\nCâu hỏi của người dùng: " + user_prompt
        return call_llm_with_fallback(full_prompt, active_model)
    except Exception as e:
        return f"Lỗi tổng hợp câu trả lời: {str(e)}", "N/A"
