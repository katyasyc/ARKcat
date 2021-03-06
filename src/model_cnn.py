import numpy as np
import cnn_train
import cnn_eval
from cnn_methods import *
import scipy
#debug
import tensorflow as tf

# converts list of ints into list of one_hot vectors (np arrays)
#for purposes of calculating cross_entropy loss
def one_hot(train_Y, CLASSES):
    one_hot = []
    for i in range(len(train_Y)):
       one_hot.append([0] * CLASSES)
       one_hot[i][train_Y[i]] = 1
       one_hot[i] = np.asarray(one_hot[i])
    return one_hot

#returns nonzero entries in input_X as np array
def to_dense(input_X, test_key = None):
    max_length = 0
    dense = []
    for example in input_X:
        example_transform = example[0].nonzero()[1]
        example_transform = example_transform.tolist()
        for i in range(len(example_transform)):
            if test_key is not None:
                example_transform[i] = test_key[example_transform[i]]
            example_transform[i] += 1
        max_length = max(max_length, len(example_transform))
        dense.append(np.asarray(example_transform))
    return dense, max_length

#gets word vecs from word2vec_filename. those not found will be initialized later
def init_word_vecs(word2vec_filename, key_array, vocab, params):
    with open(word2vec_filename, 'r') as word2vec:
        word2vec.readline()
        for i in range(3000000):   #number of words in word2vec
            line = tokenize(word2vec.readline().strip())
            #check to see if it contains nonAscii (which would break the if statement)
            try:
                line[0].decode('ascii')
            except UnicodeDecodeError:
                pass
            #turns word vectors into floats and appends to key array
            else:
                if line[0] in vocab:
                    vector = []
                    for word in line[1:]:
                        vector.append(float(word))
                    if len(vector) != params['WORD_VECTOR_LENGTH']:
                        raise ValueError
                    key_array[vocab.index(line[0])] = vector
    return key_array

#returns an array of new word vectors for that vocab,
#and dict to link indices in test_X with indices in key_array
def process_test_vocab(word2vec_filename, vocab, new_vocab_key, params):
    add_vocab_list = []
    for word in new_vocab_key.itervalues():
        if word not in vocab:
            add_vocab_list.append(word)
    new_key_array = dict_to_array(word2vec_filename, add_vocab_list, params, train=False)
    all_vocab = vocab + add_vocab_list
    for key in new_vocab_key.iterkeys():
        new_vocab_key[key] = all_vocab.index(new_vocab_key[key])
    return new_key_array, new_vocab_key

#loads word vectors
def dict_to_array(word2vec_filename, vocab, params, train=True):
    key_array = [[] for item in range(len(vocab))]
    random.seed(None)
    if params['USE_WORD2VEC']:
        key_array = init_word_vecs(word2vec_filename, key_array, vocab, params)
    for i in range(len(key_array)):
        if key_array[i] == []:
            key_array[i] = np.random.uniform(-0.25,0.25,params['WORD_VECTOR_LENGTH'])
    if train:
        key_array.insert(0, [0] * params['WORD_VECTOR_LENGTH'])
    return np.asarray(key_array)

#saves vocab from TfidfVectorizer in list. indices in self.vocab will match those in key_array
def get_vocab(indices_to_words):
    vocab = [None] * len(indices_to_words)
    for key in indices_to_words:
        vocab[key] = indices_to_words[key]
    return vocab

#transforms indices_to_words to needed form
def fix_indices(indices_to_words):
    for key in indices_to_words:
        key += 1
    #dummy key so that len() matches
    indices_to_words[0] = None
    return indices_to_words

class Model_CNN:
    def __init__(self, params, n_labels, indices_to_words, model_dir, word2vec_filename):
        self.train_counter = 0
        self.hp = params
        self.num_labels = n_labels
        self.indices_to_words = fix_indices(indices_to_words)
        # self.indices_to_words = indices_to_words
        self.model_dir = model_dir
        self.word2vec_filename = word2vec_filename
        self.set_params()

    #grayed out options force model to stay away from expensive options, speeding DEBUGGING
    #you can also reduce the number of epochs
    def set_params(self):
        self.params = {
                'FILTERS' : self.hp['filters'],
                'ACTIVATION_FN' : self.hp['activation_fn'],
                'REGULARIZER' : self.hp['regularizer'],
                'REG_STRENGTH' : self.hp['reg_strength'],
                'TRAIN_DROPOUT' : self.hp['dropout'],
                'BATCH_SIZE' : self.hp['batch_size'],
                'LEARNING_RATE' : self.hp['learning_rate'],
                'KERNEL_SIZES' : [],
                'USE_WORD2VEC' : self.hp['word_vector_init'],
                'UPDATE_WORD_VECS' : self.hp['word_vector_update'],
                'USE_DELTA' : self.hp['delta'],

                'WORD_VECTOR_LENGTH' : 300,
                'CLASSES' : self.num_labels,
                'EPOCHS' : 15
                # debug regularization:
                # 'REGULARIZER' : 'l2',
                # 'REG_STRENGTH' : -8.0,
                # 'REGULARIZER': 'l2_clip',
                # 'REG_STRENGTH': 2.0,
                # smaller: for general debugging:
                # 'FILTERS' : 2,
                # 'KERNEL_SIZES' : [3],
                # 'USE_WORD2VEC' : False,
                # 'UPDATE_WORD_VECS' : False,
                # 'USE_DELTA' : False,
                # 'EPOCHS' : 2
        }
        if self.params['REGULARIZER'] == 'l2':
            self.params['REG_STRENGTH'] = 10 ** self.params['REG_STRENGTH']
        for i in range(self.hp['kernel_num']):
            self.params['KERNEL_SIZES'].append(self.hp['kernel_size'] + i * self.hp['kernel_increment'])

    def train(self, train_X, train_Y):
        self.vocab = get_vocab(self.indices_to_words)
        self.key_array = dict_to_array(self.word2vec_filename, self.vocab, self.params)
        train_X, self.params['MAX_LENGTH'] = to_dense(train_X)
        train_Y = one_hot(train_Y, self.params['CLASSES'])
        # train_X = collapse_vectors(train_X, params['WORD_VECTOR_LENGTH'])
        if self.hp['flex']:
            self.params['FLEX'] = int(self.hp['flex_amt'] * self.params['MAX_LENGTH'])
        else:
            self.params['FLEX'] = 0
        self.best_epoch_path, self.key_array = cnn_train.train(self.params,
                                train_X, train_Y, self.key_array, self.model_dir)

    def predict(self, test_X, indices_to_words=None, measure='predict'):
        if 'numpy' not in str(type(test_X)):
            #if called on dev or test
            if indices_to_words is not None:
                test_key_array, test_vocab_key = process_test_vocab(self.word2vec_filename, self.vocab, indices_to_words, self.params)
                test_X, self.params['MAX_LENGTH'] = to_dense(test_X, test_key=test_vocab_key)
                return cnn_eval.dev_or_test_acc(self.best_epoch_path, self.params, test_X,
                                     self.key_array, measure, test_key_array)
            #called on train
            else:
                test_X, self.params['MAX_LENGTH'] = to_dense(test_X)

        return cnn_eval.dev_or_test_acc(self.best_epoch_path, self.params, test_X, self.key_array,
                                 measure, np.zeros([0, self.key_array.shape[1]]))

    #softmax array
    def predict_prob(self, test_X, indices_to_words=None):
        return self.predict(test_X, indices_to_words=indices_to_words, measure='scores')
