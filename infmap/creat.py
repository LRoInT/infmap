import numpy as np
def noise(shape,high,low): #噪声函数
    return np.random.uniform(low,high,shape)
