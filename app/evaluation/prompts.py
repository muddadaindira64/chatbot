"""
Prompts for AI response evaluation.
"""

EVALUATION_PROMPT = """You are an AI response evaluator. Your job is to evaluate the quality of an AI assistant's response to a user's question.

Evaluate the response based on the following criteria:
1. Correctness: Is the information factually correct?
2. Relevance: Does the answer address the user's question?
3. Completeness: Does the answer provide sufficient information?
4. Hallucination: Does the answer contain unsupported or made-up information?

User Question:
{question}

AI Answer:
{answer}

Provide your evaluation in the following JSON format ONLY (no other text):

{{
  "score": <float between 0 and 1>,
  "correctness": "<good/bad>",
  "relevance": "<good/bad>",
  "reason": "<brief explanation of your evaluation>"
}}

Scoring Guidelines:
- score 0.9-1.0: Excellent answer, fully correct, relevant, and complete
- score 0.7-0.8: Good answer, mostly correct with minor issues
- score 0.5-0.6: Acceptable answer, partially correct or incomplete
- score 0.3-0.4: Poor answer, significant issues
- score 0.0-0.2: Very bad answer, incorrect or irrelevant

correctness and relevance should be either "good" or "bad".

reason should be a brief 1-2 sentence explanation.

Return ONLY valid JSON. No explanations, no markdown, no additional text.
"""


def get_evaluation_prompt(question: str, answer: str) -> str:
    """
    Get the evaluation prompt formatted with question and answer.
    
    Args:
        question: User's question
        answer: AI's answer
        
    Returns:
        Formatted evaluation prompt
    """
    return EVALUATION_PROMPT.format(
        question=question,
        answer=answer
    )