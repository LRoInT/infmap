import numpy


class empty_class:  # 空类,用于存放数据
    pass


"""
ListAxis类:
    基于列表的坐标轴类

在 ListAxis 类中, 使用列表作为轴, 相较于原本的列表, 其索引方式不同
size: 轴长度
data: 轴数据(当此项不为None时,size无效)
origin: 轴原点索引
default: 轴默认值
expansion: 是否自动扩容
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
        self.origin = origin  # 原点索引
        self.expansion = expansion  # 判断是否自动扩容

        if "__call__" in dir(default):
            def data(): return default()
        else:
            def data(): return default
        self.default = data  # 默认值
        super().__init__([data() for _ in range(size)])  # 初始化轴

    def _get_list_index(self, index) -> int | slice:  # 转换轴索引为列表索引
        if isinstance(index, int):
            return index+self.origin
        elif isinstance(index, slice):
            start = None if index.start is None else self._get_list_index(
                index.start)
            stop = None if index.stop is None else self._get_list_index(
                index.stop)
            return slice(start, stop, index.step)

    def _get_axis_index(self, index) -> int | slice:  # 转换列表索引为轴索引
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

    def _reindex(self, func, index, *args, **kwargs):
        index = self._get_list_index(index)
        output = func(self, index, *args, **kwargs)  # 获取输出
        return output

    def _auto_reindex(func):  # 自动将轴索引转为列表索引
        def wrapper(self, index, *args, **kwargs):
            return self._reindex(func, index,  *args, **kwargs)
        return wrapper

    @_auto_reindex
    def __getitem__(self, index):
        self.check_extend_capacity(index)
        if isinstance(index, tuple):
            get = self
            for i in index:
                get = get[i]
            return get
        return super().__getitem__(index)

    @_auto_reindex
    def __setitem__(self, index, value):
        self.check_extend_capacity(index)
        super().__setitem__(index, value)

    @_auto_reindex
    def __delitem__(self, index):
        return super().__delitem__(index)

    def copy(self):  # 复制一个内存地址不同,内容相同的轴
        n_axis = ListAxis(self.__len__(), self.origin,
                          self.default, self.expansion)
        n_axis.funcfill(self.__getitem__)  # 填充轴数据
        return n_axis

    # 以下为原列表方法
    @_auto_reindex
    def clear(self):
        default = self.default
        expansion = self.expansion
        super().clear()
        self.origin = 0
        self.default = default
        self.expansion = expansion

    def index(self, value, *args):
        val_index = super().index(value, *args)
        return self._get_axis_index(val_index)

    @_auto_reindex
    def insert(self, index, value):
        super().insert(index, value)

    @_auto_reindex
    def pop(self, index):
        super().pop(index)

    @_auto_reindex
    def remove(self, value):
        super().remove(value)

    def get_origin(self):
        if isinstance(self[0], ListAxis):  # 当 轴 内嵌轴时, 返回轴原点
            return self.__getitem__(0).get_origin()
        return self.__getitem__(0)

    def to_list(self) -> list:  # 转换为列表
        return [i for i in self]

    def get_origin_index(self):  # 返回轴原点索引
        return self.origin

    def index_range(self) -> tuple:  # 轴索引范围
        start = self._get_axis_index(0)
        end = self._get_axis_index(self.__len__())
        return start, end

    def extend_capacity(self, index):  # 扩容
        if isinstance(index, slice):
            self.extend_capacity(index.start)
            self.extend_capacity(index.stop)
            return 0
        start, end = self.index_range()
        if index > end:
            self.extend([self.default() for _ in range(index-end)])
        if index < start:
            more = 0-index
            self.insert(0, [self.default() for _ in range(abs(start-index))])
            self.origin += more

    def check_extend_capacity(self, index):  # 检查是否自动扩容
        if self.expansion:
            self.extend_capacity(index)

    def fill_radius(self, start, end) -> bool:  # 检查填充范围是否合法
        return (start < self._get_axis_index(0) or start > self._get_axis_index(self.__len__())) or (start > end or end > self._get_axis_index(self.__len__()))

    def datafill(self, value: list | tuple, start=None, end=None):  # 数据填充
        # 设置填充范围
        ser = self.index_range()  # 轴索引范围
        start = ser[0] if start is None else start
        end = start+len(value) if end is None else end
        d = 0
        for i in range(start, end+1):  # 输入数据
            self.__setitem__(i, value[d])
            d += 1

    def funcfill(self, func, start=None, end=None):  # 填充函数输出
        # 设置填充范围
        ser = self.index_range()
        start = ser[0] if start is None else start
        end = ser[1] if end is None else end
        for i in range(start, end+1):  # 输入数据
            self.__setitem__(i, func(i))


"""
Mapnd类:
    多维地图

基于多个 ListAxis 轴, 实现多维地图

shape: 地图形状(类似numpy)
origin: 地图原点索引(索引轴都将设为同个索引)或列表(列表中每个元素对应一个轴的原点索引)
default: 地图默认值

例:
1:
Mapnd(shape=(1),origin=(0),default=0)
->[0]
   0
2:
Mapnd(shape=(3,3),origin=(1,1),default=0)
->[
    -1 [0, 0, 0],
        -1  0  1
    0  [0, 0, 0],
        -1  0  1
    1  [0, 0, 0]
        -1  0  1
]
"""


class Mapnd:
    def __init__(self, shape: tuple | list = (0),  origin: tuple | list | int | None = None, default=0, expansion: bool = False):
        self.expansion = expansion
        self.default = default
        self._set_axis(shape, origin, default, expansion)

    def _set_axis(self, shape: tuple | list, origin: tuple | list | None = None, default=0, expansion: bool = False):  # 生成地图
        # 设置原点
        if origin is None:
            origin = [0 for _ in range(len(shape))]
        elif isinstance(origin, int):
            origin = [origin for _ in range(len(shape))]
        if len(origin) != len(shape):
            raise ValueError(f"The number of origins must be {len(shape)}")
        d = 0
        for i in shape[:-1][::-1]:
            d += 1
            def _laxis(): return ListAxis(
                shape[-1], origin[d], default, expansion)
            axis = ListAxis(i, origin[d], _laxis,
                            expansion)  # 将上一个轴作为当前轴的默认数据
        self.axis = axis  # 主轴(x轴)

    def __str__(self) -> str:
        return f"Mapnd:({self.axis})"

    def __repr__(self) -> str:
        return self.__str__()

    def extend_capacity(self, index):  # 扩容
        if isinstance(index, tuple):
            for i in index:
                self.axis[i].extend_capacity(i)
        else:
            self.axis.extend_capacity(index)

    def check_extend_capacity(self, index):  # 检查是否自动扩容
        if self.expansion:
            self.extend_capacity(index)

    def __getitem__(self, index):
        self.check_extend_capacity(index)
        if isinstance(index, tuple):
            get = self.axis
            for i in index:
                get = get[i]
            return get
        return self.axis[index]

    def __setitem__(self, index, value):
        self.check_extend_capacity(index)
        if isinstance(index, tuple):
            get = self.axis
            for i in index[:-1]:
                get = get[i]
            get[index[-1]] = value
        self.axis[index] = value

    def __delitem__(self, index):
        if isinstance(index, tuple):
            get = self.axis
            for i in index[:-1]:
                get = get[i]
            del get[index[-1]]
        del self.axis[index]

    def shape(self) -> tuple:  # 获取地图形状
        map_shape = []
        a = self.axis
        while isinstance(a, ListAxis):
            map_shape.append(a.__len__())
            a = a[0]
        return tuple(map_shape)

# 多层遍历
# array:遍历数组
# time:遍历次数


def walknt(array, time) -> list:
    if time == 1:
        return array
    output = []
    for i in array:
        output.extend(walknt(i, time-1))
    return output


# numpy数组转Mapnd
def nparray2mapnd(array, origin=None, default=0, expansion=False) -> Mapnd:
    pass
