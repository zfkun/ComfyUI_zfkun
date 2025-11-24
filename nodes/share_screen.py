from PIL import Image

from ..utils import base642pil, pil2tensor, tensor2pil

class ZFShareScreen:

    @classmethod
    def INPUT_TYPES(cls):
        return {
                "required": {
                    "image_base64": ("BASE64"),
                },
                "optional": {
                    "default_image": ("IMAGE",{
                        "tooltip": "Fallback image used when reading from the shared screen fails"
                    }),
                    "RGBA": ([False, True], {
                        "default": False,
                        "tooltip": "Whether to export the image in RGBA format"
                    }),
                    "prompt": ("STRING", {
                        "multiline": True,
                        "dynamicPrompts": True,
                        "tooltip": "Prompt for further adjustments to the read image"
                    }),
                    "weight": ("FLOAT", {
                        "default": 1,
                        "min": 0,
                        "max": 1,
                        "step": 0.01,
                        "tooltip": "Weight for further adjustments to the read image"
                    }),
                    "seed": ("INT", {
                        "default": 0,
                        "min": 0,
                        "max": 0xffffffffffffffff,
                        "tooltip": "Random seed for further adjustments to the read image"
                    }),
                },
                "hidden": {"extra_pnginfo": "EXTRA_PNGINFO", "unique_id": "UNIQUE_ID"},
            }

    CATEGORY = "zfkun 🍕🅩🅕"
    OUTPUT_NODE = True

    RETURN_TYPES = ("IMAGE", "STRING", "FLOAT", "INT")
    RETURN_NAMES = ("image", "prompt", "weight", "seed")
    FUNCTION = "doit"
    DESCRIPTION = "Reads real-time images from the shared screen, supporting area cropping and prompt adjustment."

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
