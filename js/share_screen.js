import { app } from "/scripts/app.js";
import { $el } from "/scripts/ui.js";

const NODE_WIDGET_SPACE = 4;
const NODE_WIDGET_MARGIN = 16;

const runtime = {
  screen: {
    // [nodeId]: {
    //   blob: Blob,
    //   base64: String,
    // }
  },
  ssv: {
    // canvas: null,
    // ctx: null,
  },
  apd: {
    // canvas: null,
    // ctx: null,
  },
  startShare: function (id, video) {
    return new Promise((resolve) => {
      navigator.mediaDevices
        .getDisplayMedia({ video: true })
        .then((stream) => {
          video.srcObject = stream;

          if (!this.screen[id]) this.screen[id] = {};
          this.screen[id].stream = stream;
          this.screen[id].video = video;

          stream.addEventListener("inactive", () => {
            runtime.stopShare(id);
          });

          resolve(true);
        })
        .catch((e) => {
          console.info("[zfkun 🍕🅩🅕] get display media fail: ", id, e);
          resolve(false);
        });
    });
  },
  stopShare: function (id) {
    if (!this.screen[id]) return this;

    if (this.screen[id].stream) {
      this.screen[id].stream.stop?.();
      this.screen[id].stream = null;
    }

    if (this.screen[id].video) {
      this.screen[id].video.pause?.();
      if (this.screen[id].video.srcObject) {
        this.screen[id].video.srcObject.getTracks?.()?.forEach?.((track) => {
          track.stop();
        });
        this.screen[id].video.srcObject = null;
      }
      this.screen[id].video = null;
    }
  },
  saveFrame: async function (id, video, update = false) {
    if (!this.screen[id]) {
      console.info("[zfkun 🍕🅩🅕] screen cache invalid: ", id);
      return;
    }

    const x = 0;
    const y = 0;
    const width = video.videoWidth;
    const height = video.videoHeight;

    if (!this.ssv.canvas) this.ssv.canvas = new OffscreenCanvas(512, 512);
    this.ssv.canvas.width = width;
    this.ssv.canvas.height = height;

    if (!this.ssv.ctx) this.ssv.ctx = this.ssv.canvas.getContext("2d");
    this.ssv.ctx.drawImage(video, x, y, width, height, 0, 0, width, height);

    if (!this.screen[id]) this.screen[id] = {};

    try {
      this.screen[id].blob = await this.ssv.canvas.convertToBlob({
        type: "image/jpeg",
        quality: 1,
      });

      if (update)
        this.screen[id].base64 = await this.blobToBase64(this.screen[id].blob);
    } catch (e) {
      console.info("[zfkun 🍕🅩🅕] video convert to blob fail: ", id, e);
    }
  },
  getScreenBase64: function (id) {
    return this.screen[id]?.base64 || "";
  },
  averagePixelDifference: function (img1, img2, channels = 3) {
    const pixels = [];

    if (!this.apd.canvas) this.apd.canvas = document.createElement("canvas");
    if (!this.apd.ctx) this.apd.ctx = this.apd.canvas.getContext("2d");

    [img1, img2].forEach((img, i) => {
      const { width, height } = img;

      this.apd.canvas.width = width;
      this.apd.canvas.height = height;

      this.apd.ctx.drawImage(img, 0, 0, width, height);
      pixels[i] = this.apd.ctx.getImageData(0, 0, width, height).data;
    });

    channels = Math.min(Math.max(channels, 1), 3);

    let diff = 0;
    for (let i = 0; i < pixels[0].length; i += 4) {
      for (let j = 0; j < channels; j++) {
        diff += Math.abs(pixels[0][i + j] - pixels[1][i + j]);
      }
    }

    return diff / (img1.width * img1.height * channels);
  },
  blobToBase64: async function (blob) {
    return new Promise((resolve) => {
      const r = new FileReader();
      r.onload = function (e) {
        resolve(e.target.result);
      };
      r.on;
      r.readAsDataURL(blob);
    });
  },
  computePreviewY: function (node, ignoreNodes = []) {
    let y =
      LiteGraph.NODE_WIDGET_HEIGHT *
        Math.max(node.inputs.length, node.outputs.length) +
      NODE_WIDGET_SPACE;

    let widgetHeight = 0;
    for (let i = 0; i < node.widgets.length; i++) {
      const w = node.widgets[i];
      if (ignoreNodes.indexOf(w.name) >= 0) continue;

      if (w.computedHeight) {
        widgetHeight += w.computedHeight;
      } else if (w.computeSize) {
        widgetHeight += w.computeSize()[1] + NODE_WIDGET_SPACE;
      } else {
        widgetHeight += LiteGraph.NODE_WIDGET_HEIGHT + NODE_WIDGET_SPACE;
      }
    }

    return y + widgetHeight;
  },
};
window.runtime = runtime;

app.registerExtension({
  name: "Comfy.Zfkun.ShareScreen",
  async getCustomWidgets(app) {
    return {
      BASE64(node, inputName, inputData, app) {
        const widget = {
          type: inputData[0],
          name: inputName,
          size: [0, 0],
          draw(ctx, node, widget_width, y, widget_height) {},
          computeSize(...args) {
            return [0, 0];
          },
          async serializeValue(node, widgetIndex) {
            return runtime.getScreenBase64(node.id);
          },
        };
        node.addCustomWidget(widget);
        return widget;
      },
    };
  },
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name !== "ZFShareScreen") return;

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      onNodeCreated?.apply(this, arguments);

      const self = this;

      // btn
      this.addWidget(
        "button",
        "Start Share Screen",
        "",
        function (value, widget, node) {
          if (runtime.screen[node.id]?.stream) {
            this.label = "Start Share Screen";
            runtime.stopShare(node.id);
          } else {
            runtime
              .startShare(node.id, previewWidget.videoEl)
              .then((succes) => {
                if (succes) this.label = "Stop Share Screen";
              });
          }
        },
        {
          value: "",
          serialize: false,
        }
      );

      // preview
      const previewWidget = {
        type: "DOM",
        name: "preview",
        value: "",
        draw: function (ctx, node, widget_width, y, widget_height) {
          // const node_height = node.size[1];
          const ty = runtime.computePreviewY(node, [this.name]);

          const r = ctx.canvas.getBoundingClientRect();
          const transform = new DOMMatrix()
            .scaleSelf(r.width / ctx.canvas.width, r.height / ctx.canvas.height)
            .multiplySelf(ctx.getTransform())
            .translateSelf(NODE_WIDGET_MARGIN, ty + 2);

          Object.assign(this.parentEl.style, {
            transformOrigin: "0 0",
            transform: transform,
            left: 0,
            top: 0,
            cursor: "pointer",
            position: "absolute",
            maxWidth: `${widget_width - NODE_WIDGET_MARGIN * 2}px`,
            width: `${widget_width - NODE_WIDGET_MARGIN * 2}px`,
          });

          this.computedHeight = this.parentEl.getBoundingClientRect().height;
        },
        computedHeight: 250,
        computeSize: function (width) {
          return [width, this.computedHeight];
        },
      };
      this.addCustomWidget(previewWidget);

      const onRemoved = this.onRemoved;
      this.onRemoved = function () {
        previewWidget.videoEl?.remove?.();
        previewWidget.parentEl?.remove?.();
        onRemoved?.();
      };

      previewWidget.parentEl = $el("div", {});
      previewWidget.videoEl = $el("video", {
        style: {
          width: "100%",
        },
        controls: true,
        muted: true,
      });
      previewWidget.videoEl.addEventListener("loadedmetadata", function () {
        previewWidget.aspectRatio = this.videoWidth / this.videoHeight;
        previewWidget.videoEl.play();
      });
      previewWidget.videoEl.addEventListener("timeupdate", function () {
        runtime.saveFrame(self.id, this, true);
      });
      // previewWidget.videoEl.addEventListener("error", () => {
      //   previewWidget.parentEl.hidden = true;
      // });

      previewWidget.parentEl.appendChild(previewWidget.videoEl);
      document.body.appendChild(previewWidget.parentEl);

      this.serialize_widgets = true;
    };
  },
});
