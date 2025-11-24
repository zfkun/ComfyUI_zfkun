# Text Translation 🍕🅩🅕

Multilingual text translation node, supporting numerous free platforms

## Feature

- support platforms:

    - [baidu (百度翻译)](https://bobtranslate.com/service/translate/baidu.html)
    - [alibaba (阿里翻译)](https://bobtranslate.com/service/translate/ali.html)
    - [tencent (腾讯翻译)](https://bobtranslate.com/service/translate/tencent.html)
    - [volcengine (火山翻译)](https://bobtranslate.com/service/translate/volcengine.html)
    - [niutrans (小牛翻译)](https://bobtranslate.com/service/translate/niu.html)
    - [bigmodel (智谱 GLM)](https://bobtranslate.com/service/translate/zhipu.html)
        > default model: `glm-4-flash` (**free**)
        >
        > support model: `glm-4-plus`、`glm-4-air`、`glm-4-air-0111` (**Preview**)、`glm-4-airx`、`glm-4-long`、`glm-4-flashx`、`glm-4-flash` (**free**)
    - [siliconflow (硅基流动)](https://bobtranslate.com/service/translate/siliconflow.html)
        > default model: `Qwen/Qwen2.5-7B-Instruct` (**free**)
        >
        > support model: `Qwen/QwQ-32B`, `Pro/deepseek-ai/DeepSeek-R1`, `Pro/deepseek-ai/DeepSeek-V3`, `deepseek-ai/DeepSeek-R1`, `deepseek-ai/DeepSeek-V3`, `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B`, `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B`, `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` (**free**), `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` (**free**), `Pro/deepseek-ai/DeepSeek-R1-Distill-Qwen-7B`, `Pro/deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`, `deepseek-ai/DeepSeek-V2.5`, `Qwen/Qwen2.5-72B-Instruct-128K`, `Qwen/Qwen2.5-72B-Instruct`, `Qwen/Qwen2.5-32B-Instruct`, `Qwen/Qwen2.5-14B-Instruct`, `Qwen/Qwen2.5-7B-Instruct` (**free**), `Qwen/Qwen2.5-Coder-32B-Instruct`, `Qwen/Qwen2.5-Coder-7B-Instruct` (**free**), `Qwen/Qwen2-7B-Instruct` (**free**), `Qwen/Qwen2-1.5B-Instruct` (**free**), `Qwen/QwQ-32B-Preview`, `TeleAI/TeleChat2`, `THUDM/glm-4-9b-chat` (**free**), `Vendor-A/Qwen/Qwen2.5-72B-Instruct`, `internlm/internlm2_5-7b-chat` (**free**), `internlm/internlm2_5-20b-chat`, `Pro/Qwen/Qwen2.5-7B-Instruct`, `Pro/Qwen/Qwen2-7B-Instruct`, `Pro/Qwen/Qwen2-1.5B-Instruct`, `Pro/THUDM/chatglm3-6b`, `Pro/THUDM/glm-4-9b-chat`

## Parameter

- **text**: Original text content to be translated
- **platform**: Translation platform to be used
    - options:
        - baidu
        - alibaba
        - tencent
        - volcengine
        - niutrans
        - bigmodel
        - siliconflow
    - default: `baidu`
- **source**: Source language of the text to be translated
- **target**: Target language into which the text is to be translated

## Config

1. create `config.yaml` (copy from `config.yaml.example`, **make sure file encoding** is `utf-8`)
2. update `translator` field, save
3. restart `ComfyUI`

## Usage

![Example](../../../../example_workflows/text_translate.jpg)
