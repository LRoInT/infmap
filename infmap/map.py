from block import *


class InfMap:
    def __init__(self, height=10, width=10):
        # 四个象限
        self.map = np.zeros((height, width, 4))


class LinkedMapNode:  # 链式地图节点
    def __init__(self, *size):
        self.map = [[MapBlock() for _ in range(size[1])]
                    for _ in range(size[0])]

    def __getitem__(self, index):
        get=self.map.copy()
        for i in index:
            get=get[i]
        return get
