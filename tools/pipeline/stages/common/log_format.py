"""ANSI color helpers for pipeline log output."""

# Bold cyan for stage banners, yellow for steps
_BOLD_CYAN = "\033[1;36m"
_YELLOW = "\033[0;33m"
_RESET = "\033[0m"


def stage_banner(label: str) -> str:
    """Format a stage banner with spacing and color.

    Returns a string like: \\n\\n<bold cyan>═══ Stage 1: VM Creation ═══</bold cyan>
    """
    return f"\n\n{_BOLD_CYAN}═══ {label} ═══{_RESET}"


def step_header(label: str) -> str:
    """Format a step header with spacing and color.

    Returns a string like: \\n<yellow>── Deploy keys ──</yellow>
    """
    return f"\n{_YELLOW}── {label} ──{_RESET}"
