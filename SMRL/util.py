import tensorflow as tf
import numpy as np

SQRT_CONST = 1e-10

FLAGS = tf.app.flags.FLAGS

def tf_cov(x,y):
    mean_x = tf.reduce_mean(x, axis=0, keep_dims=True)
    mean_y = tf.reduce_mean(y, axis=0, keep_dims=True)
    mxy = tf.matmul(tf.transpose(mean_x), mean_y)
    vx = tf.matmul(tf.transpose(x), y) / tf.cast(tf.shape(x)[0], tf.float32)
    cov_xx = vx - mxy
    return cov_xx

def structure_keeper(x, y, k_top_cca=2):

    # x= np.random.normal(size=(4, 3))
    # y= np.random.normal(size=(4, 6))
    # import pdb; pdb.set_trace()

    # matx = tf.constant(x, dtype=tf.float32)
    # maty = tf.constant(y, dtype=tf.float32)

    matx = x
    maty = y

    sxx = tf_cov(matx, matx)
    syy = tf_cov(maty, maty)
    sxy = tf_cov(matx, maty)
    # syx = tf_cov(maty, matx)

    sa, ua, va = tf.svd(sxx)
    sb, ub, vb = tf.svd(syy)

    sxx_half =  tf.matmul(tf.matmul(ua, tf.diag(sa ** (-0.5))), tf.transpose(va))
    syy_half =  tf.matmul(tf.matmul(ub, tf.diag(sb ** (-0.5))), tf.transpose(vb))

    M = tf.matmul(tf.matmul(sxx_half, sxy), syy_half)

    sm, um, vm = tf.svd(M)

    idx = tf.nn.top_k(sm, k_top_cca)[1]

    u = tf.gather(um, indices=idx, axis=1)
    v = tf.gather(vm, indices=idx, axis=1)

    a = tf.matmul(sxx_half, u)
    b = tf.matmul(syy_half, v)

    cor = tf.matmul(tf.matmul(tf.transpose(a), sxy), b)
    cor_sum = tf.reduce_sum(tf.diag_part(cor))

    # return cor_sum
    return cor




def validation_split(D_exp, val_fraction):
    """ Construct a train/validation split """
    n = D_exp['x'].shape[0]

    if val_fraction > 0:
        n_valid = int(val_fraction*n)
        n_train = n-n_valid
        I = np.random.permutation(range(0,n))
        I_train = I[:n_train]
        I_valid = I[n_train:]
    else:
        I_train = range(n)
        I_valid = []

    return I_train, I_valid

def log(logfile,str):
    """ Log a string in a file """
    with open(logfile,'a') as f:
        f.write(str+'\n')
    # import pdb; pdb.set_trace()
    print(str)

def save_config(fname):
    """ Save configuration """
    flagdict =  FLAGS.__dict__['__flags']
    s = '\n'.join(['%s: %s' % (k,str(flagdict[k])) for k in sorted(flagdict.keys())])
    f = open(fname,'w')
    f.write(s)
    f.close()

def load_data(fname):
    """ Load data set """
    if fname[-3:] == 'npz':
        data_in = np.load(fname)
        data = {'x': data_in['x'], 't': data_in['t'], 'yf': data_in['yf']}
        try:
            data['ycf'] = data_in['ycf']
        except:
            data['ycf'] = None
    else:
        if FLAGS.sparse>0:
            data_in = np.loadtxt(open(fname+'.y',"rb"),delimiter=",")
            x = load_sparse(fname+'.x')
        else:
            data_in = np.loadtxt(open(fname,"rb"),delimiter=",")
            x = data_in[:,5:]

        data['x'] = x
        data['t'] = data_in[:,0:1]
        data['yf'] = data_in[:,1:2]
        data['ycf'] = data_in[:,2:3]

    data['HAVE_TRUTH'] = not data['ycf'] is None

    data['dim'] = data['x'].shape[1]
    data['n'] = data['x'].shape[0]

    return data

def load_sparse(fname):
    """ Load sparse data set """
    E = np.loadtxt(open(fname,"rb"),delimiter=",")
    H = E[0,:]
    n = int(H[0])
    d = int(H[1])
    E = E[1:,:]
    S = sparse.coo_matrix((E[:,2],(E[:,0]-1,E[:,1]-1)),shape=(n,d))
    S = S.todense()

    return S

def safe_sqrt(x, lbound=SQRT_CONST):
    ''' Numerically safe version of TensorFlow sqrt '''
    return tf.sqrt(tf.clip_by_value(x, lbound, np.inf))

def lindisc(X,p,t):
    ''' Linear MMD '''

    it = tf.where(t>0)[:,0]
    ic = tf.where(t<1)[:,0]

    Xc = tf.gather(X,ic)
    Xt = tf.gather(X,it)

    mean_control = tf.reduce_mean(Xc,reduction_indices=0)
    mean_treated = tf.reduce_mean(Xt,reduction_indices=0)

    c = tf.square(2*p-1)*0.25
    f = tf.sign(p-0.5)

    mmd = tf.reduce_sum(tf.square(p*mean_treated - (1-p)*mean_control))
    mmd = f*(p-0.5) + safe_sqrt(c + mmd)

    return mmd

def pdist2sq(X,Y):
    """ Computes the squared Euclidean distance between all pairs x in X, y in Y """
    C = -2*tf.matmul(X,tf.transpose(Y))
    nx = tf.reduce_sum(tf.square(X),1,keep_dims=True)
    ny = tf.reduce_sum(tf.square(Y),1,keep_dims=True)
    D = (C + tf.transpose(ny)) + nx
    return D

def pdist2(X,Y):
    """ Returns the tensorflow pairwise distance matrix """
    return safe_sqrt(pdist2sq(X,Y))

def pop_dist(X,t):
    it = tf.where(t>0)[:,0]
    ic = tf.where(t<1)[:,0]
    Xc = tf.gather(X,ic)
    Xt = tf.gather(X,it)
    nc = tf.to_float(tf.shape(Xc)[0])
    nt = tf.to_float(tf.shape(Xt)[0])

    ''' Compute distance matrix'''
    M = pdist2(Xt,Xc)
    return M

def simplex_project(x,k):
    """ Projects a vector x onto the k-simplex """
    d = x.shape[0]
    mu = np.sort(x,axis=0)[::-1]
    nu = (np.cumsum(mu)-k)/range(1,d+1)
    I = [i for i in range(0,d) if mu[i]>nu[i]]
    theta = nu[I[-1]]
    w = np.maximum(x-theta,0)
    return w
