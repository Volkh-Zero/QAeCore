# boot_archon.py
# Electric-Tide — Actuator ::Zero — Corp-Switchable Bootstrap
# Public mask: :ARC: — Private shells: :CHAOS:, :HATE:, :ACHE:

from __future__ import annotations
import os, sys, argparse, logging
from dataclasses import dataclass

# ——— Profiles ————————————————————————————————————————————————————————————————

@dataclass(frozen=True)
class CorpProfile:
    acronym: str
    name: str
    tagline: str
    crest: str  # short accent line under banner title
    color: str  # ANSI foreground
    muted: str  # dim variant

RESET = "\x1b[0m"
DIM   = "\x1b[2m"
FG    = {
    "ARC":   "\x1b[38;5;245m",  # cold graphite
    "CHAOS": "\x1b[38;5;111m",  # cyan blueprint
    "HATE":  "\x1b[38;5;203m",  # surgical red
    "ACHE":  "\x1b[38;5;177m",  # violet ache
}

CORP_PROFILES = {
    "arc": CorpProfile(
        acronym=":ARC:",
        name="The Aletheic Research Conglomerate",
        tagline="In Shadow, Precision.",
        crest="Aletheia Division | Unconcealment Engines",
        color=FG["ARC"],
        muted=DIM + FG["ARC"],
    ),
    "chaos": CorpProfile(
        acronym=":CHAOS:",
        name="Catalytic Heuristic Algorithmic Ontology Systems",
        tagline="Building Better Minds.",
        crest="Katalysis Program | Ontology Synthesis Cells",
        color=FG["CHAOS"],
        muted=DIM + FG["CHAOS"],
    ),
    "hate": CorpProfile(
        acronym=":HATE:",
        name="Hayden Accelerated Technology Emergence",
        tagline="In Shadow, Precision.",
        crest="Directive 19 | Surgical Accretion",
        color=FG["HATE"],
        muted=DIM + FG["HATE"],
    ),
    "ache": CorpProfile(
        acronym=":ACHE:",
        name="Aletheic Catalysis & Heuristic Engineering",
        tagline="Building Better Minds.",
        crest="Longing Vector | Pain-Gradient Research",
        color=FG["ACHE"],
        muted=DIM + FG["ACHE"],
    ),
}

# ——— Prefix style sheet ————————————————————————————————————————————————
# Standardized memo/log prefixes. Use short, legible, composable tokens.
# Pattern:
#   ::CELL:: CHANNEL — AGENCY — :CORP:
# Examples:
#   ::A0:: Field Report — Actuator — :ARC:
#   ::K3:: Deployment — Katalysis — :CHAOS:
#   ::H1:: Incident — Directorate — :HATE:
#   ::R5:: Lab Note — Reactor — :ACHE:

def make_prefix(cell: str = "A0", channel: str = "Field Report", agency: str = "Actuator", corp_acronym: str = ":ARC:") -> str:
    return f"::{cell}:: {channel} — {agency} — {corp_acronym}"

# ——— Banner ————————————————————————————————————————————————————————————————

def render_banner(profile: CorpProfile, width: int | None = None) -> str:
    title = f"{profile.acronym} — {profile.name}"
    tag   = profile.tagline
    crest = profile.crest

    content_width = max(len(title), len(tag) + 4, len(crest))
    box_width = max(content_width + 2, 56) if width is None else max(width, 40)

    top = "╔" + "═" * (box_width - 2) + "╗"
    bot = "╚" + "═" * (box_width - 2) + "╝"

    def line(s: str) -> str:
        pad = box_width - 2 - len(s)
        return "║" + s + " " * pad + "║"

    # color accents
    C = profile.color
    M = profile.muted
    R = RESET

    title_col = f"{C}{title}{R}"
    tag_col   = f"{M}{tag}{R}"
    crest_col = f"{M}{crest}{R}"

    rows = [
        top,
        line(" " + title_col),
        line("   " + tag_col),
        line(" " + crest_col),
        bot,
    ]
    return "\n".join(rows)

# ——— Logging wire-up ————————————————————————————————————————————————

class PrefixedFormatter(logging.Formatter):
    def __init__(self, prefix: str, color: str):
        super().__init__(fmt="%(message)s")
        self.prefix = prefix
        self.color = color

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        return f"{self.color}{self.prefix}{RESET} {base}"

def get_logger(prefix: str, color: str) -> logging.Logger:
    logger = logging.getLogger(prefix)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(PrefixedFormatter(prefix, color))
    logger.handlers = [handler]
    logger.propagate = False
    return logger

# ——— Argparse & ENV ————————————————————————————————————————————————

def resolve_profile(args) -> CorpProfile:
    # Priority: explicit args > env vars > default
    key = (args.corp_profile or os.getenv("ET_CORP_PROFILE", "arc")).lower()
    prof = CORP_PROFILES.get(key)
    if not prof:
        raise SystemExit(f"Unknown corp profile: {key}. Choose from: {', '.join(CORP_PROFILES)}")

    # Allow cosmetic overrides (acronym/name/tagline) via args or env
    acronym = args.corp or os.getenv("ET_CORP", prof.acronym)
    name    = args.corp_name or os.getenv("ET_CORP_NAME", prof.name)
    tagline = args.tagline or os.getenv("ET_TAGLINE", prof.tagline)
    crest   = args.crest or os.getenv("ET_CREST", prof.crest)
    color   = prof.color
    muted   = prof.muted

    return CorpProfile(acronym=acronym, name=name, tagline=tagline, crest=crest, color=color, muted=muted)

def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="boot_archon", add_help=True, description="Corp-skinnable bootstrap for Archon link.")
    p.add_argument("--corp-profile", choices=list(CORP_PROFILES.keys()), help="arc | chaos | hate | ache")
    p.add_argument("--corp", help="Override acronym, e.g., ':ARC:'")
    p.add_argument("--corp-name", help="Override full name")
    p.add_argument("--tagline", help="Override tagline")
    p.add_argument("--crest", help="Override crest line")
    p.add_argument("--cell", default="A0", help="Cell code for prefix")
    p.add_argument("--channel", default="Field Report", help="Channel label for prefix")
    p.add_argument("--agency", default="Actuator", help="Agency label for prefix")
    return p.parse_args(argv)

# ——— Main ————————————————————————————————————————————————————————————————

def boot(argv=None):
    args = parse_args(argv)
    profile = resolve_profile(args)

    banner = render_banner(profile)
    print("\n" + banner)
    print(f"{DIM}Link established:{RESET} Actuator ::Zero — Archon mainframe\n")

    prefix = make_prefix(cell=args.cell, channel=args.channel, agency=args.agency, corp_acronym=profile.acronym)
    logger = get_logger(prefix, profile.color)

    # Example emits
    logger.info("Handshake complete. Authentication lattice stabilized.")
    logger.info("Loading QAeCore v4.5 doctrines.")
    logger.info("Quantum Aeon Fluxor: primed.")

    # Return a small handle for callers/tests
    return {
        "profile": profile,
        "prefix": prefix,
        "logger": logger,
    }

if __name__ == "__main__":
    boot()
