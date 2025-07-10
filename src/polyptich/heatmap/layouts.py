class Layout():
    def __init__(self, padding = 0.05, size = None, resolution = None):
        
        self.padding = padding
        self._size = size
        self.resolution = resolution

    def iter(self, data):
        raise NotImplementedError

    def size(self, data):
        if self._size is None:
            if self.resolution is None:
                size = 5
            else:
                size = self.resolution * data.shape[0]
        else:
            size = self._size
        return size

class Simple(Layout):
    def __init__(self, padding = 0.05, size = None, resolution = None):
        super().__init__(padding = padding, size = size, resolution = resolution)

    def iter(self, data):
        yield 0, None, data, self.size(data)

import pandas as pd
class Broken(Layout):
    def __init__(self, split:pd.Series, padding = 0.05, size = None, resolution = None):
        super().__init__(padding = padding, size = size, resolution = resolution)
        # make sure is categorical
        if not pd.api.types.is_categorical_dtype(split):
            raise ValueError("split must be categorical")
        self.split = split

    def iter(self, data):
        assert len(data) == len(self.split), f"{len(data)} != {len(self.split)}"
        assert data.index.equals(self.split.index), f"{data.index} != {self.split.index}"
        for i, (name, df) in enumerate(data.groupby(self.split, observed = True)):
            ratio = df.shape[0]/data.shape[0]
            size = self.size(df) * ratio
            yield i, name, df, size

class Clustered(Layout):
    def __init__(self, padding = 0.05, size = None, resolution = None):
        super().__init__(padding = padding, size = size, resolution = resolution)
        pass

class BrokenClustered(Layout):
    def __init__(self, padding = 0.05):
        super().__init__(padding = padding)