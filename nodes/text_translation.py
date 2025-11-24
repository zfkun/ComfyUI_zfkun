from ..utils import TRANSLATOR_PLATFORMS, LANGUAGE_CODES, text_translate

class ZFTextTranslation:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "tooltip": "Original text content to be translated"
                }),
                "platform": ([*TRANSLATOR_PLATFORMS], {
                    "default": "baidu",
                    "tooltip": "Translation platform to be used"
                }),
                "source": (["auto", *LANGUAGE_CODES], {
                    "default": "auto",
                    "tooltip": "Source language of the text to be translated"
                }),
                "target": ([*LANGUAGE_CODES,], {
                    "default": "en",
                    "tooltip": "Target language into which the text is to be translated"
                }),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"},
        }

    # 🍕
    # Unicode: U+1F355
    # UTF-16: \uD83C\uDF55
    # 🅩
    # Unicode: U+1F171
    # UTF-16: \uD83C\uDD71
    # 🅕
    # Unicode: U+1F165
    # UTF-16: \uD83C\uDD65
    CATEGORY = "zfkun 🍕🅩🅕"
    OUTPUT_NODE = True

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("text", "platform", "source", "target")
    FUNCTION = "doit"
    DESCRIPTION = "Multilingual text translation node, supporting numerous free platforms"

    def doit(self, text:str, platform="baidu", source="auto", target="en", prompt=None, extra_pnginfo=None, unique_id=None):
        (result, fromLanguage, toLanguage,) = text_translate(platform, text, source, target)
        return {
            "ui": {"string": [result, platform, fromLanguage, toLanguage,],},
            # "result": (result, platform, fromLanguage, toLanguage,),
            "result": (result, platform, fromLanguage, toLanguage,),
        }
    