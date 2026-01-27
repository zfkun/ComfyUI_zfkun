class ZFSplitText:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "tooltip": "Original texts content to be split"
                }),
                "delimiter": ("STRING", {"default": "&", "tooltip": "Separator"})
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
    OUTPUT_IS_LIST = (True, )
    OUTPUT_NODE = True

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("texts",)
    FUNCTION = "doit"
    DESCRIPTION = "Split text to list"

    def doit(self, text, delimiter, **kwargs):
        texts = text.split(delimiter)
        return {"ui": {"string": [texts,]}, "result": (texts,)}

