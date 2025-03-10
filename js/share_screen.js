import { api } from "/scripts/api.js";
import { app } from "/scripts/app.js";
import { $el } from "/scripts/ui.js";

const NODE_WIDGET_SPACE = 4;
const NODE_WIDGET_MARGIN = 16;

const WIDGET_NAME_START_SHARE_SCREEN = "Start Share Screen";
const WIDGET_NAME_SET_CLIP_AREA = "Set Clip Area";
const WIDGET_NAME_REFRESH_DURATION = "Refresh Duration";
const WIDGET_NAME_START_QUEUE = "Start Queue";
const WIDGET_NAME_PREVIEW = "preview";

const runtime = {
  screen: {
    // [nodeId]: {
    //   running: boolean,
    //   stream: MediaStream,
    //   video: HTMLVideoElement,
    //   blob: Blob,
    //   base64: string,
    //   area: { start: { x: number; y: number; }, end { x: number; y: number; }, width: number, height: number }
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
  ssa: {
    // canvas: null,
    // ctx: null,
    // resize: () => void,
    // update: () => void,
  },

  live: 0,
  liveTimer: 0,
  liveFrame: "",
  startQueue: async function (id, widget) {
    if (!this.screen[id]) {
      alert("Please start share screen first\n请先启动共享屏幕");
      return Promise.resolve(false);
    }

    if (this.live > 0) {
      console.info("[zfkun 🍕🅩🅕] other node is living: ", id);
      return Promise.resolve(false);
    }
    console.info("[zfkun 🍕🅩🅕] start queue: ", id, this.live);

    const duration =
      app.graph._nodes_by_id[id]?.widgets?.find?.(
        (w) => w.name === WIDGET_NAME_REFRESH_DURATION
      )?.value || 1000;

    this.live = id;
    this.liveTimer = clearTimeout(this.liveTimer);

    let count = 0;
    this.queueLoop = async function () {
      const q = await api.getQueue();
      if (q.Running < 1 && q.Pending < 1) {
        // change diff
        const currentFrame = runtime.getScreenBase64(id);
        if (currentFrame) {
          const img1 = await runtime.loadImage(runtime.liveFrame);
          const img2 = await runtime.loadImage(currentFrame);

          const apd = runtime.averagePixelDifference(img1, img2);
          // console.info("[zfkun 🍕🅩🅕] current frame APD: ", id, apd, duration);
          if (apd > 1) {
            runtime.liveFrame = currentFrame;

            await app.queuePrompt(0, app.ui.batchCount);
            widget.label = `Stop Queue (${++count})`;
          }
        }
      }

      // next
      runtime.liveTimer = setTimeout(runtime.queueLoop, duration);
    };

    await this.queueLoop();

    return Promise.resolve(true);
  },
  stopQueue: async function () {
    console.info("[zfkun 🍕🅩🅕] stop queue: ", this.live);
    this.liveTimer = clearTimeout(this.liveTimer);
    this.live = 0;
    this.liveFrame = "";
    return Promise.resolve(true);
  },

  startShare: function (id, video) {
    return new Promise((resolve) => {
      if (navigator.mediaDevices && navigator.mediaDevices.getDisplayMedia) {
        navigator.mediaDevices
          .getDisplayMedia({ video: true })
          .then((stream) => {
            video.srcObject = stream;

            if (!this.screen[id]) this.screen[id] = {};
            this.screen[id].stream = stream;
            this.screen[id].video = video;
            this.screen[id].running = true;

            stream.addEventListener("inactive", () => {
              runtime.stopShare(id);
            });

            resolve(true);
          })
          .catch((e) => {
            console.info("[zfkun 🍕🅩🅕] get display media fail: ", id, e);
            resolve(false);
            if (e.message === "Permission denied by system") {
              alert(
                "Please make sure your browser has the permission for `Screen Recording`\n请确保您的浏览器具有“屏幕录制”权限"
              );
            } else {
              alert(e.message);
            }
          });
      } else {
        console.info("[zfkun 🍕🅩🅕] get display media not support: ", id);
        alert("Error access screen content: your browser not support");
        resolve(false);
      }
    });
  },
  stopShare: function (id) {
    if (!this.screen[id]) return this;

    this.screen[id].running = false;

    this.stopClipArea();

    const area = app.graph._nodes_by_id[id]?.widgets?.find?.(
      (w) => w.name == WIDGET_NAME_PREVIEW
    )?.areaEl;
    if (area) area.innerHTML = "";

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

    if (!this.screen[id].running) {
      return;
    }

    const area = this.screen[id].area;

    const sx = area ? area.x : 0;
    const sy = area ? area.y : 0;
    const width = area ? area.w : video.videoWidth;
    const height = area ? area.h : video.videoHeight;

    if (!this.ssv.canvas) this.ssv.canvas = new OffscreenCanvas(512, 512);
    this.ssv.canvas.width = width;
    this.ssv.canvas.height = height;

    if (!this.ssv.ctx) this.ssv.ctx = this.ssv.canvas.getContext("2d");
    if (area) {
      this.ssv.ctx.drawImage(video, sx, sy, width, height, 0, 0, width, height);
    } else {
      this.ssv.ctx.drawImage(video, sx, sy, width, height, 0, 0, width, height);
    }

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

  loadImage: async function (src) {
    return new Promise((r) => {
      const img = new Image();
      img.onload = () => r(img);
      img.onerror = () => r(null);
      img.src = src;
    });
  },
  getScreenBase64: function (id) {
    return this.screen[id]?.base64 || "";
  },
  averagePixelDifference: function (img1, img2, channels = 3) {
    if (!img1 || !img2) return 999;

    if (img1.width !== img2.width || img1.height !== img2.height) return 2;

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

  // 计算缩放因子，用于处理图像缩放情况下的选区计算
  calculateClipAreaScaleFactor: function (videoWidth, videoHeight) {
    this.ssa.scaleFactor = Math.min(
      1,
      window.innerWidth / videoWidth,
      window.innerHeight / videoHeight
    );
  },
  // 转换选区矩形信息到适合 drawImage 方法使用的入参
  calculateDrawImageCoordinates: function (startX, startY, endX, endY) {
    // 无效选区 视作 不裁剪
    if (startX === endX || startY === endY) return;

    const res = {
      x: startX,
      y: startY,
      w: Math.abs(endX - startX),
      h: Math.abs(endY - startY),
    };

    // 终点 在 左侧
    if (endX < startX) {
      res.x = endX;

      // 终点 在 左上
      if (endY < startY) {
        res.y = endY;
      }
    }
    // 终点 在 右侧
    else {
      // 终点 在 右上
      if (endY < startY) {
        res.y = endY;
      }
    }

    return res;
  },
  startClipArea: function (id, video) {
    if (!this.screen[id]) {
      alert("Please start share screen first\n请先启动共享屏幕");
      return;
    }

    if (!this.ssa.canvas) {
      this.ssa.canvas = document.createElement("canvas");
      Object.assign(this.ssa.canvas.style, {
        position: "fixed",
        top: "50%",
        left: "50%",
        transform: "translate3d(-50%, -50%, 0) scale(1)",
        zIndex: 99999,
      });
      this.ssa.canvas.width = 0;
      this.ssa.canvas.height = 0;
      document.body.appendChild(this.ssa.canvas);
    }
    if (!this.ssa.ctx) this.ssa.ctx = this.ssa.canvas.getContext("2d");
    if (!this.ssa.info) {
      this.ssa.info = document.createElement("div");
      Object.assign(this.ssa.info.style, {
        position: "fixed",
        top: "10px",
        left: "10px",
        backgroundColor: "white",
        padding: "5px",
        borderRadius: "5px",
        zIndex: 999999,
        color: "red",
      });
      document.body.appendChild(this.ssa.info);
    }

    const width = video.videoWidth;
    const height = video.videoHeight;

    // init scale factor
    this.calculateClipAreaScaleFactor(width, height);

    const { area } = this.screen[id];
    const { canvas, ctx, info } = this.ssa;
    let isDrag = false;
    let startX = area ? area.x : 0;
    let startY = area ? area.y : 0;
    let endX = area ? area.x + area.w : 0;
    let endY = area ? area.y + area.h : 0;

    // 交互
    if (this.ssa.mouse) {
      canvas.removeEventListener("mousedown", this.ssa.mouse);
      canvas.removeEventListener("mousemove", this.ssa.mouse);
      canvas.removeEventListener("mouseup", this.ssa.mouse);
    }
    this.ssa.mouse = function (e) {
      const { type } = e;

      if (type === "mousedown") {
        // console.info("[zfkun 🍕🅩🅕] mousedown: ", e);
        isDrag = true;
        startX = endX = Math.round(e.offsetX);
        startY = endY = Math.round(e.offsetY);
      } else if (type === "mousemove") {
        if (!isDrag) return;

        endX = Math.round(e.offsetX);
        endY = Math.round(e.offsetY);

        runtime.ssa.update?.();
      } else if (type === "mouseup") {
        isDrag = false;

        if (runtime.screen[id]) {
          runtime.screen[id].area = runtime.calculateDrawImageCoordinates(
            startX,
            startY,
            endX,
            endY
          );
        }

        runtime.updateClipArea(id, width, height);

        runtime.stopClipArea(id);
      }
    };
    canvas.addEventListener("mousedown", this.ssa.mouse);
    canvas.addEventListener("mousemove", this.ssa.mouse);
    canvas.addEventListener("mouseup", this.ssa.mouse);

    // 自适应
    if (this.ssa.resize) window.removeEventListener("resize", this.ssa.resize);
    this.ssa.resize = function () {
      runtime.calculateClipAreaScaleFactor(width, height);

      canvas.width = width;
      canvas.height = height;
      canvas.style.transform = `translate3d(-50%, -50%, 0) scale(${runtime.ssa.scaleFactor})`;

      runtime.ssa.update?.();
    };
    window.addEventListener("resize", this.ssa.resize);

    // 重绘
    this.ssa.update = function () {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(video, 0, 0, width, height);

      // draw selection area
      ctx.beginPath();
      ctx.strokeStyle = "red";
      ctx.fillStyle = "rgba(255, 0, 0, 0.6)";
      ctx.setLineDash([5, 5]);
      ctx.strokeRect(startX, startY, endX - startX, endY - startY);
      ctx.fillRect(startX, startY, endX - startX, endY - startY);
      ctx.closePath();

      if (info) {
        info.textContent = `Selection: (${startX}, ${startY}) - (${endX}, ${endY}), Size: ${Math.abs(
          endX - startX
        )}x${Math.abs(endY - startY)}`;
      }
    };

    // 初始化
    this.ssa.resize?.();
  },
  updateClipArea: function (nodeId, videoWidth, videoHeight) {
    const node = app.graph._nodes_by_id[nodeId];
    if (!node) {
      console.info("[zfkun 🍕🅩🅕] node not found: ", nodeId);
      return;
    }

    const area = this.screen[nodeId]?.area;

    // update ui
    const btn = node.widgets.find((w) => w.name === WIDGET_NAME_SET_CLIP_AREA);
    if (btn) {
      btn.label = area
        ? `Change Clip Area (${area.w}x${area.h})`
        : "Set Clip Area";
      node.setDirtyCanvas(true);
    }

    const el = node.widgets.find((w) => w.name == WIDGET_NAME_PREVIEW)?.areaEl;
    if (!el) {
      console.info("[zfkun 🍕🅩🅕] preview area elment not found: ", nodeId);
      return;
    }

    if (!this.screen[nodeId]) {
      console.info("[zfkun 🍕🅩🅕] screen invalid: ", nodeId);
      return;
    }

    el.innerHTML = "";

    if (!area) return;

    // update preview
    const { x, y, w, h } = area;
    console.info("[zfkun 🍕🅩🅕] area info: ", area, app.graph);

    const canvas = document.createElement("canvas");
    canvas.width = videoWidth;
    canvas.height = videoHeight;
    canvas.style.width = "100%";

    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.beginPath();
    ctx.strokeStyle = "red";
    ctx.fillStyle = "rgba(255, 0, 0, 0.6)";
    ctx.setLineDash([5, 5]);
    ctx.strokeRect(x, y, w, h);
    ctx.fillRect(x, y, w, h);
    ctx.closePath();

    el.appendChild(canvas);
  },
  stopClipArea: function (nodeId) {
    if (this.ssa.mouse) {
      this.ssa.canvas?.removeEventListener?.("mousedown", this.ssa.mouse);
      this.ssa.canvas?.removeEventListener?.("mousemove", this.ssa.mouse);
      this.ssa.canvas?.removeEventListener?.("mouseup", this.ssa.mouse);
    }
    this.ssa.mouse = undefined;

    if (this.ssa.resize) window.removeEventListener("resize", this.ssa.resize);
    this.ssa.resize = undefined;

    this.ssa.update = undefined;

    if (this.ssa.ctx) {
      this.ssa.ctx = undefined;
    }

    if (this.ssa.canvas) {
      document.body.removeChild(this.ssa.canvas);
      this.ssa.canvas = undefined;
    }

    if (this.ssa.info) {
      document.body.removeChild(this.ssa.info);
      this.ssa.info = undefined;
    }
  },
};

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

      this.addWidget(
        "button",
        WIDGET_NAME_START_SHARE_SCREEN,
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
      this.addWidget(
        "button",
        WIDGET_NAME_SET_CLIP_AREA,
        "",
        function (value, widget, node) {
          runtime.startClipArea(node.id, previewWidget.videoEl);
        },
        {
          value: "",
          serialize: false,
        }
      );
      this.addWidget(
        "number",
        WIDGET_NAME_REFRESH_DURATION,
        500,
        function (value, widget, node) {},
        {
          value: 500,
          // min: 50,
          // max: 10000,
          // step: 10,
          round: 1,
          precision: 0,
          serialize: false,
        }
      );
      this.addWidget(
        "button",
        WIDGET_NAME_START_QUEUE,
        "",
        function (value, widget, node) {
          if (runtime.live > 0 && runtime.live !== node.id) return;

          if (runtime.live) {
            runtime.stopQueue().then((ok) => {
              if (ok) this.label = "Start Queue";
            });
          } else {
            runtime.startQueue(node.id, this).then((ok) => {
              if (ok) this.label = "Stop Queue";
            });
          }
        },
        {
          value: "",
          serialize: false,
        }
      );

      const previewWidget = {
        type: "DOM",
        name: WIDGET_NAME_PREVIEW,
        value: "",
        draw: function (ctx, node, widget_width, y, widget_height) {
          // const node_height = node.size[1];
          const ty = runtime.computePreviewY(node, [this.name]) + 1 * (app?.bodyTop?.scrollHeight || 0);
          const tx = 1 * (app?.bodyLeft?.scrollWidth || 0);

          const r = ctx.canvas.getBoundingClientRect();
          const transform = new DOMMatrix()
            .scaleSelf(r.width / ctx.canvas.width, r.height / ctx.canvas.height)
            .multiplySelf(ctx.getTransform())
            .translateSelf(tx + NODE_WIDGET_MARGIN, ty + 2);

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
        if (self.id === runtime.live) runtime.stopQueue();
        runtime.stopShare(self.id);

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
      previewWidget.areaEl = $el("div", {
        style: {
          position: "absolute",
          left: 0,
          top: 0,
          width: "100%",
        },
      });

      previewWidget.parentEl.appendChild(previewWidget.videoEl);
      previewWidget.parentEl.appendChild(previewWidget.areaEl);
      document.body.appendChild(previewWidget.parentEl);

      this.serialize_widgets = true;
    };
  },
});
