class TTSException(Exception):
    pass


class InvalidAudioException(TTSException):
    pass


class SynthesisException(TTSException):
    pass


class ModelBusyException(RuntimeError):
    pass
