import numpy as np
import tensorflow as tf
from cnn_methods import *
from cnn_class import CNN
import cnn_eval
import time, resource
import inspect_checkpoint

def main(params, train_X, train_Y, key_array, model_dir):
    val_X, val_Y, train_X, train_Y = separate_train_and_val(train_X, train_Y)
    cnn_dir = model_dir
    with tf.Graph().as_default():
        with open(cnn_dir + 'train_log', 'a') as timelog:
        #with open('train_log', 'a') as timelog:
            timelog.write('\n\n\nNew Model:')

        # with tf.Graph().as_default():
            cnn = CNN(params, key_array)
            loss = cnn.cross_entropy
            loss += tf.mul(tf.constant(params['REG_STRENGTH']), cnn.reg_loss)
            train_step = cnn.optimizer.minimize(loss)
            sess = tf.Session(config=tf.ConfigProto(inter_op_parallelism_threads=1,
                                  intra_op_parallelism_threads=1, use_per_session_threads=True))
            sess.run(tf.initialize_all_variables())
        # with sess.as_default():
            # saver = tf.train.Saver(var_list =
            #                       {'word_embeddings': word_embeddings,
            #                       'W_delta': W_delta,
            #                       'W_1': W_1, 'W_2': W_2, 'W_3': W_3,
            #                       'b_1': b_1, 'b_2': b_2, 'b_3': b_3,
            #                       'W_fc': W_fc,
            #                       'b_fc': b_fc})
            saver = tf.train.Saver(tf.all_variables())
            file_path = cnn_dir + 'cnn_eval_%s_epoch%i' %(params['model_num'], 0)
            checkpoint = saver.save(sess, cnn_dir + 'cnn_eval_%s_epoch%i' %(params['model_num'], 0))
            reader = tf.train.NewCheckpointReader(cnn_dir + 'cnn_eval_%s_epoch%i' %(params['model_num'], 0))
            print(reader.debug_string().decode("utf-8"))
            best_dev_accuracy = cnn_eval.float_entropy(file_path, saver, val_X, val_Y, key_array, params)
            timelog.write( '\ndebug acc %g' %best_dev_accuracy)
            timelog.write('\n%g'%time.clock())

            for i in range(params['EPOCHS']):
                print 'debug%i' %params['epoch']
                params['epoch'] = i + 1
                batches_x, batches_y = scramble_batches(params, train_X, train_Y)
                for j in range(len(batches_x)):
                    feed_dict = {cnn.input_x: batches_x[j], cnn.input_y: batches_y[j],
                                 cnn.dropout: params['TRAIN_DROPOUT']}
                    train_step.run(feed_dict=feed_dict, session = sess)
                    #apply l2 clipping to weights and biases
                    if params['REGULARIZER'] == 'l2_clip':
                        cnn.clip_vars(params)
                timelog.write('\n\nepoch %i initial time %g' %(params['epoch'], time.clock()))
                timelog.write('\nCPU usage: %g'
                            %(resource.getrusage(resource.RUSAGE_SELF).ru_utime +
                            resource.getrusage(resource.RUSAGE_SELF).ru_stime))
                timelog.write('\nmemory usage: %g' %(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))
                checkpoint = saver.save(sess, cnn_dir + 'cnn_eval_%s_epoch%i' %(params['model_num'], params['epoch']))
                dev_accuracy = cnn_eval.float_entropy(checkpoint, val_X, val_Y, key_array, params)
                timelog.write('\ndev accuracy: %g'%dev_accuracy)
                if dev_accuracy > best_dev_accuracy:
                    checkpoint = saver.save(sess, 'temp/cnn_' + params['model_num'], global_step = params['epoch'])
                    best_dev_accuracy = dev_accuracy
                    if dev_accuracy < best_dev_accuracy - .02:
                        #early stop if accuracy drops significantly
                        return checkpoint
            return checkpoint

if __name__ == "__main__":
    main()