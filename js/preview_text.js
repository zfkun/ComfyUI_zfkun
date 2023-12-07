import { app } from "/scripts/app.js";
import { ComfyWidgets } from "/scripts/widgets.js";

app.registerExtension({
  name: "Comfy.Zfkun.PreviewText",
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeData.name !== "ZFPreviewText") return;

    const resize = function () {
      // auto resize
      const sz = this.computeSize();
      if (this.size[0] < sz[0]) this.size[0] = sz[0];
      if (this.size[1] < sz[1]) this.size[1] = sz[1];

      requestAnimationFrame(() => {
        this.onResize?.(this.size);
        app.graph.setDirtyCanvas(true, false);
      });
    };

    const refresh = function (values) {
      // console.info("node refresh: ", this.type, this.id, values);

      if (values) {
        const w = this?.widgets?.find(
          (v) => v.type === "customtext" && v.name === "__preview"
        );
        if (w) {
          let text = "";

          if (typeof values === "string") text = values;
          else if (Array.isArray(values)) text = values[0];

          w.value = text;
          app.graph.setDirtyCanvas(true, false);
        }
      }

      // auto resize
      resize.call(this);
    };

    const onNodeCreated = nodeType.prototype.onNodeCreated;
    nodeType.prototype.onNodeCreated = function () {
      // add preview widget
      const previewer = ComfyWidgets.STRING(
        this,
        "__preview",
        [
          "STRING",
          {
            default: "",
            placeholder: "Preview text...",
            multiline: true,
          },
        ],
        app
      );
      previewer.widget.inputEl.readOnly = true;
      app.graph.setDirtyCanvas(true, false);
      resize.call(this);

      onNodeCreated?.apply(this, arguments);
    };

    const onConfigure = nodeType.prototype.onConfigure;
    nodeType.prototype.onConfigure = function (w) {
      onConfigure?.apply(this, arguments);
      if (w?.widgets_values?.length > 0) refresh.call(this, w.widgets_values);
    };

    const onExecuted = nodeType.prototype.onExecuted;
    nodeType.prototype.onExecuted = function (output) {
      onExecuted?.apply(this, arguments);
      refresh.call(this, output?.string);
    };
  },
});
