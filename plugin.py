import gradio as gr
from shared.utils.plugins import WAN2GPPlugin

class CharacterLockPlugin(WAN2GPPlugin):
    def __init__(self):
        super().__init__()
        self.name = "Character Lock Prompt"
        self.version = "1.2.0"
        self.description = "Prevents character switching with dynamic prompts & strong-lock for Continue/LastVideo."

        # --- RUNTIME SETTINGS (hot reload without restart) ---
        self.enabled = True
        self.neg_enabled = True
        self.auto_strong = True  # auto strong mode for continue video

        # Normal lock
        self.lock_prompt = (
            "Keep the character consistent. Do not change identity, body type or gender."
        )

        # Normal negative lock
        self.neg_lock_prompt = (
            "style switching, anime to realistic, realistic to anime, character replacement, new person appearing, random face change, identity drift, uncontrolled morphing, background jump"
        )

        # Strong mode (automatically applied for continue modes)
        self.strong_lock = (
            "ABSOLUTELY lock character AND visual STYLE across all frames."
            "This is a CONTINUATION of the same scene."
            "The final transformed appearance MUST remain identical."
            "No new character, no face replacement, no style change."
            "If anime style is used, stay anime. If realistic, stay realistic."
            "Background, lighting and proportions must remain consistent. "
        )

        self.strong_neg = (
            "style change, anime to photorealistic, photorealistic to anime,"
            "character swap, face replacement,identity drift after transformation, unwanted reversion, flicker, distortion, background inconsistency, model drift"
        )

    # ------------------------------------------------------------------
    # request main components + hook events
    # ------------------------------------------------------------------
    def setup_ui(self):
        self.request_component("prompt")
        self.request_component("negative_prompt")

        # Hot reload → no config file needed
        self.register_data_hook("before_task_enqueue", self.apply_locks)

    # ------------------------------------------------------------------
    # UI Panel (directly under the prompt box)
    # ------------------------------------------------------------------
    def post_ui_setup(self, components):

        def build_ui():
            with gr.Accordion("Character Lock Prompt (Plugin)", open=False):

                # --- Main Lock ---
                enable_box = gr.Checkbox(
                    label="Enable Character Lock",
                    value=self.enabled
                )

                prompt_box = gr.Textbox(
                    label="Lock Prompt (before main prompt)",
                    value=self.lock_prompt,
                    lines=3
                )

                # --- Negative Lock ---
                neg_enable_box = gr.Checkbox(
                    label="Enable Negative Lock",
                    value=self.neg_enabled
                )

                neg_prompt_box = gr.Textbox(
                    label="Negative Lock Prompt (before negative prompt)",
                    value=self.neg_lock_prompt,
                    lines=3
                )

                # --- Strong Auto Mode ---
                auto_strong_box = gr.Checkbox(
                    label="Auto Strong-Lock for 'Continue Video' / 'Last Video'",
                    value=self.auto_strong
                )

                strong_prompt_box = gr.Textbox(
                    label="Strong Lock (MAIN Prompt for continue modes)",
                    value=self.strong_lock,
                    lines=3
                )

                strong_neg_box = gr.Textbox(
                    label="Strong Negative Lock (NEG prompt for continue modes)",
                    value=self.strong_neg,
                    lines=3
                )

                save_btn = gr.Button("Apply (hot reload)")

                def save_settings(en, lp, en_n, lp_n, st, slp, sln):
                    self.enabled = en
                    self.lock_prompt = lp
                    self.neg_enabled = en_n
                    self.neg_lock_prompt = lp_n
                    self.auto_strong = st
                    self.strong_lock = slp
                    self.strong_neg = sln
                    return gr.Info("Settings applied. No restart required.")

                save_btn.click(
                    fn=save_settings,
                    inputs=[
                        enable_box,
                        prompt_box,
                        neg_enable_box,
                        neg_prompt_box,
                        auto_strong_box,
                        strong_prompt_box,
                        strong_neg_box
                    ],
                    outputs=[]
                )

        self.insert_after("prompt", build_ui)

    # ------------------------------------------------------------------
    # MAIN HOOK: applied before Task is added to the queue
    # ------------------------------------------------------------------
    def apply_locks(self, data: dict):

        mode = str(data.get("mode", "")).lower()
        is_continue = (
            "continue" in mode
            or data.get("last_video", False)
            or data.get("task_type") == "video_continue"
        )

        # ------------------------------------------------------------------
        # STRONG MODE (auto-detected)
        # ------------------------------------------------------------------
        if self.auto_strong and is_continue:
            if self.enabled:
                data["prompt"] = (
                    self.strong_lock.strip() + "\n" + data.get("prompt", "")
                )

            if self.neg_enabled:
                data["negative_prompt"] = (
                    self.strong_neg.strip() + "\n" + data.get("negative_prompt", "")
                )

            return data

        # ------------------------------------------------------------------
        # NORMAL MODE
        # ------------------------------------------------------------------
        if self.enabled:
            prompt = data.get("prompt", "")
            data["prompt"] = self.lock_prompt.strip() + "\n" + prompt

        if self.neg_enabled:
            neg = data.get("negative_prompt", "")
            data["negative_prompt"] = self.neg_lock_prompt.strip() + "\n" + neg

        return data
