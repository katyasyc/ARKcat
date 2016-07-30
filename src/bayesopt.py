from hyperopt import fmin, tpe, hp, Trials, space_eval

#uses Bayesian optimization to choose parameters of model

def get_linear_model(model_num):
    return {
        'model_' + model_num: 'LR',
        'regularizer_lr_' + model_num: hp.choice('regularizer_lr_' + model_num,[
            ('l1', hp.loguniform('l1_strength_lr_' + model_num, -5,5)),
            ('l2', hp.loguniform('l2_strength_lr_' + model_num, -5,5))
        ]),
        'converg_tol_' + model_num: hp.loguniform('converg_tol_' + model_num, -10, -1)
    }

def get_xgboost_model(model_num):
    return {
            'model_' + model_num: 'XGBoost',
            'eta_' + model_num: hp.loguniform('eta_' + model_num,-5,0),
            'gamma_' + model_num: hp.uniform('gamma_' + model_num,0,10),
            'max_depth_' + model_num: hp.quniform('max_depth_' + model_num, 1,30,1),
            'min_child_weight_' + model_num: hp.uniform('min_child_weight_' + model_num, 0, 10),
            'max_delta_step_' + model_num: hp.uniform('max_delta_step_' + model_num, 0, 10),
            'num_round_' + model_num: hp.quniform('num_round_' + model_num, 1, 10, 1),
            'subsample_' + model_num: 1,
            'regularizer_xgb_' + model_num: hp.choice('regularizer_xgb_' + model_num,[
                ('l1', hp.loguniform('l1_strength_xgb_' + model_num, -5,5)),
                ('l2', hp.loguniform('l2_strength_xgb_' + model_num, -5,5))

            ])
        }

def get_cnn_model_big(model_num):
    hyperparams = {
            'model_' + model_num: 'CNN',
            # choose btwn rand, word2vec--implement glove
            'word_vectors_' + model_num: hp.choice('word_vectors_' + model_num,[
                ('word2vec', hp.choice('word2vec_update_' + model_num, [True, False])),
                ('rand', hp.choice('rand_update_' + model_num, [True, False]))
            ]),
            'delta_' + model_num: hp.choice('delta_' + model_num, [True, False]),
            'flex_' + model_num: hp.choice('flex_' + model_num, [
                (False, 0.0),
                (True, hp.uniform('flex_amt_' + model_num, 0, 0.3))
                ]),
            'filters_' + model_num: hp.quniform('filters_' + model_num, 10, 1000,1),
            'kernel_size_' + model_num: hp.quniform('kernel_size_' + model_num, 1, 30, 1),
            'kernel_increment_' + model_num: hp.quniform('kernel_increment_' + model_num, 0, 10, 1),
            'kernel_num_' + model_num: hp.quniform('kernel_num_' + model_num, 1, 5, 1),
            'dropout_' + model_num: hp.uniform('dropout_' + model_num, 0, 1),
            'batch_size_' + model_num: hp.quniform('batch_size_' + model_num, 10, 200, 1),
            'activation_fn_' + model_num: hp.choice('activation_fn_' + model_num,
                ['iden', 'relu', 'elu', 'tanh', 'sigmoid']),
            #none, clipped, or penalized
            'regularizer_cnn_' + model_num: hp.choice('regularizer_cnn_' + model_num, [
                (None, 0.0),
                ('l1', hp.loguniform('l1_strength_cnn_' + model_num, 0,10)),
                ('l2', hp.loguniform('l2_strength_cnn_' + model_num, 0,10)),
                ('l2_clip', hp.uniform('l2_clip_norm_' + model_num, 1,10))
            ]),
            #debug to check if this has a mean about .001
            # 'learning_rate_' + model_num: hp.lognormal('learning_rate_' + model_num, 0, 1) / 1000)
            'learning_rate_' + model_num: .00025 + (hp.lognormal('learning_rate_' + model_num, 0, 1) / 370)
            }

def get_cnn_model(model_num):
    return {'model_' + model_num: 'CNN',
            'word_vectors_' + model_num: ('word2vec', True),
            'delta_' + model_num: True,
            'flex_' + model_num: (True, .15), #hp.choice('flex_' + model_num, [
                # (False, 0.0),
                # (True, hp.uniform('flex_amt_' + model_num, 0, 0.3))]),
            'filters_' + model_num: hp.quniform('filters_' + model_num, 100, 600,1),
            'kernel_size_' + model_num: hp.quniform('kernel_size_' + model_num, 1, 15, 1),
            'kernel_increment_' + model_num: hp.quniform('kernel_increment_' + model_num, 0, 5, 1),
            # 'kernel_num_' + model_num: hp.quniform('kernel_num_' + model_num, 1, 5, 1),
            'kernel_num_' + model_num: 3,
            # 'dropout_' + model_num: hp.uniform('dropout_' + model_num, 0, 1),
            'dropout_' + model_num: .5,
            'batch_size_' + model_num: hp.quniform('batch_size_' + model_num, 10, 200, 1),
            # iden, relu, and elu
            'activation_fn_' + model_num: hp.choice('activation_fn_' + model_num, ['iden', 'relu', 'elu']),
            #clipped, or penalized
            'regularizer_cnn_' + model_num: hp.choice('regularizer_cnn_' + model_num, [
                # (None, 0.0),
                ('l2', hp.uniform('l2_strength_cnn_' + model_num, -8,-2)),
                ('l2_clip', hp.uniform('l2_clip_norm_' + model_num, 2,6))
            ]),
            # 'learning_rate_' + model_num: .00025 + (hp.lognormal('learning_rate_' + model_num, 0, 1) / 370)
            'learning_rate_' + model_num: .001
        }

def get_cnn_yk(model_num):
    return {'model_' + model_num: 'CNN',
            'word_vectors_' + model_num: ('word2vec', True),
            'delta_' + model_num: False,
            'flex_' + model_num: (True, .15),
            'filters_' + model_num: 100,
            'kernel_size_' + model_num: 3,
            'kernel_increment_' + model_num: 1,
            'kernel_num_' + model_num: 3,
            'dropout_' + model_num: hp.uniform('dropout_' + model_num, 0, 1),
            'batch_size_' + model_num: 50,
            'activation_fn_' + model_num: 'relu',
            'regularizer_cnn_' + model_num: hp.choice('regularizer_cnn_' + model_num, [
                (None, 0.0),
                ('l2', hp.uniform('l2_strength_cnn_' + model_num, -4, -1)),
                ('l2_clip', hp.uniform('l2_clip_norm_' + model_num, 1,5))
            ]),
            'learning_rate_' + model_num: .001
        }
