from PIL import Image

from ..utils import base642pil, pil2tensor, tensor2pil

class ZFShareScreen:

    @classmethod
    def INPUT_TYPES(cls):
        return {
                "required": {
                    "image_base64": ("BASE64",),
                },
                "optional": {
                    "default_image": ("IMAGE",),
                    "RGBA": ([False, True], {"default": False}),
                    "prompt": ("STRING", {"multiline": True, "dynamicPrompts": True}),
                    "weight": ("FLOAT", {"default": 1, "min": 0, "max": 1, "step": 0.01}),
                    "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
                },
                "hidden": {"extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"},
            }

    CATEGORY = "zfkun 🍕🅩🅕"
    OUTPUT_NODE = True

    RETURN_TYPES = ("IMAGE", "STRING", "FLOAT", "INT")
    RETURN_NAMES = ("image", "prompt", "weight", "seed")
    FUNCTION = "doit"

    def doit(self, image_base64, default_image=None, RGBA=False, prompt=None, weight=None, seed=None, extra_pnginfo=None, unique_id=None):
        if isinstance(image_base64, str):
            image = base642pil(image_base64)
        else:
            image = None
        
        if image is None:
            # 自定义兜底
            if default_image is not None:
                image = tensor2pil(default_image)
            else:
                if RGBA:
                    image = Image.new(mode='RGBA', size=(512, 512), color=(0, 0, 0, 0))
                else:    
                    image = Image.new(mode='RGB', size=(512, 512), color=(0, 0, 0))
        
        image = pil2tensor(image.convert('RGBA' if RGBA else 'RGB'))

        return (image, prompt, weight, seed,)
