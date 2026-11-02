class Processor:
    """Every enhancement model implements this, so models can be swapped."""
    name = "base"
    is_ai = False

    def process(self, img, mode):
        raise NotImplementedError
