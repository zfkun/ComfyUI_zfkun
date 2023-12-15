import os

from .utils import VERSION, ADDON_NAME, HOME_PATH, COMFY_WEB_EXTENSIONS_PATH, printColor, checkDir, addFilesToDir, load_config
from .nodes.preview_text import ZFPreviewText
from .nodes.preview_text_multiline import ZFPreviewTextMultiline
from .nodes.text_translation import ZFTextTranslation


NODE_CLASS_MAPPINGS = {
    "ZFPreviewText": ZFPreviewText,
    "ZFPreviewTextMultiline": ZFPreviewTextMultiline,
    "ZFTextTranslation": ZFTextTranslation,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ZFPreviewText": "Preview Text 🍕🅩🅕",
    "ZFPreviewTextMultiline": "Preview Text (Multiline) 🍕🅩🅕",
    "ZFTextTranslation": "Text Translation 🍕🅩🅕",
}

__version__ = VERSION

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

def install_nodes():
    js_folder = os.path.join(HOME_PATH, "js")
    install_folder = os.path.join(COMFY_WEB_EXTENSIONS_PATH, ADDON_NAME)

    checkDir(install_folder)
    addFilesToDir(js_folder, install_folder)

printColor(f"boot start", "\033[1;35m")
load_config()
install_nodes()
printColor(f"boot end", "\033[1;35m")