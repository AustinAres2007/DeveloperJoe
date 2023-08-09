from TTS.api import TTS

COQUI_TTS_MODELS = [
    "tts_models/en/ljspeech/tacotron2-DDC"
]

if __name__ == "__main__":
    for model in COQUI_TTS_MODELS:
        TTS(model).download_model_by_name(model)
    print(f"Got models at: {TTS.get_models_file_path()}")