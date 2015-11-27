import os
import codecs
import datetime
import cPickle as pickle
from optparse import OptionParser

from hyperopt import fmin, tpe, hp, Trials, space_eval

import classify_test


data_filename = None
label_filename = None
feature_dir = None
output_dir = None
log_filename = None

space = {
    'model': hp.choice('model', [
        {
            'model': 'SVM',
            'regularizer_svm': 'l2',
            'C_svm': hp.loguniform('C_svm', -1.15, 9.2)
        },
        {
            'model': 'LR',
            'regularizer_lr': hp.choice('regularizer_lr', ['l1', 'l2']),
            'alpha_lr': hp.loguniform('alpha_lr', -1.15, 9.2)
        }
    ]),
    'features': {
        'unigrams':
            {
                'transform': hp.choice('u_transform', ['None', 'binarize', 'tfidf']),
                'min_doc_threshold': hp.choice('u_min_doc_threshold', [1,2,3,4,5])
            },
        'bigrams':
            hp.choice('bigrams', [
                {
                    'use': False
                },
                {
                    'use': True,
                    'transform': hp.choice('b_transform', ['None', 'binarize', 'tfidf']),
                    'min_doc_threshold': hp.choice('b_min_doc_threshold', [1,2,3,4,5])
                }
            ]),
    }
}

def call_experiment(args):
    model = args['model']['model']
    feature_list, description, kwargs = wrangle_params(args)
    result = classify_test.classify(train_data_filename, train_label_filename, dev_data_filename, 
                                    dev_label_filename, train_feature_dir, dev_feature_dir, 
                                    feature_list, **kwargs)
    with codecs.open(log_filename, 'a') as output_file:
        output_file.write(str(datetime.datetime.now()) + '\t' + ' '.join(feature_list) + '\t' + ' '.join(description) +
                          '\t' + str(-result['loss']) + '\n')
    save_model(model, feature_list, kwargs)

    return result

def wrangle_params(args):
    kwargs = {}

    # WARNING THIS IS A HACK! Should pass this is as a param
    kwargs['folds'] = 0

    print('')
    print('the args:')
    print(args)
    model = args['model']['model']
    kwargs['model_type'] = model
    if model == 'SVM':
        kwargs['regularizer'] = args['model']['regularizer_svm']
        kwargs['alpha'] = args['model']['C_svm']
    elif model == 'LR':
        kwargs['regularizer'] = args['model']['regularizer_lr']
        kwargs['alpha'] = args['model']['alpha_lr']

    feature_list = []
    unigrams = 'ngrams,n=1' + \
               ',transform=' + args['features']['unigrams']['transform'] + \
               ',min_doc_threshold=' + str(args['features']['unigrams']['min_doc_threshold'])
    feature_list.append(unigrams)
    if args['features']['bigrams']['use']:
        bigrams = 'ngrams,n=2' + \
                  ',transform=' + args['features']['bigrams']['transform'] + \
                  ',min_doc_threshold=' + str(args['features']['bigrams']['min_doc_threshold'])
        feature_list.append(bigrams)

    print feature_list
    description = [str(k) + '=' + str(v) for (k, v) in kwargs.items()]
    return feature_list, description, kwargs
    

def save_model(model, feature_list, model_hyperparams):
    #printing for debugging

    print('\n\n')
    print(feature_list)
    print(model_hyperparams)
    print('\n\n')

    # to save the model after each iteration
    feature_string = ''
    for i in range(0,len(feature_list)):
        feature_string = feature_string + feature_list[i] + ';'
    for hparam in model_hyperparams:
        feature_string = feature_string + hparam + '=' + str(model_hyperparams[hparam]) + ';'
    feature_string = feature_string[:-1]
    pickle.dump(model, open(output_dir + '/' + feature_string + '.model', 'wb'))
    


def main():
    usage = "%prog train_text.json train_labels.csv dev_text.json dev_labels.csv train_feature_dir dev_feature_dir output_dir"
    parser = OptionParser(usage=usage)
    parser.add_option('-m', dest='max_iter', default=4,
                      help='Maximum iterations of Bayesian optimization; default=%default')

    (options, args) = parser.parse_args()
    max_iter = int(options.max_iter)

    global train_data_filename, train_label_filename, dev_data_filename, dev_label_filename, train_feature_dir, dev_feature_dir, output_dir, log_filename

    train_data_filename = args[0]
    train_label_filename = args[1]
    dev_data_filename = args[2]
    dev_label_filename = args[3]
    train_feature_dir = args[4]
    dev_feature_dir = args[5]
    output_dir = args[6]
    

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    log_filename = os.path.join(output_dir, 'log.txt')

    with open(log_filename, 'w') as logfile:
        logfile.write(','.join([train_data_filename, train_label_filename, dev_data_filename, dev_label_filename, train_feature_dir, dev_feature_dir, output_dir]) + '\n')

    trials = Trials()
    best = fmin(call_experiment,
                space=space,
                algo=tpe.suggest,
                max_evals=max_iter,
                trials=trials)

    print space_eval(space, best)
    print "losses:", [-l for l in trials.losses()]



if __name__ == '__main__':
    main()
