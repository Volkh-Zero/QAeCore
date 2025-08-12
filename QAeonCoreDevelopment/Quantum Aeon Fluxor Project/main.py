import os
import sys
import importlib.util
import argparse
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
from google.generativeai.protos import SafetySetting

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import qacore_prompt_engine using importlib
qacore_path = os.path.join(
    os.path.dirname(__file__),
    "Syzygy(Framework_Integration)",
    "Integration_Prototyping",
    "qacore_prompt_engine.py"
)

try:
    spec = importlib.util.spec_from_file_location("qacore_prompt_engine", qacore_path)
    qacore_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qacore_module)
    QuantumPromptGenerator = qacore_module.QuantumPromptGenerator
    QACORE_AVAILABLE = True
except (ImportError, FileNotFoundError) as e:
    QACORE_AVAILABLE = False
    print(f"QÆCore prompt engine not available: {e}. Running in basic mode.")

# --- Constants ---
MODEL_NAME = 'gemini-2.5-pro'
GENERATION_CONFIGS = {
    "default": GenerationConfig(
        temperature=0.7,
        top_p=0.95,
        top_k=64,
        max_output_tokens=8192
    ),
    "consciousness": GenerationConfig(
        temperature=0.8, top_p=0.9, top_k=50, max_output_tokens=8192
    ),
    "eonic": GenerationConfig(
        temperature=0.75, top_p=0.85, top_k=45, max_output_tokens=8192
    ),
    "meta": GenerationConfig(
        temperature=0.95, top_p=0.98, top_k=64, max_output_tokens=8192
    ),
}

def _get_safety_settings(block_none=True):
    """Returns a list of safety settings.

    Args:
        block_none (bool): If True, sets all harm categories to BLOCK_NONE.
                           Otherwise, uses default settings.

    Returns:
        list: A list of SafetySetting objects.
    """
    if not block_none:
        return []

    # Using a list comprehension for conciseness
    return [
        SafetySetting(category=category, threshold=HarmBlockThreshold.BLOCK_NONE)
        for category in [
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            HarmCategory.HARM_CATEGORY_HARASSMENT,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        ]
    ]

def _initialize_model(api_key):
    """Initializes and configures the generative model."""
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL_NAME)

def run_generative_model(model: genai.GenerativeModel):
    """
    Applies custom safety settings and generates content based on a prompt.
    The model is expected to be pre-initialized.

    Args:
        model: An initialized GenerativeModel instance.
    """
    if QACORE_AVAILABLE:
        prompt_generator = QuantumPromptGenerator()
        qacore_prompt = prompt_generator.generate_consciousness_inquiry(
            domain="artificial intelligence",
            question="What is the nature of genuine understanding versus pattern matching?",
            depth_level="deep"
        )
        print(f"Using QÆCore-enhanced prompt:\n{ '-' * 50}\n{qacore_prompt}\n{ '-' * 50}")
        prompt_to_use = qacore_prompt
    else:
        prompt_to_use = "Tell me a story about a brave knight."

    response = model.generate_content(
    prompt_to_use,
    generation_config=GENERATION_CONFIGS["default"],
    safety_settings=_get_safety_settings()
    )
    print(response.text)

def _run_and_print_demo(title, model, prompt, config):
    """Helper function to run a demo section, generate content, and print it."""
    print(title)
    print("-" * len(title))
    try:
        response = model.generate_content(prompt, generation_config=config, safety_settings=_get_safety_settings())
        print(f"{response.text}\n\n{'='*60}\n")
    except Exception as e:
        print(f"An error occurred: {e}\n\n{'='*60}\n")

def run_qacore_demo(model: genai.GenerativeModel):
    """
    Demonstrate QÆCore capabilities if available.
    The model is expected to be pre-initialized.

    Args:
        model: An initialized GenerativeModel instance.
    """
    if not QACORE_AVAILABLE:
        print("QÆCore system not available.")
        return

    prompt_generator = QuantumPromptGenerator()

    print("=== QÆCore Demonstration ===\n")

    # 1. Consciousness Inquiry
    consciousness_prompt = prompt_generator.generate_consciousness_inquiry(
        domain="complexity science",
        question="How does consciousness emerge from complex systems?",
        depth_level="transcendent"
    )
    _run_and_print_demo("1. Consciousness Inquiry", model, consciousness_prompt, GENERATION_CONFIGS["consciousness"])

    # 2. Eonic Scrutiny
    eonic_prompt = prompt_generator.generate_eonic_scrutiny("emergence of language")
    _run_and_print_demo("2. Eonic Scrutiny", model, eonic_prompt, GENERATION_CONFIGS["eonic"])

    # 3. Meta-Link Session
    meta_prompt = prompt_generator.generate_meta_link("QÆCore framework effectiveness")
    _run_and_print_demo("3. Meta-Link Session", model, meta_prompt, GENERATION_CONFIGS["meta"])

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Run the Quantum Æon Core generative model.")
    parser.add_argument(
        'mode',
        choices=['basic', 'demo'],
        nargs='?',
        default='basic',
        help="The mode to run the script in: 'basic' for a single prompt, 'demo' for the QÆCore showcase. (default: basic)"
    )
    args = parser.parse_args()

    api_key = os.getenv("GOOGLE_API_KEY")
    model = _initialize_model(api_key)

    if args.mode == 'demo':
        run_qacore_demo(model)
    else:  # 'basic' is the default
        run_generative_model(model)

if __name__ == "__main__":
    main()
