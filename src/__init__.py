"""
Main package initialization.
Filter out specific warnings that come from dependencies.
"""

import warnings

# Filter out specific warnings
warnings.filterwarnings("ignore", message="torch.utils._pytree._register_pytree_node is deprecated")
warnings.filterwarnings("ignore", message="`resume_download` is deprecated")

# Set up version
__version__ = "0.1.0"
