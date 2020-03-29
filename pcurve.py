import sklearn
import numpy as np
from sklearn.decomposition import PCA
from scipy.interpolate import UnivariateSpline

class PrincipalCurve:
    def __init__(self, k = 3):
        self.k = k
        self.p = None
        self.s = None
        
    def project(self, X, p, s):
        '''
        Get interpolating s values for projection of X onto the curve defined by (p, s)
        @param X: data
        @param p: curve points
        @param s: curve parameterisation
        @returns: interpolating parameter values
        '''
        s_interp = np.zeros(X.shape[0])
        
        for i in range(0, X.shape[0]):
            z = X[i, :]
            seg_proj = (((p[1:] - p[0:-1]).T)*np.einsum('ij,ij->i', z - p[0:-1], p[1:] - p[0:-1])/np.power(np.linalg.norm(p[1:] - p[0:-1], axis = 1), 2)).T
            proj_dist = (z - p[0:-1]) - seg_proj
            dist_endpts = np.minimum(np.linalg.norm(z - p[0:-1], axis = 1), np.linalg.norm(z - p[1:], axis = 1))
            dist_seg = np.maximum(np.linalg.norm(proj_dist, axis = 1), dist_endpts)

            idx_min = np.argmin(dist_seg)
            q = seg_proj[idx_min] 
            s_interp[i] = (np.linalg.norm(q)/np.linalg.norm(p[idx_min + 1, :] - p[idx_min, :]))*(s[idx_min+1]-s[idx_min]) + s[idx_min]
            
        return s_interp
     
    def renorm_parameterisation(self, p):
        '''
        Renormalise curve to unit speed 
        @param p: curve points
        @returns: new parameterisation
        '''
        seg_lens = np.linalg.norm(p[1:] - p[0:-1], axis = 1)
        s = np.zeros(p.shape[0])
        s[1:] = np.cumsum(seg_lens)
        s = s/sum(seg_lens)
        return s
        
    def fit(self, X, w = None, max_iter = 10):
        '''
        Fit principal curve to data
        @param X: data
        @param w: data weights (optional)
        @param max_iter: maximum number of iterations 
        @returns: None
        '''
        pca = sklearn.decomposition.PCA(n_components = X.shape[1])
        pca.fit(X)
        pc1 = pca.components_[:, 0]
        
        p = np.kron(np.dot(X, pc1)/np.dot(pc1, pc1), pc1).reshape(X.shape) # starting point for iteration
        order = np.argsort([np.linalg.norm(p[0, :] - p[i, :]) for i in range(0, p.shape[0])])
        p = p[order]
        s = self.renorm_parameterisation(p)
        
        for i in range(0, max_iter):
            s_interp = self.project(X, p, s)
            order = np.argsort(s_interp)
            s_interp = s_interp[order]
            X = X[order, :]

            spline = [UnivariateSpline(s_interp, X[:, j], k = 3) for j in range(0, X.shape[1])]

            p = np.zeros((len(s_interp), X.shape[1]))
            for j in range(0, X.shape[1]):
                p[:, j] = spline[j](s_interp)

            idx = [i for i in range(0, p.shape[0]-1) if (p[i] != p[i+1]).any()]
            p = p[idx, :]
            s = self.renorm_parameterisation(p)
            
        self.s = s
        self.p = p
        return
    
    