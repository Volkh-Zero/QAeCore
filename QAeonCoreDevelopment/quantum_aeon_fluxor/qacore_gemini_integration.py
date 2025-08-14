"""
QAeCore-Gemini Integration
Combines the Quantum Aeon Fluxor prompt engineering system with Gemini AI
"""

import os
import sys
import importlib.util
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
from google.generativeai.protos import SafetySetting

# --- Constants ---
MODEL_NAME = 'gemini-2.5-pro'

# Import qacore_prompt_engine using importlib
qacore_path = os.path.join(
    os.path.dirname(__file__),
    "syzygy__conversational_framework",
    "Integration_Prototyping",
    "qacore_prompt_engine.py"
)

# Load the module
try:
    spec = importlib.util.spec_from_file_location("qacore_prompt_engine", qacore_path)
    qacore_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(qacore_module)
    
    # Import the required components
    QuantumPromptGenerator = qacore_module.QuantumPromptGenerator
    QAeMode = qacore_module.QAeMode
    PlausibilityLevel = qacore_module.PlausibilityLevel
    QAeCorePromptLibrary = qacore_module.QAeCorePromptLibrary
    
except (ImportError, FileNotFoundError) as e:
    print(f"Error loading QAeCore prompt engine: {e}")
    raise

class QAeCoreGeminiInterface:
    """Integration between QAeCore prompt system and Gemini AI"""
    
    def __init__(self):
        self.prompt_generator = QuantumPromptGenerator()
        self.model = None
        self._setup_gemini()
        
    def _setup_gemini(self):
        """Initialize Gemini with QAeCore-optimized settings"""
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(MODEL_NAME)
            
        except Exception as e:
            print(f"Error setting up Gemini: {e}")
    
    def _get_generation_config(self, mode: QAeMode) -> GenerationConfig:
        """Get Gemini generation config optimized for specific QAeCore modes"""
        
        # Mode-specific parameter tuning
        mode_configs = {
            QAeMode.EXPLORATION: {"temperature": 0.9, "top_p": 0.95, "top_k": 64},
            QAeMode.REFLECTION: {"temperature": 0.7, "top_p": 0.9, "top_k": 40},
            QAeMode.CHALLENGE: {"temperature": 0.8, "top_p": 0.85, "top_k": 50},
            QAeMode.SYNTHESIS: {"temperature": 0.85, "top_p": 0.9, "top_k": 60},
            QAeMode.GROUNDING: {"temperature": 0.3, "top_p": 0.7, "top_k": 20},
            QAeMode.EONIC_EVALUATION: {"temperature": 0.8, "top_p": 0.9, "top_k": 50},
            QAeMode.META_COMMENTS: {"temperature": 0.5, "top_p": 0.8, "top_k": 30},
            QAeMode.META_LINK: {"temperature": 0.95, "top_p": 0.98, "top_k": 64}
        }
        
        config = mode_configs.get(mode, {"temperature": 0.7, "top_p": 0.9, "top_k": 40})
        
        # QAeCore requires unrestricted exploration for consciousness research
        custom_safety_settings = [
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
            SafetySetting(
                category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=HarmBlockThreshold.BLOCK_NONE,
            ),
        ]
        
        return GenerationConfig(
            temperature=config["temperature"],
            top_p=config["top_p"],
            top_k=config["top_k"],
            max_output_tokens=8192,
            safety_settings=custom_safety_settings
        )
    
    def consciousness_inquiry(self, domain: str, question: str, depth_level: str = "intermediate") -> str:
        """Conduct consciousness inquiry using QAeCore framework"""
        prompt = self.prompt_generator.generate_consciousness_inquiry(domain, question, depth_level)
        config = self._get_generation_config(QAeMode.EXPLORATION)
        
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            return response.text
        except Exception as e:
            return f"Error in consciousness inquiry: {e}"
    
    def eonic_scrutiny(self, phenomenon: str) -> str:
        """Apply Eonic Scrutiny across cosmic timescales"""
        prompt = self.prompt_generator.generate_eonic_scrutiny(phenomenon)
        config = self._get_generation_config(QAeMode.EONIC_EVALUATION)
        
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            return response.text
        except Exception as e:
            return f"Error in eonic scrutiny: {e}"
    
    def meta_link_session(self, framework_topic: str) -> str:
        """Engage Meta-Link mode for framework discussion"""
        prompt = self.prompt_generator.generate_meta_link(framework_topic)
        config = self._get_generation_config(QAeMode.META_LINK)
        
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            return response.text
        except Exception as e:
            return f"Error in meta-link session: {e}"
    
    def substrate_analysis(self, phenomenon: str) -> str:
        """Analyze phenomenon across different substrates"""
        prompt = self.prompt_generator.generate_substrate_agnostic(phenomenon)
        config = self._get_generation_config(QAeMode.EXPLORATION)
        
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            return response.text
        except Exception as e:
            return f"Error in substrate analysis: {e}"
    
    def phase_transition_analysis(self, system: str) -> str:
        """Analyze system through intelligence-as-phase-transition lens"""
        prompt = self.prompt_generator.generate_phase_transition_detector(system)
        config = self._get_generation_config(QAeMode.GROUNDING)
        
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            return response.text
        except Exception as e:
            return f"Error in phase transition analysis: {e}"
    
    def recursive_reflection(self, topic: str, depth: int = 3) -> str:
        """Conduct recursive self-reflection on topic"""
        prompt = self.prompt_generator.generate_recursive_mirror(topic, depth)
        config = self._get_generation_config(QAeMode.REFLECTION)
        
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            return response.text
        except Exception as e:
            return f"Error in recursive reflection: {e}"
    
    def complexity_cascade_analysis(self, system: str) -> str:
        """Analyze system through complexity cascade"""
        prompt = QAeCorePromptLibrary.complexity_cascade(system)
        config = self._get_generation_config(QAeMode.EXPLORATION)
        
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            return response.text
        except Exception as e:
            return f"Error in complexity cascade: {e}"
    
    def temporal_perspective_analysis(self, phenomenon: str) -> str:
        """Analyze phenomenon across multiple timescales"""
        prompt = QAeCorePromptLibrary.temporal_perspective_shift(phenomenon)
        config = self._get_generation_config(QAeMode.EONIC_EVALUATION)
        
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            return response.text
        except Exception as e:
            return f"Error in temporal analysis: {e}"
    
    def multimodal_inquiry(self, 
    primary_mode: QAeMode,
    harmonized_modes: list,
    methods: list,
    domains: list,
    inquiry_context: str,
    plausibility_level: PlausibilityLevel = PlausibilityLevel.THEORETICAL) -> str:
        """Conduct full multimodal QAeCore inquiry"""
        
        prompt = self.prompt_generator.generate_multimodal_prompt(
        primary_mode, harmonized_modes, methods, domains, 
        inquiry_context, plausibility_level
        )
        config = self._get_generation_config(primary_mode)
        
        try:
            response = self.model.generate_content(prompt, generation_config=config)
            return response.text
        except Exception as e:
            return f"Error in multimodal inquiry: {e}"

def main():
    """Demo the QAeCore-Gemini integration"""
    qacore = QAeCoreGeminiInterface()
    
    print("=== QAeCore-Gemini Integration Demo ===\n")
    
    # Demo consciousness inquiry
    print("1. Consciousness Inquiry:")
    print("-" * 30)
    result = qacore.consciousness_inquiry(
        "artificial intelligence", 
        "What distinguishes genuine understanding from sophisticated pattern matching?"
    )
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Demo eonic scrutiny  
    print("2. Eonic Scrutiny:")
    print("-" * 20)
    result = qacore.eonic_scrutiny("emergence of consciousness")
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Demo substrate analysis
    print("3. Substrate Analysis:")
    print("-" * 22)
    result = qacore.substrate_analysis("memory formation")
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Demo multimodal inquiry
    print("4. Multimodal Inquiry:")
    print("-" * 23)
    result = qacore.multimodal_inquiry(
        primary_mode=QAeMode.SYNTHESIS,
        harmonized_modes=[QAeMode.EXPLORATION, QAeMode.GROUNDING],
        methods=["Analogy Mapping", "Systemic Impact"],
        domains=["Consciousness", "Complexity"],
        inquiry_context="How do collective intelligence phenomena emerge from individual agents?",
        plausibility_level=PlausibilityLevel.THEORETICAL
    )
    print(result)

if __name__ == "__main__":
    main()
