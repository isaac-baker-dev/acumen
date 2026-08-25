"""Acumen Self-Correction - Reviews and fixes responses before sending."""

from acumen.core.logger import get_logger

logger = get_logger("acumen.core.self_correct")

REVIEW_TRIGGERS = ["explain", "compare", "analyze", "how does", "design",
    "build", "create", "write a", "step by step", "difference between",
    "pros and cons", "evaluate", "why does", "what causes"]

def needs_review(message):
    msg = message.lower().strip()
    if len(msg) < 30:
        return False
    return any(t in msg for t in REVIEW_TRIGGERS)

def self_correct(original_response, message, llm_fast):
    try:
        review_prompt = (
            f"Review this AI response for accuracy and quality. "
            f"The user asked: {message[:200]}\n\n"
            f"Response to review:\n{original_response[:1500]}\n\n"
            f"Check for:\n"
            f"1. Factual errors or contradictions\n"
            f"2. Missing important information\n"
            f"3. Unclear or confusing parts\n\n"
            f"If the response is good, reply with exactly: APPROVED\n"
            f"If there are issues, reply with: FIX: [brief description of what to fix]"
        )
        review = llm_fast.invoke(review_prompt)
        if "APPROVED" in review.upper():
            logger.info("Self-correction: response approved")
            return original_response
        if "FIX:" in review.upper():
            fix_description = review.split("FIX:")[-1].strip()[:200]
            logger.info(f"Self-correction: fixing - {fix_description[:50]}")
            fix_prompt = (
                f"Improve this response based on the feedback.\n\n"
                f"Original question: {message[:200]}\n\n"
                f"Original response:\n{original_response[:1500]}\n\n"
                f"Feedback: {fix_description}\n\n"
                f"Write an improved version. Keep the same friendly tone and structure:"
            )
            fixed = llm_fast.invoke(fix_prompt)
            if len(fixed) > 50:
                return fixed
        return original_response
    except Exception as e:
        logger.warning(f"Self-correction failed: {e}")
        return original_response