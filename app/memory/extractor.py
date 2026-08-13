import json
import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)


# System prompt for personal information extraction
EXTRACTION_SYSTEM_PROMPT = """You are a personal information extractor. Your job is to analyze user messages and extract ONLY personal information about the user.

Extract ONLY the following types of information if present:
- name: User's name
- role: User's job title, role, or profession
- company: User's company or organization
- skills: User's skills or technologies they know (as a list)
- preferences: User's preferences (likes, dislikes, favorites, etc.)

RULES:
1. ONLY extract information that the user is sharing about THEMSELVES
2. DO NOT extract information from questions like "What is Python?" or "Who is the PM of India?"
3. DO NOT extract general knowledge or facts
4. If NO personal information is found, return {"has_personal_info": false}
5. If personal information IS found, return {"has_personal_info": true, ...fields}
6. Be precise - only extract what is explicitly stated

EXAMPLES:

Input: "My name is Indira"
Output: {"has_personal_info": true, "name": "Indira"}

Input: "I work as a GEN AI intern"
Output: {"has_personal_info": true, "role": "GEN AI intern"}

Input: "I work at ABC company"
Output: {"has_personal_info": true, "company": "ABC company"}

Input: "I know Python, JavaScript, and React"
Output: {"has_personal_info": true, "skills": ["Python", "JavaScript", "React"]}

Input: "My favorite food is biryani"
Output: {"has_personal_info": true, "preferences": {"favorite_food": "biryani"}}

Input: "What is Python?"
Output: {"has_personal_info": false}

Input: "Who is the CM of AP?"
Output: {"has_personal_info": false}

Input: "Tell me about machine learning"
Output: {"has_personal_info": false}

Return ONLY valid JSON. No explanations or additional text.
"""


def extract_personal_information(message: str) -> Dict[str, Any]:
    """
    Extract personal information from user message using LLM.
    
    Args:
        message: User message to analyze
        
    Returns:
        Dictionary with has_personal_info flag and extracted fields
    """
    try:
        # Check if API key is configured
        if not settings.openrouter_api_key:
            logger.warning("OpenRouter API key not configured, skipping extraction")
            return {"has_personal_info": False}
        
        # Initialize LLM
        llm = ChatOpenAI(
            model="openai/gpt-4o-mini",
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            temperature=0.1  # Low temperature for consistent extraction
        )
        
        # Create messages
        messages = [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=message)
        ]
        
        # Invoke LLM
        response = llm.invoke(messages)
        
        # Parse response
        content = response.content.strip()
        
        # Try to extract JSON from response
        # Sometimes LLM wraps JSON in markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        # Parse JSON
        extracted = json.loads(content)
        
        # Validate response structure
        if "has_personal_info" not in extracted:
            logger.warning("Invalid extraction response: missing has_personal_info field")
            return {"has_personal_info": False}
        
        logger.info(
            "Personal information extraction: %s",
            "FOUND" if extracted["has_personal_info"] else "NONE"
        )
        
        return extracted
        
    except json.JSONDecodeError as e:
        logger.error("Failed to parse extraction response: %s", e)
        return {"has_personal_info": False}
    
    except Exception as e:
        logger.exception("Error during personal information extraction")
        return {"has_personal_info": False}


# Legacy function for backward compatibility
def extract_user_memory(message: str) -> dict:
    """
    Legacy extraction function (rule-based).
    Kept for backward compatibility.
    
    Args:
        message: User message
        
    Returns:
        Dictionary with extracted fields
    """
    extracted = {}
    text = message.lower()
    
    if "my name is" in text:
        name = message.split("my name is")[-1].strip()
        extracted["name"] = name
    
    if "i am a" in text:
        role = message.split("i am a")[-1].strip()
        extracted["role"] = role
    
    if "i know" in text:
        skills = message.split("i know")[-1].split(",")
        extracted["skills"] = [x.strip() for x in skills]
    
    return extracted