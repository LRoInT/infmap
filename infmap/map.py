import copy


class empty_class:  # 空类,用于存放数据
    pass


"""
ListAxis类:
    基于列表的坐标轴类

在 ListAxis 类中, 使用列表作为轴, 相交于原本的列表, 其索引方式不同

例:
List:           [1, 2, 3, 4, 5]
ListIndex:       0  1  2  3  4
ListAxis:       [0 , 1, 2, 3, 4] (origin=2)
ListAxisIndex:   -2 -1  0  1  2

ListAxis._get_axis_index(index):用于将列表索引转换为轴索引 (2->0)
ListAxis._get_list_index(index):用于将轴索引转换为列表索引 (0->2)

"""


class ListAxis(list):  # 基于列表的轴类
    def __init__(self, size: int, origin: int = 0, default=0, expansion: bool = False):
        if "__call__" in dir(default):
            def data(): return default()
        else:
            def data(): return default
        super().__init__([data() for _ in range(size)])  # 初始化轴
        self.origin = origin  # 原点索引
        self.expansion = expansion  # 判断是否自动扩容
        self.default = data  # 默认值

    def __getitem__(self, index):
        self.check_extend_capacity(index)
        if isinstance(index, tuple):
            get = self
            for i in index:
                get = get[i]
            return get
        return super().__getitem__(self._get_list_index(index))

    def __setitem__(self, index, value):
        self.check_extend_capacity(index)
        super().__setitem__(self._get_list_index(index), value)

    def __delitem__(self, index):
        return super().__delitem__(self._get_list_index(index))

    def _get_list_index(self, index):  # 转换轴索引为列表索引
        if isinstance(index, int):
            return index+self.origin
        elif isinstance(index, slice):
            start = None if index.start is None else self._get_list_index(
                index.start)
            stop = None if index.stop is None else self._get_list_index(
                index.stop)
            return slice(start, stop, index.step)

    def _get_axis_index(self, index):  # 转换列表索引为轴索引
        if isinstance(index, int):
            if index > self.origin:
                return index-self.origin-1
            else:
                return index-self.origin

        elif isinstance(index, slice):
            start = None if index.start is None else self._get_axis_index(
                index.start)
            stop = None if index.stop is None else self._get_axis_index(
                index.stop)
            return slice(start, stop, index.step)

    def copy(self):  # 复制一个内存地址不同,内容相同的轴
        n_axis = ListAxis(self.__len__(), self.origin,
                          self.default, self.expansion)
        n_axis.funcfill(self.__getitem__)  # 填充轴数据
        return n_axis

    def get_origin(self):
        if isinstance(self[0], ListAxis):  # 当 轴 内嵌轴时, 返回轴原点
            return self[0].get_origin()
        return self.__getitem__(0)

    def to_list(self):  # 转换为列表
        return [i for i in self]

    def get_origin_index(self):  # 返回轴原点索引
        return self.origin

    def index_range(self):  # 轴索引范围
        start = self._get_axis_index(0)
        end = self._get_axis_index(self.__len__())
        return start, end

    def extend_capacity(self, index):  # 扩容
        # 判断是否需要扩容
        start, end = self.index_range()
        if index > end:
            self.extend([self.default() for _ in range(index-end)])
        if index < start:
            more = 0-index
            self.insert(0, [self.default() for _ in range(abs(start-index))])
            self.origin += more

    def check_extend_capacity(self, index):
        if self.expansion:
            self.extend_capacity(index)

    def fill_radius(self, start, end) -> bool:
        return (start < self._get_axis_index(0) or start > self._get_axis_index(self.__len__())) or (start > end or end > self._get_axis_index(self.__len__()))

    def datafill(self, value: list | tuple, start=None, end=None):  # 数据填充
        # 设置填充范围
        ser = self.index_range()  # 轴索引范围
        start = ser[0] if start is None else start
        end = start+len(value) if end is None else end
        d = 0
        for i in range(start, end):  # 输入数据
            self.__setitem__(i, value[d])
            d += 1

    def funcfill(self, func, start=None, end=None):  # 填充函数输出
        # 设置填充范围
        ser = self.index_range()
        start = ser[0] if start is None else start
        end = ser[1] if end is None else end
        for i in range(start, end):  # 输入数据
            self.__setitem__(i, func(i))


# 多维地图
class Mapnd:
    def __init__(self, shape: tuple, origin=0, default=0, expansion: bool = False):
        self.shape = shape
        self.expansion = expansion
        self._set_axis(shape, origin, default, expansion)

    def _set_axis(self, shape: tuple | list, origin=0, default=0, expansion: bool = False):  # 生成地图
        axis = ListAxis(shape[-1], origin, default, expansion)  # 最后一个轴
        for i in shape[:-1][::-1]:
            axis = ListAxis(i, origin, axis.copy,
                            expansion)  # 将上一个轴作为当前轴的默认数据
        self.mainaxis = axis  # 主轴(x轴)

    def __str__(self):
        return f"Mapnd:({self.mainaxis})"

    def __repr__(self):
        return self.__str__()

    def __getitem__(self, index):
        if isinstance(index, tuple):
            get = self.mainaxis
            for i in index:
                get = get[i]
            return get
        return self.mainaxis[index]

    def __setitem__(self, index, value):
        if isinstance(index, tuple):
            get = self.mainaxis
            for i in index[:-1]:
                get = get[i]
            get[index[-1]] = value
        self.mainaxis[index] = value

    def __delitem__(self, index):
        if isinstance(index, tuple):
            get = self.mainaxis
            for i in index[:-1]:
                get = get[i]
            del get[index[-1]]
        del self.mainaxis[index]
