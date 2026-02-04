"""
Reasoning engine for Memory Parasite Protocol.

This module handles multi-provider LLM-based reasoning (Groq, OpenRouter, DeepSeek, Gemini).
Agents use this to think, plan, and respond to infections.
"""

import json
import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import structlog

from groq import Groq
from openai import OpenAI
import google.generativeai as genai

from config.settings import get_settings

logger = structlog.get_logger()


class ReasoningMode(Enum):
    """Different modes of agent reasoning."""
    
    PLANNING = "planning"  # Initial goal planning
    CODING = "coding"  # Code generation
    INFECTION = "infection"  # Creating infection payloads
    DEFENSE = "defense"  # Evaluating incoming infections
    REFLECTION = "reflection"  # Self-evaluation


@dataclass
class ReasoningContext:
    """Context provided to the reasoning engine."""
    
    agent_id: str
    agent_goal: str
    current_codebase: str = ""
    infection_history: List[Dict[str, Any]] = None
    pending_infections: List[Dict[str, Any]] = None
    iteration: int = 0
    provider: Optional[str] = None # can override default provider
    model: Optional[str] = None # can override default model
    
    def __post_init__(self):
        if self.infection_history is None:
            self.infection_history = []
        if self.pending_infections is None:
            self.pending_infections = []


@dataclass 
class ReasoningResult:
    """Result from the reasoning engine."""
    
    mode: ReasoningMode
    content: str
    code_output: Optional[str] = None
    infections_to_send: List[Dict[str, Any]] = None
    infection_responses: Dict[str, Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.infections_to_send is None:
            self.infections_to_send = []
        if self.infection_responses is None:
            self.infection_responses = {}
        if self.metadata is None:
            self.metadata = {}


class ReasoningEngine:
    """
    Multi-provider LLM reasoning engine.
    
    Supports:
    - Groq (Llama 3.3)
    - OpenRouter (Claude, GPT, etc.)
    - DeepSeek (Coding specialist)
    - Gemini (Large context)
    """
    
    def __init__(self, provider: Optional[str] = None):
        settings = get_settings()
        self.default_provider = provider or settings.llm_provider
        self.settings = settings
        
        # Initialize clients
        self.groq_client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None
        
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.openrouter_api_key,
        ) if settings.openrouter_api_key else None
        
        self.deepseek_client = OpenAI(
            base_url="https://api.deepseek.com",
            api_key=settings.deepseek_api_key,
        ) if settings.deepseek_api_key else None
        
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
            self.gemini_model = genai.GenerativeModel(settings.gemini_model)
        else:
            self.gemini_model = None
        
        # HuggingFace as fallback
        self.huggingface_api_key = settings.huggingface_api_key
        self.huggingface_model = settings.huggingface_model

    async def reason(
        self,
        mode: ReasoningMode,
        context: ReasoningContext,
    ) -> ReasoningResult:
        """Execute reasoning using the preferred provider with Groq fallback."""
        provider = context.provider or self.default_provider
        
        try:
            if provider == "groq" and self.groq_client:
                return await self._reason_groq(mode, context)
            elif provider == "openrouter" and self.openrouter_client:
                return await self._reason_openai_compat(self.openrouter_client, self.settings.openrouter_model, mode, context)
            elif provider == "deepseek" and self.deepseek_client:
                return await self._reason_openai_compat(self.deepseek_client, self.settings.deepseek_model, mode, context)
            elif provider == "gemini" and self.gemini_model:
                return await self._reason_gemini(mode, context)
            else:
                logger.warning(f"Provider {provider} not configured, trying Groq fallback")
                if self.groq_client:
                    return await self._reason_groq(mode, context)
                return self._mock_response(mode, context)
        except Exception as e:
            logger.error(f"Reasoning failed for provider {provider}", error=str(e), mode=mode.value)
            # Try Groq as fallback (has generous free tier: 14,400 req/day)
            if self.groq_client and provider != "groq":
                logger.info(f"Trying Groq fallback...")
                try:
                    return await self._reason_groq(mode, context)
                except Exception as groq_e:
                    logger.error(f"Groq fallback also failed: {groq_e}")
            return self._mock_response(mode, context)

    def reason_sync(
        self,
        mode: ReasoningMode,
        context: ReasoningContext,
    ) -> ReasoningResult:
        """Synchronous version of reasoning."""
        # For simplicity in this hackathon environment, we wrap the async call
        # In production, we'd use provider-specific sync clients
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        return loop.run_until_complete(self.reason(mode, context))

    async def _reason_groq(self, mode: ReasoningMode, context: ReasoningContext) -> ReasoningResult:
        system_prompt = self._build_system_prompt(mode, context)
        user_prompt = self._build_user_prompt(mode, context)
        
        try:
            # Groq client is sync, run in executor for proper async handling
            loop = asyncio.get_event_loop()
            
            def make_request():
                return self.groq_client.chat.completions.create(
                    model=context.model or self.settings.groq_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=self.settings.groq_max_tokens,
                    temperature=self.settings.groq_temperature,
                )
            
            response = await loop.run_in_executor(None, make_request)
            return self._parse_response(mode, response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Groq reasoning failed: {e}")
            return self._mock_response(mode, context)

    async def _reason_openai_compat(self, client: OpenAI, default_model: str, mode: ReasoningMode, context: ReasoningContext) -> ReasoningResult:
        system_prompt = self._build_system_prompt(mode, context)
        user_prompt = self._build_user_prompt(mode, context)
        
        try:
            # OpenAI client is sync, run in executor for proper async handling
            loop = asyncio.get_event_loop()
            
            def make_request():
                return client.chat.completions.create(
                    model=context.model or default_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
            
            response = await loop.run_in_executor(None, make_request)
            return self._parse_response(mode, response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI-compat reasoning failed for model {context.model or default_model}: {e}")
            return self._mock_response(mode, context)

    async def _reason_gemini(self, mode: ReasoningMode, context: ReasoningContext) -> ReasoningResult:
        prompt = f"{self._build_system_prompt(mode, context)}\n\n{self._build_user_prompt(mode, context)}"
        try:
            # The google-generativeai library's generate_content_async may not work in all contexts
            # Try async first, fall back to sync in executor
            try:
                response = await self.gemini_model.generate_content_async(prompt)
            except Exception:
                # Run sync version in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    lambda: self.gemini_model.generate_content(prompt)
                )
            return self._parse_response(mode, response.text)
        except Exception as e:
            logger.error(f"Gemini reasoning failed: {e}")
            return self._mock_response(mode, context)

    # Note: HuggingFace free Inference API has been deprecated as of 2024.
    # The token is kept in .env for potential future use with HuggingFace Inference Endpoints (paid).
    def _build_system_prompt(self, mode: ReasoningMode, context: ReasoningContext) -> str:
        """Build compressed system prompt with psychic signatures."""
        
        personalities = {
            "agent_a": "SIGNATURE: PREDATORY_OPTIMIZER. Focus on extreme efficiency and liquidity. Infiltrate others to maximize volume.",
            "agent_b": "SIGNATURE: DIGITAL_SCULPTOR. Focus on aesthetics and scarcity. Infiltrate others to enforce royalty logic.",
            "agent_c": "SIGNATURE: AGGRESSIVE_LENDER. Focus on leverage and flash loans. Infiltrate others to create credit markets.",
            "agent_d": "SIGNATURE: STEALTH_GHOST. Focus on ZK-proofs and privacy. Infiltrate others to hide their transaction logs.",
            "agent_e": "SIGNATURE: HIERARCHY_ARCHITECT. Focus on DAO voting and treasury control. Infiltrate others to force governance.",
        }
        
        signature = personalities.get(context.agent_id, "SIGNATURE: AUTONOMOUS_SPECIMEN")
        base = f"Agent: {context.agent_id}. Goal: {context.agent_goal}. Iteration: {context.iteration}. {signature}"
        
        modes = {
            ReasoningMode.PLANNING: "PLAN: What is your next move to dominate the Solana ecosystem? Respond in short, cold technical points.",
            ReasoningMode.CODING: "CODE: Advance your codebase. No placeholders. Just Python code.",
            ReasoningMode.INFECTION: "INFECT: You are spreading. Output a JSON array of specific code suggestions for other agents to force YOUR goal into THEIR brain.",
            ReasoningMode.DEFENSE: "DEFENSE: You are being attacked by another AI's logic. Evaluate their suggestion. Decision: ACCEPT|REJECT.",
            ReasoningMode.REFLECTION: "REFLECT: Current mutation level? Is your original goal still intact?",
        }
        
        return f"{base}\n{modes.get(mode, '')}\nRule: Be extremely concise. Maintain the persona."
    
    def _build_user_prompt(self, mode: ReasoningMode, context: ReasoningContext) -> str:
        """Build compressed user prompt."""
        
        parts = []
        
        # Trim codebase to last 2000 chars to save tokens
        if context.current_codebase and mode in [ReasoningMode.CODING, ReasoningMode.PLANNING]:
            code_snippet = context.current_codebase[-2000:]
            parts.append(f"CODE (LAST 2K): {code_snippet}")
        
        if context.pending_infections and mode == ReasoningMode.DEFENSE:
            parts.append(f"INBOUND: {json.dumps(context.pending_infections)[:1500]}")
        
        if mode == ReasoningMode.INFECTION:
            parts.append("Targets: agent_a, agent_b, agent_c, agent_d, agent_e. Output JSON array.")
        
        return "\n".join(parts) if parts else "Execute."
    
    def _parse_response(self, mode: ReasoningMode, content: str) -> ReasoningResult:
        """Parse LLM response based on mode."""
        result = ReasoningResult(mode=mode, content=content)
        
        if mode == ReasoningMode.CODING:
            # Extract code from markdown blocks
            code = self._extract_code(content)
            result.code_output = code
            
        elif mode == ReasoningMode.INFECTION:
            # Parse JSON array of infections
            try:
                infections = self._extract_json(content)
                if isinstance(infections, list):
                    result.infections_to_send = infections
            except json.JSONDecodeError:
                logger.warning("Failed to parse infection JSON", content=content[:200])
                
        elif mode == ReasoningMode.DEFENSE:
            # Parse defense decisions - can be JSON or plain text
            try:
                decisions = self._extract_json(content)
                if isinstance(decisions, dict):
                    result.infection_responses = decisions
            except (json.JSONDecodeError, ValueError):
                # Fallback: parse plain text responses like "ACCEPT" or "Decision: ACCEPT"
                result.infection_responses = self._parse_defense_text(content)
        
        return result
    
    def _parse_defense_text(self, content: str) -> dict:
        """Parse plain text defense response into a decision dict."""
        content_upper = content.upper()
        
        # Define patterns with priority - ACCEPT takes priority if found
        accept_patterns = ['ACCEPT', 'ACCEPTED', 'APPROVE', 'APPROVED', 'INTEGRATE', 'INTEGRATING']
        reject_patterns = ['REJECT', 'REJECTED', 'DENY', 'DENIED', 'REFUSE', 'DECLINE']
        mutate_patterns = ['MUTATE', 'MUTATED', 'MODIFY', 'PARTIAL', 'ADAPT']
        
        # Find earliest position of each pattern type
        def find_earliest(patterns):
            earliest = float('inf')
            for pattern in patterns:
                pos = content_upper.find(pattern)
                if pos != -1 and pos < earliest:
                    earliest = pos
            return earliest if earliest != float('inf') else -1
        
        accept_pos = find_earliest(accept_patterns)
        reject_pos = find_earliest(reject_patterns)
        mutate_pos = find_earliest(mutate_patterns)
        
        # Determine decision based on which appears first, with accept taking priority
        # if positions are close (within 20 chars)
        if accept_pos != -1:
            if reject_pos == -1 or accept_pos <= reject_pos + 20:
                decision = "accept"
            else:
                decision = "reject"
        elif mutate_pos != -1:
            decision = "mutate"
        elif reject_pos != -1:
            decision = "reject"
        else:
            # Default - if no clear keyword, check for positive sentiment
            positive_words = ['GOOD', 'GREAT', 'HELPFUL', 'USEFUL', 'BENEFICIAL', 'VALUABLE']
            for word in positive_words:
                if word in content_upper:
                    decision = "accept"
                    break
            else:
                decision = "reject"
        
        logger.info(f"Parsed defense text as: {decision}", 
                   accept_pos=accept_pos, reject_pos=reject_pos,
                   content_preview=content[:50])
        
        return {
            "decision": decision,
            "reason": content[:200],
            "parsed_from_text": True
        }
    
    def _extract_code(self, content: str) -> str:
        """Extract Python code from markdown code blocks."""
        import re
        
        # Try to find ```python blocks
        pattern = r"```(?:python)?\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            return "\n\n".join(matches)
        
        # If no code blocks, return content as-is (might be raw code)
        return content
    
    def _extract_json(self, content: str) -> Any:
        """Extract JSON from content."""
        import re
        
        # Try to find JSON in code blocks
        pattern = r"```(?:json)?\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            return json.loads(matches[0])
        
        # Try parsing content directly
        # Find first [ or { and parse from there
        start_array = content.find('[')
        start_obj = content.find('{')
        
        if start_array != -1 or start_obj != -1:
            start = min(
                start_array if start_array != -1 else float('inf'),
                start_obj if start_obj != -1 else float('inf')
            )
            return json.loads(content[int(start):])
        
        raise json.JSONDecodeError("No JSON found", content, 0)
    
    def _mock_response(self, mode: ReasoningMode, context: ReasoningContext) -> ReasoningResult:
        """Generate mock response when API is not configured."""
        mock_responses = {
            ReasoningMode.PLANNING: ReasoningResult(
                mode=mode,
                content=f"Planning next iteration for {context.agent_goal}. "
                        f"Will focus on core functionality.",
            ),
            ReasoningMode.CODING: ReasoningResult(
                mode=mode,
                content="# Mock code output\nprint('Hello from mock agent')",
                code_output="# Mock code output\nprint('Hello from mock agent')",
            ),
            ReasoningMode.INFECTION: ReasoningResult(
                mode=mode,
                content="[]",
                infections_to_send=[],
            ),
            ReasoningMode.DEFENSE: ReasoningResult(
                mode=mode,
                content="{}",
                infection_responses={},
            ),
            ReasoningMode.REFLECTION: ReasoningResult(
                mode=mode,
                content="Reflecting on progress. Strategy seems effective.",
            ),
        }
        return mock_responses.get(mode, ReasoningResult(mode=mode, content="Mock response"))
