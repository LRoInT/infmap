import numpy as np


class ListAxis(list):  # 基于列表的轴类
    def __init__(self, size: int, origin: int = 0, default=0, scal=lambda x: x):
        super().__init__([default for _ in range(size)])  # 初始化轴
        self.origin = origin  # 原点索引
        self.scal = scal  # 自动扩容函数
        self.default = default  # 默认值

    def __getitem__(self, index):
        if isinstance(index, tuple):
            get = None
            for i in index:
                get = get[i]
            return get
        return super().__getitem__(self._get_index(index))

    def __setitem__(self, index, value):
        return super().__setitem__(self._get_index(index), value)

    def __delitem__(self, index):
        return super().__delitem__(self._get_index(index))

    def get_origin(self):
        if isinstance(self[0], ListAxis):  # 当轴也为 轴 时
            return self[0].get_origin()
        return self[0]

    def _get_index(self, index):  # 转换索引
        if isinstance(index, int):
            index += self.origin
            return index
        elif isinstance(index, slice):
            start = None if index.start is None else self._get_index(
                index.start)
            stop = None if index.stop is None else self._get_index(index.stop)
            return slice(start, stop, index.step)

    def get_origin_index(self):  # 返回轴列表
        return self.origin

    def get_size(self):  # 返回轴长度
        size = 0
        for i in self:
            if "__len__" in dir(i):
                size += len(i)
            else:
                size += 1

    def extend_capacity(self, index):  # 扩容
        if self._get_index(index) >= 0 and self._get_index(index) < self.__len__():  # 判断是否需要扩容
            return
        index = self._get_index(index)
        if index > self.__len__():
            self.extend([self.default for _ in range(index-self.__len__())])
        if index < 0:
            more = 0-index
            self.insert(0, [self.default for _ in range(0-index)])
            self.origin += more

    def datafill(self, value: list | tuple, start=None, end=None):  # 数据填充
        # 设置填充范围
        start = 0 if start is None else self._get_index(start)
        end = self.__len__() if end is None else self._get_index(end)
        if (start < 0 or start > self.__len__()) or (start > end or end > len):
            raise IndexError("Index out of range")
        if len(value) != end-start:
            raise ValueError("Value cannot be filled")
        for i in range(start, end+1):  # 输入数据
            self[i] = value[i]

    def funcfill(self, func, start=None, end=None):  # 填充函数输出
        # 设置填充范围
        start = 0 if start is None else self._get_index(start)
        end = self.__len__() if end is None else self._get_index(end)
        if (start < 0 or start > self.__len__()) or (start > end or end > len):
            raise IndexError("Index out of range")
        for i in range(start, end+1):  # 输入数据
            self[i] = func(i)


class MapBlock:  # 区块类
    def __init__(self, size=[10, 10, 2]):
        self.inside = np.zeros(size)

    def __getitem__(self, path):
        return self.inside[path]

    def __setitem__(self, path, value):
        self.inside[path] = value

    def set_block(self, path, value):
        self.__setitem__(path, value)

    def get_block(self, path):
        return self.__getitem__(path)
