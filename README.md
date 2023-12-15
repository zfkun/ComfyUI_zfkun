# ComfyUI zfkun

**Custom nodes pack for ComfyUI**

# ChangeLog

## 2023-12-16

- update version to `0.0.3`

- add [niutrans](https://bobtranslate.com/service/translate/niu.html) platform for text translate node

## 2023-12-15

- update version to `0.0.2`

- add auto converting encoding to `utf-8` for `config.yaml`

- add auto install requirements

## 2023-12-08

- add [baidu](https://bobtranslate.com/service/translate/baidu.html), [alibaba](https://bobtranslate.com/service/translate/ali.html), [tencent](https://bobtranslate.com/service/translate/tencent.html), [volcengine](https://bobtranslate.com/service/translate/volcengine.html) platform for text translate node

- update README

# Installation

## Using ComfyUI Manager (recommended)

Install [ComfyUI Manager](https://github.com/ltdrdata/ComfyUI-Manager) and do steps introduced there to install this repo.

## Alternative

```shell
cd ComfyUI/custom_nodes/
git clone https://github.com/zfkun/ComfyUI_zfkun

# comfyui use system python
pip install -r requirements.txt

# if comfyui use venv
# path/to/ComfUI/venv/bin/python -s -m pip install -r requirements.txt

# restart ComfyUI
```

## Nodes

### Preview Text

support text、primitive (text) for input

### Preview Text (Multiline)

support text、primitive (clip text) for input

### Text Translation

support platforms:

- [baidu (百度翻译)](https://bobtranslate.com/service/translate/baidu.html)
- [alibaba (阿里翻译)](https://bobtranslate.com/service/translate/ali.html)
- [tencent (腾讯翻译)](https://bobtranslate.com/service/translate/tencent.html)
- [volcengine (火山翻译)](https://bobtranslate.com/service/translate/volcengine.html)
- [niutrans (小牛翻译)](https://bobtranslate.com/service/translate/niu.html)

> 1. create `config.yaml` (copy from `config.yaml.example`, **make sure file encoding** is `utf-8`)
> 2. update `translator` field, save
> 3. restart `ComfyUI`

# Examples

## Preview Text

![](./example_preview_text.png)

## Preview Text (Multiline)

![](./example_preview_text_multiline.png)

## Text Translation

![](./example_text_translate.png)
