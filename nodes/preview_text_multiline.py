class ZFPreviewTextMultiline:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {
                    "forceInput": True,
                    "multiline": True,
                    "tooltip": "Original text content to be previewed"
                })
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

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "unique_id")
    FUNCTION = "doit"
    DESCRIPTION = "Simple and efficient multiline text content preview node (supports multiline content display)"

    def doit(self, text, prompt=None, extra_pnginfo=None, unique_id=None):
        return {"ui": {"string": [text, unique_id,]}, "result": (text, unique_id,)}

