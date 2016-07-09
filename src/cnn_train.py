import numpy as np
import tensorflow as tf
from cnn_methods import *
from cnn_class import CNN
import cnn_eval

#rename: cnn_obj, cnn_run, cnn_methods???
def main(params, train_X, train_Y, key_array):
    val_X, val_Y, train_X, train_Y = separate_train_and_val(train_X, train_Y)

    with tf.Graph().as_default():
        print 'debug 1'
        cnn = CNN(params, key_array)
        loss = cnn.cross_entropy
        loss += tf.mul(tf.constant(params['REG_STRENGTH']), cnn.reg_loss)
        train_step = cnn.optimizer.minimize(loss)
        saver = tf.train.Saver(tf.all_variables())
        sess = tf.Session(config=tf.ConfigProto(inter_op_parallelism_threads=1,
                          intra_op_parallelism_threads=1, use_per_session_threads=True))
        sess.run(tf.initialize_all_variables())
        with sess.as_default():
            checkpoint = saver.save(sess, 'cnn_eval')
            print 'debug 2'
            best_dev_accuracy = cnn_eval.float_entropy(checkpoint, val_X, val_Y, key_array, params)
            print 'debug acc', best_dev_accuracy
            for i in range(params['EPOCHS']):
                params['epoch'] = i + 1
                batches_x, batches_y = scramble_batches(params, train_X, train_Y)
                for j in range(len(batches_x)):
                    feed_dict = {cnn.input_x: batches_x[j], cnn.input_y: batches_y[j],
                                 cnn.dropout: params['TRAIN_DROPOUT']}
                    train_step.run(feed_dict=feed_dict, session = sess)
                    #apply l2 clipping to weights and biases
                    if params['REGULARIZER'] == 'l2_clip':
                        cnn.clip_vars(params)
                print 'debug3'
                dev_accuracy = cnn_eval.float_entropy(checkpoint, val_X, val_Y, key_array, params)
                if dev_accuracy > best_dev_accuracy:
                    checkpoint = saver.save(sess, 'cnn_' + params['model_num'], global_step = params['epoch'])
                    word_embeddings = cnn.word_embeddings.eval()
                    if params['USE_DELTA']:
                        delta = cnn.W_delta.eval()
                    else:
                        delta = None
                    best_dev_accuracy = dev_accuracy
                elif dev_accuracy < best_dev_accuracy - .02:
                    #early stop if accuracy drops significantly
                    return checkpoint, word_embeddings, delta
            return checkpoint, word_embeddings, delta

if __name__ == "__main__":
    main()
