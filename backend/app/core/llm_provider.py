"""
LLM Provider — Cerebras AI
============================
Async Cerebras AI provider via api.cerebras.ai

Uses httpx.AsyncClient for non-blocking FastAPI integration.
Models: llama3.1-8b (lightest/cheapest), gpt-oss-120b, qwen-3-235b
"""
import os
import json
import httpx
from typing import Dict, Any
from loguru import logger


class QwenProvider:
    """
    Cerebras AI LLM provider (OpenAI-compatible).
    
    Base URL: https://api.cerebras.ai/v1
    Model: llama3.1-8b (8B params, ~2,200 tok/s, cheapest)
    Features: JSON output, Arabic support, extremely fast
    """
    
    BASE_URL = "https://api.cerebras.ai/v1"
    MODEL = "llama3.1-8b"
    TIMEOUT = 45.0  # seconds
    
    def __init__(self):
        self.api_key = os.getenv("QWEN_API_KEY", "")
        if not self.api_key:
            raise ValueError("QWEN_API_KEY not set in environment. Add it to backend/.env")
        
        logger.info(f"QwenProvider initialized: model={self.MODEL}")
    
    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output from Qwen AI.
        
        Async — does not block FastAPI worker.
        
        Args:
            system_prompt: System instructions
            user_prompt: User request
            max_retries: Number of retries on failure
            
        Returns:
            Parsed JSON dict from AI response
            
        Raises:
            ValueError: If API fails or returns invalid JSON
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                    response = await client.post(
                        f"{self.BASE_URL}/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.MODEL,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt},
                            ],
                            "response_format": {"type": "json_object"},
                            "temperature": 0.7,
                        },
                    )
                    
                    if response.status_code != 200:
                        logger.error(
                            f"Qwen API error (attempt {attempt + 1}): "
                            f"{response.status_code} — {response.text[:200]}"
                        )
                        last_error = ValueError(
                            f"Qwen API returned {response.status_code}"
                        )
                        continue
                    
                    data = response.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    
                    if not content:
                        logger.error(f"Empty response from Qwen (attempt {attempt + 1})")
                        last_error = ValueError("Empty response from Qwen AI")
                        continue
                    
                    # Parse JSON — handle markdown code blocks, YAML-like format, and JSON Schema wrappers
                    content = content.strip()
                    
                    # Remove markdown code blocks
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    # Remove JSON Schema wrapper if present (e.g., {"type": "object", "properties": {...}})
                    if '"type": "object"' in content[:50]:
                        # Extract just the actual data object
                        import re
                        match = re.search(r'\{[^{]*"base_product"', content)
                        if match:
                            content = content[match.start():]
                    
                    # Fix YAML-like format from Cerebras models
                    # Cerebras/llama models often output YAML-like format with colons and indentation
                    # Example: "key":\n  "subkey": "value"  (invalid JSON)
                    # Should be: "key": {"subkey": "value"}  (valid JSON)
                    import re

                    # Step 1: Remove JSON Schema wrapper if present
                    if '"type": "object"' in content[:100]:
                        match = re.search(r'\{[^{]*"base_product"', content)
                        if match:
                            content = content[match.start():]

                    # Step 2: Convert YAML-like format to JSON
                    # Pattern: "key":\n  "subkey": "value"  →  "key": {"subkey": "value"}
                    if re.search(r'":\s*\n\s+"', content):
                        lines = content.split('\n')
                        fixed_lines = []
                        i = 0
                        while i < len(lines):
                            line = lines[i].rstrip()

                            # YAML object start: line ends with ":" and next line is indented
                            if line.endswith(':') and i + 1 < len(lines) and lines[i + 1].startswith('  '):
                                key_part = line[:-1].strip()
                                children = []
                                i += 1
                                # Collect all indented child lines
                                while i < len(lines):
                                    child_line = lines[i]
                                    # Stop when we hit a line that's not indented
                                    if child_line.strip() and not child_line.startswith('  '):
                                        break
                                    children.append(child_line.strip().rstrip(','))
                                    i += 1
                                # Build JSON object from children
                                child_json = ', '.join(children)
                                fixed_lines.append(f'{key_part}: {{{child_json}}}')
                            else:
                                fixed_lines.append(line.rstrip(','))
                                i += 1
                        content = '\n'.join(fixed_lines)

                    # Step 3: Handle truncated JSON - find last valid closing brace
                    # Track brace depth while respecting string boundaries
                    try:
                        result = json.loads(content)
                    except json.JSONDecodeError:
                        brace_depth = 0
                        last_valid_end = 0
                        in_string = False
                        escape_next = False

                        for idx, char in enumerate(content):
                            if escape_next:
                                escape_next = False
                                continue
                            if char == '\\':
                                escape_next = True
                                continue
                            if char == '"':
                                in_string = not in_string
                                continue
                            if not in_string:
                                if char == '{':
                                    brace_depth += 1
                                elif char == '}':
                                    brace_depth -= 1
                                    if brace_depth == 0:
                                        last_valid_end = idx + 1

                        if last_valid_end > 0:
                            content = content[:last_valid_end]
                            result = json.loads(content)
                        else:
                            raise
                    
                    # Usage stats
                    usage = data.get("usage", {})
                    tokens = usage.get("total_tokens", "unknown")
                    logger.info(f"Qwen response: {tokens} tokens used")
                    
                    return result
                    
            except json.JSONDecodeError as e:
                logger.error(
                    f"Invalid JSON from Qwen (attempt {attempt + 1}): {e}\n"
                    f"Content: {content[:200] if 'content' in locals() else 'N/A'}"
                )
                last_error = ValueError(f"Qwen returned invalid JSON: {e}")
                continue
                
            except httpx.TimeoutException:
                logger.warning(f"Qwen API timeout (attempt {attempt + 1})")
                last_error = ValueError("Qwen API request timed out")
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")
                last_error = e
                continue
        
        # All retries exhausted
        raise last_error or ValueError("Qwen API failed after retries")
