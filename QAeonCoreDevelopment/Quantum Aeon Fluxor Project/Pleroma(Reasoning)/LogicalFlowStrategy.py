# qef_core/reasoning/LogicalFlowStrategy.py

from .BaseStrategy import BaseStrategy
# Import our new client. The path may need adjustment based on your final structure.
from ..Hermetic_Engine.Conduits.GeminiClient import GeminiClient

class LogicalFlowStrategy(BaseStrategy):
    """
    A reasoning strategy focused on generating a clear, coherent, and
    step-by-step logical argument or process.
    """

    def __init__(self):
        # Initialize the connection to our LLM client when the strategy is created.
        self.llm_client = GeminiClient()

    @property
    def name(self) -> str:
        return "logical_flow"

    def execute(self, user_prompt: str, context: dict) -> dict:
        """
        Generates a logically structured response to the user's prompt using a live LLM.
        """
        print(f"--- Executing Strategy: {self.name} ---")

        # --- Stage 1: Decomposition ---
        decomposition_prompt = f"""
        Analyze the following user prompt: "{user_prompt}"
        Your task is to decompose this prompt into a series of clear, logical steps
        that must be followed to provide a comprehensive and well-structured answer.
        Present these steps as a numbered list.
        """
        decomposed_steps = self.llm_client.query(decomposition_prompt)
        print(f"Step 1 (Decomposition): Identified steps:\n{decomposed_steps}\n")

        # --- Stage 2: Generation ---
        generation_prompt = f"""
        Based on the following logical steps:
        <steps>
        {decomposed_steps}
        </steps>
        And the original user prompt: "{user_prompt}"
        Generate a clear and comprehensive response that follows these steps exactly.
        Use Markdown formatting for clarity.
        """
        generated_content = self.llm_client.query(generation_prompt)
        print(f"Step 2 (Generation): Generated content.\n")

        # --- Stage 3: Self-Evaluation ---
        evaluation_prompt = f"""
        Review the following generated response:
        <response>
        {generated_content}
        </response>
        Does this response logically follow the requested steps and fully address
        the user's original prompt? Answer with only "Yes" or "No" and a brief
        one-sentence justification.
        """
        evaluation = self.llm_client.query(evaluation_prompt)
        print(f"Step 3 (Self-Evaluation): Result: {evaluation}\n")

        # --- Stage 4: Final Output ---
        result = {
            "strategy_name": self.name,
            "input_prompt": user_prompt,
            "reasoning_path": decomposed_steps,
            "final_output": generated_content,
            "self_evaluation": evaluation,
            "status": "Success"
        }
        
        print(f"--- Strategy {self.name} Complete ---")
        return result

# --- Example Usage ---
# (The example usage remains the same, but will now perform live API calls)
if __name__ == "__main__":
    strategy = LogicalFlowStrategy()
    test_prompt = "Explain the concept of a Python class."
    test_context = {}
    final_result = strategy.execute(test_prompt, test_context)
    
    print("\n--- FINAL RESULT ---")
    import json
    print(json.dumps(final_result, indent=2))