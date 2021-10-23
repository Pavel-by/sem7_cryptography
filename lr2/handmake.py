import numpy as np

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning) 


IP = np.fromfile('tables/ip', sep=' ', dtype=np.int64) - 1
IP_1 = np.fromfile('tables/ip_1', sep=' ', dtype=np.int64) - 1
KEY_E = np.fromfile('tables/key_e', sep=' ', dtype=np.int64) - 1
KEY_CP = np.fromfile('tables/key_cp', sep=' ', dtype=np.int64) - 1
KEY_N = np.fromfile('tables/key_n', sep=' ', dtype=np.int64)
F_EP = np.fromfile('tables/f_ep', sep=' ', dtype=np.int64) - 1
F_S = np.fromfile('tables/f_s', sep=' ', dtype=np.int64).reshape([4 * 8, 16])
F_P = np.fromfile('tables/f_p', sep=' ', dtype=np.int64) - 1


def num_to_bits(_num, _padding):
    return np.fromstring(np.binary_repr(_num).zfill(_padding), dtype='S1').astype(int) 


def bits_to_symbols(_bits):
    _bits = _bits.reshape([-1])
    assert(len(_bits) % 8 == 0)
    _i = 0
    _symbols = ""
    while _i < len(_bits):
        _num = 0
        for _ind in range(8):
            _num <<= 1
            _num |= _bits[_i]
            _i += 1
        _symbols += chr(_num)
    return _symbols


def symbols_to_bits(_symbols):
    _bits = []
    for _c in _symbols:
        _code = ord(_c)
        _code_bits = []
        for i in range(8):
            _code_bits.insert(0, _code & 1)
            _code >>= 1
        _bits += _code_bits
    return np.array(_bits, dtype=np.int64)


def generate_keys(_key, _rounds):
    print("Generating keys")
    _bits = symbols_to_bits(_key).reshape([8, 7])
    _bits = np.append(_bits, np.zeros([8,1], dtype=np.int64), axis=1)
    print("Key bits\n", _bits)
    _bits = np.take(_bits.reshape([-1]), KEY_E).reshape(8, 7)
    print("Applying E\n", _bits)

    _C = _bits[:len(_bits)//2]
    _D = _bits[len(_bits)//2:]
    print("C\n", _C)
    print("D\n", _D)
    
    _keys = []
    for _round in range(_rounds):
        _C = np.roll(_C, KEY_N[_round])
        _D = np.roll(_D, KEY_N[_round])
        _round_key = np.append(_C, _D)
        _round_key = np.take(_round_key, KEY_CP)
        _keys.append(_round_key)
        print("Round key {0}\n".format(_round + 1), _round_key.reshape(8, 6))

    return _keys
    

def f(_b, _key):
    _bits = np.take(_b.reshape([-1]), F_EP)
    _key = _key.reshape([-1])
    _bits = np.logical_xor(_bits, _key) * 1
    _bits = _bits.reshape([8, 6])
    _out_bits = np.array([], dtype=np.int64)

    for _i in range(8):
        _s = F_S[_i * 4:(_i + 1) * 4]
        _row = _bits[_i][0] * 2 + _bits[_i][5]
        _column = _bits[_i][1] * 8 + _bits[_i][2] * 4 + _bits[_i][3] * 2 + _bits[_i][4]
        _out_bits = np.append(_out_bits, num_to_bits(_s[_row][_column], 4))
        
    _bits = _out_bits
    _bits = np.take(_bits, F_P)
    
    return _bits


def encode(_symbols, _key, _rounds):
    _bits = symbols_to_bits(_symbols).reshape([-1])
    assert(len(_bits) == 64)
    print("Encoding {0}".format(_symbols))
    _keys = generate_keys(_key, _rounds)
    _bits = np.take(_bits, IP)
    _A = _bits[:len(_bits)//2]
    _B = _bits[len(_bits)//2:]

    for _round in range(_rounds):
        print("Round {0}".format(_round + 1))
        _A, _B = _B, np.logical_xor(_A, f(_B, _keys[_round])) * 1
        
    _bits = np.append(_A, _B)
    _bits = np.take(_bits, IP_1)

    return bits_to_symbols(_bits)


def decode(_symbols, _key, _rounds):
    _bits = symbols_to_bits(_symbols).reshape([-1])
    assert(len(_bits) == 64)
    print("Decoding {0}".format(_symbols))
    _keys = generate_keys(_key, _rounds)
    _bits = np.take(_bits, IP)
    _A = _bits[:len(_bits)//2]
    _B = _bits[len(_bits)//2:]

    for _round in reversed(range(_rounds)):
        print("Round {0}".format(_round + 1))
        _A, _B = np.logical_xor(_B, f(_A, _keys[_round])) * 1, _A

    _bits = np.append(_A, _B)
    _bits = np.take(_bits, IP_1)

    return bits_to_symbols(_bits)

        
key = "838208d"
rounds = 2

encoded = encode("mironchi", key, rounds)
print([ord(c) for c in encoded], encoded)

print("-----------------------------------")

decoded = decode(encoded, key, rounds)
print([ord(c) for c in decoded], decoded)

