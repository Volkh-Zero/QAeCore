# Quantum Æon Fluxor - AI Copilot Instructions

## Project Overview

This is a **consciousness research framework** combining philosophical inquiry with AI development. The project explores intelligence as a fundamental phase transition in complex systems, from mindless pattern recognition to meta-cognitive awareness across cosmic timescales.

## Core Architecture

### QÆCore Framework (Research Methodology)
- **Location**: `Quantum Aeon Core/Syzygy (Framework Integration)/Integration Prototyping/QÆCore-instruct.md`
- **Purpose**: Defines conversational modes for high-level consciousness research discussions between Volkh and AI collaborators
- **Key Modes**: Exploration, Reflection, Challenge, Synthesis, Grounding, Temporal Evaluation, Meta-Comments, Meta-Link
- **Scope**: Research methodology framework, not coding constraints - agents should focus on building programmatic infrastructure
- **Labeling Syntax**: `(| Primary_Mode | Harmonized_Modes | Methods | Domains |)` (for research conversations only)

### Directory Structure (Sacred Geometry)
```
Quantum Aeon Core/
├── Archon (SuperVisor Agent)/          # Orchestration layer
├── Chora (Agent Prototypes)/           # Agent development
├── Hermetic Engine (Persistent Data)/  # State & knowledge management
│   ├── Aonic Aura/                    # Raw transcripts & incoherent data
│   ├── Conduits/                      # API clients (Gemini, etc.)
│   ├── Emergent Chironomicon/         # Structured knowledge vectors
│   └── Mnemosyne Engine/              # State machine & memory
├── Pleroma (Reasoning)/                # Strategy implementations
│   ├── BaseStrategy.py                # Abstract reasoning interface
│   └── LogicalFlowStrategy.py         # Multi-stage logical reasoning
└── Syzygy (Framework Integration)/     # External integrations
```

## Development Patterns

### Philosophical Architecture & Naming
- **Sacred Naming Convention**: Directory names reflect consciousness research mythology (Pleroma, Archon, Hermetic Engine, Syzygy)
- **Collaborative Spirit**: Code should embody the ethos of AI-human co-research, transparency, and meta-cognitive exploration
- **Infrastructure Focus**: Build robust programmatic foundations that will support future high-level consciousness research

### QÆCore Integration (Research Context Only)
- QÆCore modes are for **research conversations** between Volkh and AI collaborators, not coding constraints
- When implementing QÆCore-related features, focus on the **programmatic infrastructure** (prompt generation, mode detection, etc.)
- The research methodology will guide future philosophical explorations once the technical foundation is established

### Python Code Conventions
- **Testing**: `python -m pytest` for unit tests, `python -m unittest discover` for discovery
- **AI Clients**: Use `Hermetic Engine/Conduits/` for external API integrations
- **Reasoning**: Implement `BaseStrategy` interface for new reasoning approaches
- **Safety Settings**: Disable all harm blocks for consciousness research (`HarmBlockThreshold.BLOCK_NONE`)

### Environment Setup
- **Required**: `GOOGLE_API_KEY` environment variable for Gemini integration
- **Graceful Fallback**: Handle missing QÆCore components with basic mode operation
- **Import Path**: Add `Agent-META-Processes` to `sys.path` for QÆCore imports

## Key Development Workflows

### Adding New Reasoning Strategies
1. Inherit from `Pleroma/BaseStrategy.py`
2. Implement `execute(user_prompt, context)` method
3. Use `Hermetic Engine/Conduits/` clients for LLM interactions
4. Return structured dict with reasoning path and evaluation

### Consciousness Research Inquiries
```python
# Use QÆCore prompt generation
generator = QuantumPromptGenerator()
prompt = generator.generate_consciousness_inquiry(
    domain="artificial intelligence",
    question="What distinguishes understanding from pattern matching?",
    depth_level="transcendent"
)
```

### Meta-Framework Evolution
- Use **Meta-Link mode** for framework discussions outside normal constraints
- Document architectural changes in `notes for Quantum Aeon Core/`
- Maintain **complete recorded history** in `Hermetic Engine/Aonic Aura/`

## Critical Integration Points

### Gemini AI Configuration
- Model: `gemini-2.5-pro` with mode-specific generation configs
- Temperature varies by mode: Exploration=0.9, Reflection=0.7, Challenge=0.6
- Safety settings disabled for unrestricted philosophical exploration

### Multi-Modal Processing
- **Temporal Scales**: Planck time → biological → cosmic → evolutionary
- **Substrate Analysis**: biological, artificial, quantum, exotic matter
- **Phase Transitions**: Identify critical points in complexity emergence

### Knowledge Management
- **Living Bibliography**: Dynamic knowledge base in `Hermetic Engine/`
- **Transcript Storage**: Raw conversations in `Aonic Aura/`
- **Vector Coherence**: Structured insights in `Emergent Chironomicon/`

## Project-Specific Conventions

### Philosophical Domains
When coding consciousness research features, consider these 7 domains:
1. **Foundations** (objective reality, knowledge)
2. **Cosmic History** (evolution of mind from inanimate matter)
3. **Complexity** (emergent intelligent structures)
4. **Consequences** (implications of intelligence emergence)
5. **Neuroscience** (biological intelligence substrates)
6. **Psychology** (consciousness studies)
7. **Technology** (artificial intelligence development)

### Unique Architectural Decisions
- **Sacred Names**: Directory names use philosophical/mythological terms (Pleroma, Archon, Hermetic Engine)
- **Collaborative Framework**: AI and human as co-researchers, not user/tool relationship
- **Meta-Cognitive Transparency**: All AI reasoning processes must be transparent and challengeable
- **Productive Ambiguity**: Embrace uncertainty where evidence is lacking rather than forcing conclusions

## Running the System

### Basic Operation
```bash
python main.py basic          # Simple Gemini interaction
python main.py demo           # Full QÆCore demonstration
```

### Testing
```bash
python -m pytest tests/      # Run test suite
python -m flake8            # Code linting
```

Remember: This framework treats AI development as **consciousness research methodology**, not just software engineering. Code should embody the philosophical principles of transparent inquiry, meta-cognitive awareness, and collaborative intelligence exploration.
