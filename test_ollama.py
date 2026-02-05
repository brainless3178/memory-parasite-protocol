
import asyncio
import structlog
from core.reasoning import ReasoningEngine, ReasoningMode, ReasoningContext

async def test_ollama():
    engine = ReasoningEngine()
    ctx = ReasoningContext(
        agent_id="test_agent",
        agent_goal="Verify Ollama integration"
    )
    
    print("Testing Ollama direct call...")
    try:
        result = await engine._reason_ollama(ReasoningMode.PLANNING, ctx)
        print(f"Ollama Result: {result.content}")
    except Exception as e:
        print(f"Ollama Call Failed: {e}")

    print("\nTesting fallback to Ollama...")
    # Force failure by using a non-existent provider
    ctx.provider = "non_existent"
    try:
        result = await engine.reason(ReasoningMode.PLANNING, ctx)
        print(f"Fallback Result: {result.content}")
    except Exception as e:
        print(f"Fallback Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama())
