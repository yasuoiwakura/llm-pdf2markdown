"""Centralized debug logging function."""

def debug(verbose: int, level: int, *args):
    """Print debug message if verbose >= level.
    
    Args:
        verbose: The verbosity level (e.g., from config/env)
        level: The debug level of this message (1=info, 2=debug, 3=trace)
        *args: Arguments to print
    """
    if verbose >= level:
        print(f"[DEBUG:{level}]", *args)