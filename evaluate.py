import sys
import os

import pickle

from SMRL.logger import Logger as Log
## YS
Log.VERBOSE = True
# Log.VERBOSE = False

import SMRL.evaluation as evaluation
from SMRL.plotting import *

def sort_by_config(results, configs, key):
    temp = np.array([stt[key] for stt in configs])
    I_vals = np.argsort(temp)

    for k in results['train'].keys():
        results['train'][k] = results['train'][k][I_vals,]
        results['valid'][k] = results['valid'][k][I_vals,]

        if k in results['test']:
            results['test'][k] = results['test'][k][I_vals,]

    configs_sorted = []
    for i in I_vals:
        configs_sorted.append(configs[i])

    return results, configs_sorted

def load_config(config_file):
    with open(config_file, 'r') as f:
        cfg = [l.split('=') for l in f.read().split('\n') if '=' in l]
        cfg = dict([(kv[0], eval(kv[1])) for kv in cfg])

    # # YS
    # print('load fun 2 !!' * 5)
    # import pdb; pdb.set_trace()

    return cfg

def evaluate(config_file, overwrite=False, filters=None):

    if not os.path.isfile(config_file):
        raise Exception('Could not find config file at path: %s' % config_file)

    cfg = load_config(config_file)

    ### YS change output_dir here

    output_dir = cfg['outdir']
    # output_dir_results_summary = cfg['outdir']

    if not os.path.isdir(output_dir):
        raise Exception('Could not find output at path: %s' % output_dir)

    data_train = cfg['datadir']+'/'+cfg['dataform']
    data_test = cfg['datadir']+'/'+cfg['data_test']
    binary = False
    if cfg['loss'] == 'log':
        binary = True

    eval_path = '%s/evaluation.npz' % output_dir
    if overwrite or (not os.path.isfile(eval_path)):
        eval_results, configs, exp_dirs_result_summary = evaluation.evaluate(output_dir,
                                data_path_train=data_train,
                                data_path_test=data_test,
                                binary=binary)

        ## YS save into sub-folder
        # eval_path = '%s/evaluation.npz' % exp_dirs_result_summary

        # Save evaluation
        pickle.dump((eval_results, configs), open(eval_path, "wb"))
    else:
        if Log.VERBOSE:
            print('Loading evaluation results from %s...' % eval_path)
        # Load evaluation
        eval_results, configs = pickle.load(open(eval_path, "rb"))
    data_train_find = load_data(data_train)

    ## YS
    # import pdb; pdb.set_trace()



    if binary:
        if data_train_find['HAVE_TRUTH']:
            plot_evaluation_cont(eval_results, configs, output_dir, data_train, data_test, exp_dirs_result_summary, filters)
        else:

            plot_evaluation_bin(eval_results, configs, output_dir, data_train, data_test, filters)
    else:
        plot_evaluation_cont(eval_results, configs, output_dir, data_train, data_test, exp_dirs_result_summary, filters)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python evaluate.py <config_file> <overwrite (default 0)> <filters (optional)>')
    else:
        config_file = sys.argv[1]

        overwrite = False
        if len(sys.argv)>2 and sys.argv[2] == '1':
            overwrite = True

        filters = None
        if len(sys.argv)>3:
            filters = eval(sys.argv[3])

        # evaluate(config_file, overwrite, filters=filters)

        ## YS
        import time
        import datetime
        time_tol = time.time()

        evaluate(config_file, overwrite, filters=filters)

        import pytz
        time_now = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%m-%d %H:%M:%S")
        print('Time Now: %s' % time_now)
        print('Total Time used: ' + str(datetime.timedelta(seconds=time.time() - time_tol)))

