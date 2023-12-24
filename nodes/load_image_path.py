import os
from hashlib import sha256
from urllib.parse import urlparse
from urllib import request

import torch
from PIL import Image

from ..utils import printColorError, tensor2pil, pil2tensor, pil2mask

class ZFLoadImagePath:

    @classmethod
    def INPUT_TYPES(cls):
        return {
                "required": {
                    "image_path": ("STRING", {"default": './input/example.png'}),
                    "RGBA": ([False, True], {"default": False}),
                },
                "optional": {
                    "default_image": ("IMAGE",),
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

    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("image", "mask", "filename")
    FUNCTION = "doit"

    def doit(self, image_path, default_image=None, RGBA=False, prompt=None, extra_pnginfo=None, unique_id=None):
        filename = ''
        img: Image = None

        if image_path.startswith('http'):
            filename = os.path.basename(urlparse(image_path).path)
            img = self.download(image_path)
        else:
            image_path = os.path.expanduser(image_path)
            filename = os.path.basename(image_path)

            try:
                img = Image.open(image_path)
            except Exception as e:
                printColorError(f'image open fail: {image_path.strip()}, {e}')
                img = None

        if img is None:
            # 自定义兜底
            if default_image is not None:
                img = tensor2pil(default_image)

            # 新建兜底
            if img is None:
                try:
                    img = Image.new(mode='RGB', size=(512, 512), color=(0, 0, 0))
                    filename = ''
                except Exception as e:
                    printColorError(f'create empty image fail: {e}')
                    img = None

        if img is None:
            return

        # 导出图像
        res = pil2tensor(img.convert('RGBA' if RGBA else 'RGB'))

        # 导出遮罩
        if 'A' in img.getbands():
            mask = pil2mask(img.getchannel('A'))
        else:
            mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")

        return (res, mask, filename)

    def download(self, url):
        try:
            from io import BytesIO

            with request.urlopen(url) as response:
                img_data = response.read()
        except request.URLError as e:
            printColorError("image download faile: URL Error,", e.reason)
        except request.HTTPError as e:
            printColorError("image download faile: HTTP Error,", e.code, e.reason)
        except request.ContentTooShortError as e:
            printColorError("image download faile: Content Too Short, ", e.content)
        except Exception as e:
            printColorError("image download faile: Unexpected Error:", str(e))
        else:
            img = Image.open(BytesIO(img_data))
            return img

    @classmethod
    def IS_CHANGED(cls, image_path):
        if image_path.startswith('http'):
            return float("NaN")
        m = sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()
