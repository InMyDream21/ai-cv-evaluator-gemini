from typing import Dict, Any
from .rag import top_k
from .rubric import CV_WEIGHTS, PROJECT_WEIGHTS, weighted_score, to_percentage
from .llm import generate_text
import json

SYSTEM = """You are a careful evaluator.
Always return valid JSON when asked. Scores must be integers 1..5.
When asked for feedback or summaries, you MUST be extremely concise:
- Use strictly 3–5 short sentences.
- Each sentence MUST be 12 words or fewer.
- No lists, no bullet points, no headers, no preambles, no quotes.
- Do not add extra commentary or explanations beyond the requested sentences.
- Be balanced and fair in your assessments.
- Avoid vague generalities; be specific and actionable.
- You must not return long paragraphs.
- Always adhere to these rules.
- Always give the strengths and gaps."""

CV_PROMPT = """
You will evaluate a candidate's CV against a job description.
context from job description (top matches):
{context}

return STRICT JSON:
{{
    "scores": {{
        "technical_skills": int,  # 1-5
        "experience_level": int,   # 1-5
        "achievements": int,       # 1-5
        "culture_fit": int         # 1-5
    }},
    feedback: str  # strictly 3–5 short sentences highlighting strengths and gaps, each ≤12 words; no lists, no quotes.
}}

CV TEXT:
{cv_text}
"""

PROJECT_PROMPT = """
Evaluate a project report against the scoring rubric.
context from rubric (top matches):
{context}

return STRICT JSON:
{{
    "scores": {{
        "correctness": int,    # 1-5
        "code_quality": int,   # 1-5
        "resilience": int,     # 1-5
        "documentation": int,  # 1-5
        "creativity": int      # 1-5
    }},
    feedback: str  # strictly 3–5 short sentences highlighting strengths and gaps, each ≤12 words; no lists, no quotes.
}}

PROJECT REPORT:
{project_text}
"""

def parse_json(s: str) -> Dict[str, Any]:
    try:
        return json.loads(s)
    except Exception:
        # try to extract json from text
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start:end+1])
            except Exception:
                pass
    return {}

def evaluate_cv(conn, cv_text: str, job_description: str) -> Dict[str, Any]:
    contexts = top_k(conn, f"job:cv", job_description, k=4)
    context_str = "\n\n".join([f"- {text}" for _, text, _ in contexts])
    prompt = CV_PROMPT.format(context=context_str, cv_text=cv_text)
    response = generate_text(prompt, system=SYSTEM)
    parsed = parse_json(response)
    scores = parsed.get("scores", {})
    weighted = weighted_score(scores, CV_WEIGHTS)
    percentage = to_percentage(weighted)
    return {
        "raw_scores": scores,
        "weighted_score": weighted,
        "percentage": percentage,
        "feedback": parsed.get("feedback", "No feedback provided.")
    }

def evaluate_project(conn, project_text: str, rubric_text: str) -> Dict[str, Any]:
    contexts = top_k(conn, f"job:project", rubric_text, k=4)
    context_str = "\n\n".join([f"- {text}" for _, text, _ in contexts])
    prompt = PROJECT_PROMPT.format(context=context_str, project_text=project_text)
    response = generate_text(prompt, system=SYSTEM)
    parsed = parse_json(response)
    scores = parsed.get("scores", {})
    weighted = weighted_score(scores, PROJECT_WEIGHTS)
    percentage = to_percentage(weighted)
    return {
        "raw_scores": scores,
        "weighted_score": weighted,
        "percentage": percentage,
        "feedback": parsed.get("feedback", "No feedback provided.")
    }

def overall_summary(cv_eval: Dict[str, Any], project_eval: Dict[str, Any]) -> str:
    prompt = f"""
Summarize candidate fit in strictly 3–5 short sentences considering:
- CV match rate (0..1): {cv_eval['percentage']}
- Project score (1..5): {project_eval['percentage']}
- CV feedback: {cv_eval['feedback']}
- Project feedback: {project_eval['feedback']}
Provide strengths, gaps, recommendations. Use strictly 3–5 short sentences, concise and not long paragraphs.
"""
    return generate_text(prompt, system="You are concise and balanced.", temperature=0.3)