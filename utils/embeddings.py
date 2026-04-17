import gensim.downloader as api

_model = None

def get_model():
    global _model

    if _model is None:
        _model = api.load("glove-wiki-gigaword-100")

    return _model