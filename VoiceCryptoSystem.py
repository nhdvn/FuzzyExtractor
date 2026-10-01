
import json
import hashlib
import math
import multiprocessing
import os
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


class VoiceCryptoSystem:

    def __init__(self, dataset: dict):
        
        self.id_pos = dataset['id_pos']
        self.n_size = dataset['n_size']
        self.r_size = dataset['r_size']
        self.extractor = SampleLock(3, 0.2, self.r_size)


    def enroll_user(self, user: int, data: numpy.ndarray):

        index = self.select_reliable_index(data)
        input = self.extract_reliable_bits(data, index)
        self.save_index(list(index))
        return self.extractor.key_generate(user, input)


    def verify_user(self, user: int, data: numpy.ndarray):

        index = self.load_index(user)
        if not index: return None
        input = self.extract_reliable_bits(data, index)
        return self.extractor.key_reproduce(user, input)


    def save_index(self, user: int, index: list):

        with open(f'./public/{user}', 'w') as output:
            output.write(str(index))

    
    def load_index(self, user: int):
        
        try:
            with open(f'./public/{user}', 'r') as input:
                return json.loads(input.read())
        except:
            print(f'User {user} Not Exists')


    def select_reliable_index(self, data: numpy.ndarray):

        result = []

        for i in range(self.n_size):
            mean = data[:, i].mean()
            dist = data[:, i] - mean
            vari = (dist ** 2).sum()
            result.append(vari)

        return numpy.argsort(result)[:self.r_size]


    def extract_reliable_bits(self, data: numpy.ndarray, index: list):

        res = ''
        mean = numpy.mean(data, axis = 0)

        for val in mean[index]:
            res += '0' if val <= 0 else '1'

        return res



class DigitalLocker:

    def __init__(self, _N, _K, _R):
        
        self.N = _N # 28 bytes - 224 bits hash
        self.K = _K # 16 bytes - 128 bits secret
        self.R = _R # 18 bytes - 144 bits nonce
        self.P = bytes(self.N - self.K)


    def xor(self, b1: bytes, b2: bytes) -> bytes:

        val = int.from_bytes(b1, "big") ^ int.from_bytes(b2, "big")

        return val.to_bytes(self.N, "big")


    def lock(self, key: bytes, value: bytes) -> bytes:

        nonce = os.urandom(self.R)

        vhash = hashlib.sha224(nonce + key).digest()

        return nonce + self.xor(vhash, value + self.P)


    def unlock(self, key: bytes, data: bytes) -> bytes:

        nonce, vlock = data[:self.R], data[self.R:]

        vhash = hashlib.sha224(nonce + key).digest()

        vlock = self.xor(vhash, vlock)

        if vlock[self.K:] == self.P: return vlock[:self.K]




class SampleLock:

    def __init__(self, div: int, rate: float, size: int):

        self.locker = DigitalLocker(28, 16, 18)
        self.div_size = div
        self.key_size = 16
        self.sub_size = 80
        self.pub_size = 126 # = 80 + 46
        
        self.bound = math.floor(math.exp(rate * self.sub_size)) // div
        self.range = range(size)


    def bits_to_bytes(self, bio: str, idx: list):

        subset = "".join([bio[i] for i in idx])

        return int(subset, 2).to_bytes(10, "big")


    def array_to_bytes(self, idx: list, bio: str):

        return bytes(idx), self.bits_to_bytes(bio, idx)


    def public_to_bytes(self, arr: bytes, bio: str):

        return self.bits_to_bytes(bio, [i for i in arr])


    def key_generate(self, user: int, bio: str):

        secret = os.urandom(self.key_size)
        handler = multiprocessing.Pool(self.div_size)
        
        for i in range(self.div_size):
            params = (user, bio, i, secret)
            handler.apply_async(self.worker_gen, params)

        handler.close()
        handler.join()
        return secret

    
    def key_reproduce(self, user: int, bio: str):

        manager = multiprocessing.Manager()
        handler = multiprocessing.Pool(self.div_size)
        result = manager.dict()
        
        def terminate(result):
            if result: handler.terminate()

        for i in range(self.div_size):
            params = (user, bio, i, result)
            handler.apply_async(self.worker_rep, args = params, callback = terminate)

        handler.close()
        handler.join()
        
        for secret in result.values():
            if secret != None: return secret
        return None


    def worker_gen(self, user: int, input: str, nth: int, secret: bytes):

        helper = open(f"./public/{user}_{nth}", "wb")

        for _ in range(self.bound):

            index = random.sample(self.range, self.sub_size)
            index, subset = self.array_to_bytes(index, input)
            vlock = self.locker.lock(subset, secret)
            helper.write(index + vlock)

        helper.close()


    def worker_rep(self, user: int, input: str, nth: int, result: dict):

        helper = open(f"./public/{user}_{nth}", "rb")

        for _ in range(self.bound):

            block = helper.read(self.pub_size)
            index = block[:self.sub_size]
            vlock = block[self.sub_size:]
            
            subset = self.public_to_bytes(index, input)
            secret = self.locker.unlock(subset, vlock)
            if secret: break

        helper.close()
        result[nth] = secret
        return secret




def read_numpy_data(source: str):
    
    try:
        return numpy.genfromtxt(source, delimiter = ',')
    except:
        print('Error Reading Template')


def enroll(argv: list):

    if len(argv) != 4:
        return print('Error Arguments')

    userid = argv[2]
    source = argv[3]

    name = source[:source.find('_')]
    name = name.strip('.\\')
    system = VoiceCryptoSystem(dataset[name])

    enroll_data = read_numpy_data(source)
    enroll_key = system.enroll_user(int(userid), enroll_data)

    return print(f'User {userid} Secret Key: {enroll_key}')


def verify(argv: list):

    if len(argv) != 4:
        return print('Error Arguments')

    userid = argv[2]
    source = argv[3]

    name = source[:source.find('_')]
    name = name.strip('.\\')
    system = VoiceCryptoSystem(dataset[name])

    verify_data = read_numpy_data(source)
    verify_key = system.verify_user(int(userid), verify_data)

    return print(f'User {userid} Secret Key: {verify_key}')



def main():

    if len(sys.argv) < 2:
        return print('Not Enough Arguments')

    action = sys.argv[1]

    if action == 'enroll':
        return enroll(sys.argv)

    if action == 'verify':
        return verify(sys.argv)

    print('Unknown Action')


if __name__ == '__main__':
    main()
