from .utils import VERSION, printColor, load_config
from .nodes.preview_text import ZFPreviewText
from .nodes.preview_text_multiline import ZFPreviewTextMultiline
from .nodes.text_translation import ZFTextTranslation
from .nodes.load_image_path import ZFLoadImagePath
from .nodes.share_screen import ZFShareScreen


NODE_CLASS_MAPPINGS = {
    "ZFPreviewText": ZFPreviewText,
    "ZFPreviewTextMultiline": ZFPreviewTextMultiline,
    "ZFTextTranslation": ZFTextTranslation,
    "ZFLoadImagePath": ZFLoadImagePath,
    "ZFShareScreen": ZFShareScreen,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZFPreviewText": "Preview Text 🍕🅩🅕",
    "ZFPreviewTextMultiline": "Preview Text (Multiline) 🍕🅩🅕",
    "ZFTextTranslation": "Text Translation 🍕🅩🅕",
    "ZFLoadImagePath": "Load Image Path 🍕🅩🅕",
    "ZFShareScreen": "Share Screen 🍕🅩🅕",
}

WEB_DIRECTORY = "./web/js"

__version__ = VERSION

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

printColor(f"boot start", "\033[1;35m")
load_config()
printColor(f"boot end", "\033[1;35m")