def on_building_ui(self):
    # 使用翻译函数替换硬编码的英文文本
    with gr.Row():
        with gr.Column(scale=3):
            self.chatbot = gr.Chatbot(
                show_label=False,
                height=700,
                avatar_images=(None, self._app_icon),
                render_markdown=True,
                elem_id="chatbot",
                show_copy_button=True,
                likeable=True,
                bubble_full_width=False,
            )
            with gr.Row():
                self.msg = gr.Textbox(
                    show_label=False,
                    placeholder=self._app.t("ask_something"),  # "Ask something..."
                    container=False,
                    scale=12,
                )
                self.btn_submit = gr.Button(
                    self._app.t("send"),  # "Send"
                    scale=1,
                    variant="primary",
                    min_width=100,
                )