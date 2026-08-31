# SONIC FORGE

A minimalist local text-to-audio studio powered by the Hugging Face Space
[`stabilityai/stable-audio-3`](https://huggingface.co/spaces/stabilityai/stable-audio-3).

## Run it

Install [uv](https://docs.astral.sh/uv/) if needed, then run:

```bash
cd /Users/vipulmahesh/Desktop/sonic-forge
uv run python audio_app.py
```

On first launch, paste a Hugging Face access token with access to the Space. The
token is kept locally in `.env`; your non-sensitive defaults are stored in
`settings.json`. Neither file is tracked by Git or displayed back in the UI.

## Project files

- `audio_app.py` — Gradio interface and Stable Audio inference call.
- `settings_manager.py` — secure local token and preference persistence.
- `pyproject.toml` — uv/Python dependency configuration.
