class ZFPreviewTextList:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "texts": ("STRING", {
                    "forceInput": True,
                    "multiline": True,
                    "tooltip": "Original texts content to be previewed"
                }),
            },
            "hidden": {"unique_id": "UNIQUE_ID",},
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
    INPUT_IS_LIST = True
    OUTPUT_IS_LIST = (True, )
    OUTPUT_NODE = True

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("texts",)
    FUNCTION = "doit"
    DESCRIPTION = "Simple and efficient text content preview (support list input)"

    def doit(self, texts, **kwargs):
        return {"ui": {"string": [texts,]}, "result": (texts,)}

