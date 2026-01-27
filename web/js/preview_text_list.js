import { app } from "../../scripts/app.js";
import { ComfyWidgets } from "../../scripts/widgets.js";

app.registerExtension({
  name: "Comfy.Zfkun.PreviewTextList",
  aboutPageBadges: [
    {
      label: "ComfyUI zfkun",
      url: "https://github.com/zfkun/ComfyUI_zfkun",
      icon: "pi p-github"
    }
  ],
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    if (nodeType.comfyClass !== "ZFPreviewTextList") return;

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
      if (values) {
        let texts = [];

        if (typeof values === "string") texts = [values];
        else if (Array.isArray(values)) {
          if (typeof values[0] === "string") texts = [values[0]];
          else if (Array.isArray(values)) texts = values[0];
        }

        this?.widgets?.forEach((v) => v.onRemove());
        this.widgets = [];

        texts.forEach(text => {
           const previewer = ComfyWidgets.STRING(
            this,
            "preview",
            [
              "STRING",
              {
                default: text,
                placeholder: "Preview text...",
                multiline: true,
              },
            ],
            app
          );
          previewer.widget.inputEl.readOnly = true;
        }, this);

        app.graph.setDirtyCanvas(true, false);
      }

      // auto resize
      resize.call(this);
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
