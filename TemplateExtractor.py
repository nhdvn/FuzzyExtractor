
import numpy
import random
import sys

dataset = {

    "vkyc": {
        "d_path": "./data/vkyc",
        "n_size": 512,
        "r_size": 256,
        "id_pos": -1
    },

    "timit": {
        "d_path": "./data/timit",
        "n_size": 512,
        "r_size": 256,
        "id_pos": -1
    },
}


class TemplateExtractor:

    def __init__(self, dataset: dict):

        self.n_data = numpy.genfromtxt(dataset['d_path'], delimiter = ',')

        self.id_pos = dataset['id_pos']
        self.n_size = dataset['n_size']
        self.r_size = dataset['r_size']

        self.d_list = self.enumerate_data()
        self.u_list = list(self.d_list.keys())


    def list_user_id(self):

        return self.u_list

    
    def list_user_feature_vector_by_index(self):

        return self.d_list


    def enumerate_data(self) -> dict:

        res = {}

        for i, row in enumerate(self.n_data):

            u = int(row[self.id_pos]) # index of uid in the vector

            if u not in res: res[u] = []

            res[u] += [i] # store index of vector for reuse

        return res


    def load_user_data(self, uid: int, n: int) -> list:

        row = self.d_list[uid]

        if len(row) < n: return None

        return self.n_data[random.sample(row, n)]


    def binary_distance(self, x: list, y: list) -> float:

        count = 0

        for a, b in zip(x, y):
            if a != b: count += 1
        
        return count / len(x)


    def reliable_index(self, data: numpy.ndarray):

        result = []

        for i in range(self.n_size):
            mean = data[:, i].mean()
            dist = data[:, i] - mean
            vari = (dist ** 2).sum()
            result.append(vari)

        return numpy.argsort(result)[:self.r_size]


    def reliable_bits(self, data: numpy.ndarray, index: list):

        res = ''
        mean = numpy.mean(data, axis = 0)

        for val in mean[index]:
            res += '0' if val <= 0 else '1'

        return res


    def mean_distance(self, n: int, k: int):

        intra = []
        inter = []

        for ix, arr in self.d_list.items():

            size = len(arr)
            if n > size: continue

            entry = self.n_data[arr[:n]]
            index = self.reliable_index(entry)
            entry = self.reliable_bits(entry, index)

            for i in range(n, size, k):
                if i + k > size: break

                input = self.n_data[arr[i: i + k]]
                input = self.reliable_bits(input, index)
                error = self.binary_distance(input, entry)
                intra += [error]

            for iv, brr in self.d_list.items():

                size = len(brr)
                if ix == iv: continue

                for i in range(0, size, k):
                    if i + k > size: break
                    
                    input = self.n_data[brr[i: i + k]]
                    input = self.reliable_bits(input, index)
                    error = self.binary_distance(input, entry)
                    inter += [error]

        return intra, inter



def list_user(argv: list):

    if len(argv) != 3:
        return print('Error Arguments')

    if argv[2] not in ('vkyc', 'timit'):
        return print('Unknown Source')

    loader = TemplateExtractor(dataset[argv[2]])

    return print(loader.list_user_id())


def load_data(argv: list):

    if len(argv) != 5:
        return print('Error Arguments')

    if argv[2] not in ('vkyc', 'timit'):
        return print('Unknown Source')
    
    loader = TemplateExtractor(dataset[argv[2]])
    
    source = argv[2]
    userid = argv[3]
    number = argv[4]

    try:
        data = loader.load_user_data(int(userid), int(number))
    
    except:
        return print('Error UserID')


    if type(data) is numpy.ndarray:

        output = f'{source}_{userid}_{number}.txt'
        numpy.savetxt(output, data, delimiter = ',')
            
    else:
        print('Not Enough Template')



def test_data(argv: list):

    if len(argv) != 7:
        return print('Error Arguments')
    
    if argv[2] not in ('vkyc', 'timit'):
        return print('Unknown Source')
    
    loader = TemplateExtractor(dataset[argv[2]])

    try:
        usr_x = int(argv[3])
        cnt_x = int(argv[4])
        usr_y = int(argv[5])
        cnt_y = int(argv[6])
    except:
        return print('Error UserID')


    if usr_x == usr_y:
        data = loader.load_user_data(usr_x, cnt_x + cnt_y)
        data_x = data[:cnt_x]
        data_y = data[cnt_x:]
    else:
        data_x = loader.load_user_data(usr_x, cnt_x)
        data_y = loader.load_user_data(usr_y, cnt_y)


    if type(data_x) is not numpy.ndarray:
        return print(f'Not Enough Template User {usr_x}')

    if type(data_y) is not numpy.ndarray:
        return print(f'Not Enough Template User {usr_y}')


    index = loader.reliable_index(data_x)
    bit_x = loader.reliable_bits(data_x, index)
    bit_y = loader.reliable_bits(data_y, index)
    dist = loader.binary_distance(bit_x, bit_y)
    print(f'Hamming Distance Threshold: {dist}')

    with open('test.txt', 'w') as output:
        output.write(bit_x + '\n')
        output.write(bit_y + '\n')




def main():

    if len(sys.argv) < 2:
        return print('Not Enough Arguments')

    action = sys.argv[1]

    if action == 'list':
        return list_user(sys.argv)

    if action == 'load':
        return load_data(sys.argv)

    if action == 'test':
        return test_data(sys.argv)


    print('Unknown Action')



if __name__ == '__main__':
    main()