# Share Screen 🍕🅩🅕

Reads real-time images from the shared screen, supporting area cropping and prompt adjustment.

## Feature

- support window capture、screen share、camera capture ..
- support multiple share node at the same time
- support custom clip area
- support custom refresh duration
- support default image (`RGBA` support)
- support weight and prompt

## Parameter

- **image_base64**: Base64 image data
- **default_image**: Fallback image used when the shared screen reading fails
- **RGBA**: Whether to export the image in RGBA format
- **prompt**: Prompt for further adjustments to the read image
- **weight**: Weight for further adjustments to the read image

    > range: [0, 1], setp: 0.01, default: 1

- **seed**: Random seed for further adjustments to the read image

    > range: [0, 1000000000], default: 0

- **control_after_generate**: Whether to apply control after generating the image

    > options: ["fixed", "increment", "decrement", "randomize"], default: "randomize"

## Usage

![Example](../../../example_workflows/preview_text.jpg)

## Server

I have also provided two lightweight server-side programs. These programs are used to collect and generate images to the local system in real time, and provide support for the `image_base64` parameter of this node.

- [Camera Capture Simple](https://github.com/zfkun/ComfyUI_zfkun?tab=readme-ov-file#camera-capture-simple)

- [Window Capture Simple Server](https://github.com/zfkun/ComfyUI_zfkun?tab=readme-ov-file#camera-capture-simple)

