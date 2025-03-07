"""
Models module initialization.
Contains additional filters for HuggingFace and Transformers-related warnings.
"""

import warnings

# Filter out specific warnings that occur when using HuggingFace models
warnings.filterwarnings("ignore", message="torch.utils._pytree._register_pytree_node is deprecated")
warnings.filterwarnings("ignore", message="`resume_download` is deprecated")
