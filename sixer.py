import numpy as np

f = open('three.txt', 'r')
words = f.read().split('\n')

def sixer():
    one = np.random.randint(len(words))
    two = np.random.randint(len(words))
    return (words[one] + words[two]).upper()


if __name__ == '__main__':
    print(sixer())
