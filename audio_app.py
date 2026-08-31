"""SONIC FORGE — a local Stable Audio 3 Gradio studio."""

from __future__ import annotations

from typing import Any

import gradio as gr
from gradio_client import Client

from settings_manager import clear_local_setup, load_settings, load_token, save_settings, save_token

SPACE_ID = "stabilityai/stable-audio-3"
MODELS = ["medium", "small-music", "small-sfx"]
SAMPLERS = ["pingpong", "euler", "rk4", "dpmpp"]


def token_is_valid(token: str) -> bool:
    """Check that the token can authenticate with the target Hugging Face Space."""
    if not token or not token.strip():
        return False
    try:
        Client(SPACE_ID, hf_token=token.strip()).view_api(return_format="dict")
        return True
    except Exception:
        return False


def _audio_path(result: Any) -> str:
    """Extract a filepath from common gradio-client return shapes."""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        for key in ("path", "name", "url"):
            if result.get(key):
                return str(result[key])
    if isinstance(result, (tuple, list)):
        for value in result:
            try:
                return _audio_path(value)
            except ValueError:
                continue
    raise ValueError("The Space did not return an audio file.")


def generate_audio(model: str, prompt: str, duration: float, steps: int, cfg_scale: float, sampler: str, seed: float):
    """Call Stable Audio 3's /infer API and return an audio file for Gradio."""
    token = load_token()
    if not token:
        raise gr.Error("Your Hugging Face token is missing. Open Settings to add one.")
    if not prompt or not prompt.strip():
        raise gr.Error("Describe the audio you want to generate.")
    try:
        client = Client(SPACE_ID, hf_token=token)
        result = client.predict(
            # The public Space labels this control "Model", but exposes it in
            # its API as `variant_key`; likewise its sampler is `sampler_type`.
            variant_key=model,
            prompt=prompt.strip(),
            duration=float(duration),
            steps=int(steps),
            cfg_scale=float(cfg_scale),
            sampler_type=sampler,
            seed=int(seed or 0),
            api_name="/infer",
        )
        path = _audio_path(result)
        return path, gr.update(value=path, visible=True), "Generation complete. Your audio is ready."
    except gr.Error:
        raise
    except Exception as exc:
        raise gr.Error(f"Generation failed: {exc}") from exc


def save_first_time_setup(token: str, model: str, duration: float):
    if not token_is_valid(token):
        return gr.update(value="We couldn't verify that token. Check it and try again.", visible=True), gr.update(), gr.update()
    save_token(token)
    save_settings(model, duration)
    return (
        gr.update(value="", visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
    )


def save_preferences(model: str, duration: float):
    save_settings(model, duration)
    return "Defaults saved locally.", gr.update(value=model), gr.update(value=duration)


def replace_token(token: str):
    if not token.strip():
        return "Enter a token to replace the current one."
    if not token_is_valid(token):
        return "We couldn't verify that token. Nothing was changed."
    save_token(token)
    return "Token updated securely on this computer."


def clear_setup(confirmed: bool):
    if not confirmed:
        return "Check the confirmation box before clearing local setup.", gr.update(), gr.update(), gr.update()
    clear_local_setup()
    return (
        "Local setup cleared.",
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
    )


CSS = """
footer {display: none !important;}
.gradio-container {background: #f7f7f4 !important; font-family: Inter, ui-sans-serif, system-ui, sans-serif !important; color: #17171b;}
.page-shell {max-width: 1040px; margin: 0 auto; padding: 34px 18px 60px;}
.card {background: #fff; border: 1px solid #dfdfe3; border-radius: 18px; padding: 24px; box-shadow: 0 8px 24px rgba(28, 28, 35, .035);}
.setup-card {max-width: 620px; margin: 7vh auto;}
.eyebrow {color: #315cf5; font-size: .78rem; font-weight: 750; letter-spacing: .12em; text-transform: uppercase; margin-bottom: 8px;}
.brand-title {font-size: clamp(2rem, 5vw, 3.4rem); font-weight: 800; letter-spacing: -.055em; margin: 0;}
.tagline {color: #686873; margin: 8px 0 0; font-size: 1.05rem;}
.primary-btn {background: #315cf5 !important; color: white !important; border: 0 !important; border-radius: 11px !important; font-weight: 700 !important;}
.settings-btn {border-radius: 10px !important;}
.status {min-height: 1.4em; color: #555560; margin-top: 7px;}
"""


def build_app() -> gr.Blocks:
    preferences = load_settings()
    # Validate a saved credential at startup so stale credentials return the user
    # to setup instead of failing later in the studio.
    is_configured = token_is_valid(load_token())

    with gr.Blocks(title="SONIC FORGE", css=CSS, theme=gr.themes.Base()) as demo:
        with gr.Column(elem_classes=["page-shell"]):
            with gr.Column(visible=not is_configured, elem_classes=["card", "setup-card"]) as setup_view:
                gr.HTML("<div class='eyebrow'>First-time setup</div><h1 class='brand-title'>SONIC FORGE</h1><p class='tagline'>Connect your Hugging Face account to start sculpting sound.</p>")
                setup_token = gr.Textbox(label="Hugging Face access token", type="password", placeholder="hf_…")
                with gr.Row():
                    setup_model = gr.Dropdown(MODELS, value=preferences["default_model"], label="Default model")
                    setup_duration = gr.Slider(5, 120, value=preferences["default_duration"], step=1, label="Default duration (seconds)")
                setup_submit = gr.Button("Verify & enter studio", variant="primary", elem_classes=["primary-btn"])
                setup_status = gr.Markdown(visible=False)

            with gr.Column(visible=is_configured) as studio_view:
                with gr.Row():
                    gr.HTML("<div><div class='eyebrow'>Text-to-audio studio</div><h1 class='brand-title'>SONIC FORGE</h1><p class='tagline'>Shape a scene, set the signal, and render it into sound.</p></div>")
                    settings_open = gr.Button("Settings", elem_classes=["settings-btn"])
                with gr.Column(elem_classes=["card"]):
                    prompt = gr.Textbox(label="What do you want to hear?", placeholder="Warm modular synth pulses over rain on a city window, slow and cinematic…", lines=5)
                    with gr.Row():
                        model = gr.Dropdown(MODELS, value=preferences["default_model"], label="Model")
                        duration = gr.Slider(5, 120, value=preferences["default_duration"], step=1, label="Length (seconds)")
                    with gr.Row():
                        steps = gr.Slider(4, 16, value=8, step=1, label="Steps")
                        cfg_scale = gr.Slider(0.5, 3.0, value=1.0, step=0.1, label="CFG scale")
                        sampler = gr.Dropdown(SAMPLERS, value="pingpong", label="Sampler")
                        seed = gr.Number(value=0, precision=0, label="Seed (0 = random)")
                    generate = gr.Button("Generate audio", variant="primary", elem_classes=["primary-btn"])
                with gr.Column(elem_classes=["card"]):
                    gr.Markdown("### Your render")
                    audio = gr.Audio(label="Generated audio", type="filepath", interactive=False)
                    download = gr.DownloadButton("Download audio", visible=False)
                    generation_status = gr.Markdown(elem_classes=["status"])

            with gr.Column(visible=False, elem_classes=["card"]) as settings_view:
                gr.Markdown("## Settings")
                with gr.Row():
                    settings_model = gr.Dropdown(MODELS, value=preferences["default_model"], label="Default model")
                    settings_duration = gr.Slider(5, 120, value=preferences["default_duration"], step=1, label="Default duration")
                save_defaults = gr.Button("Save defaults", variant="primary", elem_classes=["primary-btn"])
                new_token = gr.Textbox(label="Replace Hugging Face token", type="password", placeholder="Leave empty to keep your current token")
                update_token = gr.Button("Update token")
                gr.Markdown("---\n### Reset this device")
                confirm_clear = gr.Checkbox(label="I understand this removes the saved token and preferences from this device.")
                clear_button = gr.Button("Clear local setup", variant="stop")
                settings_status = gr.Markdown(elem_classes=["status"])
                close_settings = gr.Button("Back to studio")

        setup_submit.click(save_first_time_setup, [setup_token, setup_model, setup_duration], [setup_status, setup_view, studio_view])
        generate.click(generate_audio, [model, prompt, duration, steps, cfg_scale, sampler, seed], [audio, download, generation_status])
        settings_open.click(lambda: gr.update(visible=True), None, settings_view)
        close_settings.click(lambda: gr.update(visible=False), None, settings_view)
        save_defaults.click(save_preferences, [settings_model, settings_duration], [settings_status, model, duration])
        update_token.click(replace_token, new_token, settings_status)
        clear_button.click(clear_setup, confirm_clear, [settings_status, setup_view, studio_view, settings_view])
    return demo


if __name__ == "__main__":
    build_app().launch()
