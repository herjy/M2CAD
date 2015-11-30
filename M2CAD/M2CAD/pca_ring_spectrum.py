import numpy as np
import mk_pca as mk
#import k_means as km
import matplotlib.pyplot as plt
import scipy.signal as scp
import sklearn.cluster as skc
import matplotlib.cm as cm
import pyfits as pf
import MCA

def pca_ring_spectrum(images, std = [0,0]):
    #Goals:
    #Performs PCA ont the spectrum of each pixel in a cube of a n1xn2 image taken
    #in Ns wavelength and identifies clusters of PCA coefficients in
    #a given dimensional space.
    #
    #Inputs:
    #   images: cube of images in different wavelength of size n1xn2xNs
    #
    #   ndim: number of dimensions to be considered for clustering
    #
    #   nclus: expected number of clusters (it is advised to set an overestimated
    #          value
    #
    #Outputs:
    #   alpha: PCA coefficients of the decomposition
    #
    #   base: PCA basis of the decomposition
    #
    #   clus: number of the cluster to which each set of coefficients belongs to
    #
    #   avg: centroids of the clusters
    #
    #   final_clus: number of clusters identified

    pad = 0
    images = images.T
    n1,n2,s = np.shape(images)
    res0 = images +0
    res = res0+0
    res1 = res+0.
    sigmamr = np.zeros(s)
    tr = res+0 #For thresholded images
    support = np.zeros((n1,n2))
    for j in np.linspace(0,s-1,s):
        sigmamr[j] = MCA.MAD(res0[:,:,j])
        res[:,:,j] = res1[:,:,j]
        x,y = np.where(res[:,:,j]==0)
        tr[x,y,j] = 0
        tr[:,:,-1] = 1


    support = np.prod(tr,2)

    support[np.where(support==0.0)] = 0
    support[np.where(support!=0.0)] = 1
    x00,y00 = np.where(support == 0)
    res[x00,y00,:] = 0
    
    x,y = np.where(support == 1)

    support1d = np.reshape(support,(n1*n2))
    x1d = np.where(support1d==1)

    spectrums = np.reshape(res[x,y,:],(np.size(x1d),s))


    

    alphas = np.zeros((np.size(x),n1*n2))
    alpha,base = mk.mk_pca(spectrums.T)

##Noise propagation in PCA space

    noise = np.multiply(np.random.randn(100,s),std.T)
    alphanoise = np.dot(base.T,noise.T)
    sig = np.zeros(2)
    sig[0] = np.std(alphanoise[0,:])
    sig[1] = np.std(alphanoise[1,:])


    count = 0
    for ind in np.reshape(x1d,np.size(x1d)):
        alphas[:,ind] = alpha[:,count]
        count = count+1


    return alphas, base, sig

def actg(X,Y):
        
        if X >0 and Y>=0:
            angle = np.arctan(Y/X)
        if X >0 and Y<0:
            angle = np.arctan(Y/X)+2*np.pi
        if X<0:
            angle = np.arctan(Y/X)+np.pi
        if X ==0 and Y>0:
            angle = np.pi/2
        if X ==0 and Y<=0:
            angle = 3*np.pi/2
        return angle
    

def pca_lines(alphas, sig, dt, ns):
    #
    #Identifies alignements of coefficients
    #INPUTS:
    #   alphas: PCA coefficients
    #   coeffs: coefficients thought to be proportional
    #
    #OUTPUTS:
    #   Images: image containing locations identified as belonging to a band with a given value
    #
    dt = dt*np.pi/180
    n1,n2 = np.shape(alphas)

    #coefficients dans le bruit
    noisy = np.zeros(n2)
    noisy[np.where(np.abs(alphas[0,:])<5*sig[0])] = 1
    noisy[np.where(np.abs(alphas[1,:])<5*sig[1])] = noisy[np.where(np.abs(alphas[1,:])<5*sig[1])] +1
    alphas[:,np.where(noisy==2)] = 0.

    #norm
    norm = (alphas[0,:]**2 + alphas[1,:]**2)
    

    
    alphas[:,np.where(norm == 0)] = 0
    #Rescaling des angles
    alphas[0,:] = np.sign(alphas[0,:])*np.abs(alphas[0,:]/np.max(np.abs(alphas[0,:])))
    alphas[1,:] = np.sign(alphas[1,:])*np.abs(alphas[1,:]/np.max(np.abs(alphas[1,:])))

    X = alphas[0,:]
    Y = alphas[1,:]
    angle = np.zeros(np.size(X))
    for i in range(np.size(angle)):
        angle[i] = actg(X[i],Y[i])

                           
    angle[np.where( norm==0)] = 0
    angle


    #Angles a zero non pris en compte
    loc = np.where(angle!=0)
    theta = angle[loc]
    
    normtrunc = norm[loc]
    theta = theta
    cluster = np.zeros(np.size(theta))*2
    attractors = np.zeros(ns)
    attractors[0] = np.random.rand(1)*np.pi*2
    for h in np.linspace(1,ns-1,ns-2):
        attractors[h] = attractors[h-1]+2*dt+np.random.rand(ns)*dt/10
    find = 0
    last = 0

    beta = np.zeros(2*np.pi/dt)
    count = 0
    maxi = np.zeros(ns)
    loctheta = np.zeros(2*np.pi/dt)
    k = 0
        
    while 1:
        isdone = 0
        count = 0
        #On parcours les angles pour leur attribuer chacun un attracteur
        for T in theta:
            #Distance angle attracteur
            dist = np.abs(T-attractors)

            #Correction du passage 2pi-0
            bigloc =np.where(dist>=np.pi) 
            if np.size(bigloc)>0:
                dist[bigloc] = 2*np.pi-dist[bigloc]
            find = np.where(dist == np.min(dist))[0]
            #Attribution de l'attracteur
            cluster[count]=find

           
            count = count+1
 
        if last ==1:
            break
        #Recomputing attractors by averaging over the detected angles
        oldattractors = attractors+0.
        for j in np.linspace(0,ns-1,ns):
            sample = theta[np.where(cluster == j)]
            if np.size(sample) ==0:
                attractors[j] = np.random.rand(1)*np.pi*2
            else:
                if np.max(sample)-np.min(sample) >= np.pi:
                    sample[np.where(sample<np.pi)] = sample[np.where(sample<np.pi)] + 2*np.pi
   
                if np.mean(sample) >2*np.pi:
                    attractors[j] = np.median(sample)-2*np.pi
                else:
                    attractors[j] = np.median(sample)
                if attractors[j] == oldattractors[j]:
                    isdone = isdone+1
        if isdone == ns:
            last = 1

    #Select only the coefficients in an given angular proximity
    locky = np.zeros(np.size(theta))-1.
    for i in np.linspace(0,ns-1,ns):
        distance = np.abs(theta-attractors[i])

        bigloc = np.where(distance >= np.pi)
        if np.size(bigloc) >0:
            distance[bigloc] = 2*np.pi-distance[bigloc]

        
        distance[np.where(theta == 0)] = 0
        locky[np.where(distance<dt/2)]=i
##############
    ##Second correction of attractors
    for j in np.linspace(0,ns-1,ns):
        attractors[j] = np.median(theta[np.where(locky == j)])
    locky = np.zeros(np.size(theta))-1.
    for i in np.linspace(0,ns-1,ns):
        distance = np.abs(theta-attractors[i])

        bigloc = np.where(distance >= np.pi)
        if np.size(bigloc) >0:
            distance[bigloc] = 2*np.pi-distance[bigloc]

        
        distance[np.where(theta == 0)] = 0
        locky[np.where(distance<dt/2)]=i
    ###############
    
    theta[np.where(locky ==-1)]=0

    locator = np.zeros(np.size(angle))-1.
    locator[loc] = locky

# plt.plot(alphas[0,:],alphas[1,:],'x')
#   plt.plot([0,np.cos(attractors[0])],[0,np.sin(attractors[0])])
#   plt.plot([0,np.cos(attractors[1])],[0,np.sin(attractors[1])])
#   plt.show()
    
    images = np.zeros([n2**0.5,n2**0.5])
    images[:,:]=-1
    x,y = np.where(np.zeros((n2**0.5,n2**0.5))==0)


    clus = angle +0.
    for j in np.linspace(0,np.size(angle)-1, np.size(angle)):

 #       clus[j] = np.where(mini==j)#np.where(np.abs(axis-angle[j]) == np.min(np.abs(axis-angle[j])))[0]+1
 #       if norm0[j] == 0: 
 #               clus[j] =-2
        images[x[j], y[j]] = locator[j]
            
    n_clus = ns+1

    colors = [[0.6,0,0],np.array([135, 233, 144])/255.,[0,0,0]]#plt.cm.Spectral(np.linspace(0, 1, n_clus))

    for k, col in zip(set(locator), colors):
        if k == -1:
            # Black used for noise.
            col = [0,0,0.7]
    
## #       class_member_mask = (clus== k)
        xy = alphas[0:2,np.where(locator == k)[0]]
        
        plt.figure(1)
        plt.plot(xy[0,:], xy[1,:], 'o', markerfacecolor=col, markeredgecolor='k', markersize=14)
        plt.xlabel('PCA 1')
        plt.ylabel('PCA 2')
        

##   #     xk.XKCDify(ax, expand_axes=True)
 #   plt.axis('equ)      
    plt.figure(20)
    plt.imshow(np.flipud(images), interpolation ='nearest')#; plt.colorbar()
    plt.axis('off')
    plt.show()

    return images









