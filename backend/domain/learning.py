import numpy as np
from sklearn.cluster import Birch
from sklearn.preprocessing import StandardScaler

DEFAULT_THRESHOLD = .25

def matrix(rows):
    return [[r[k] for k in ('length','perforation')] for r in rows]

def model(samples, threshold):
    scale=StandardScaler().fit(matrix(samples))
    vector=scale.transform(matrix(samples))
    clusterer=Birch(threshold=threshold,n_clusters=None)
    for batch in np.array_split(vector,3): clusterer.partial_fit(batch)
    return scale,clusterer

def calculate(data):
    samples=data['samples']; target=data['target']
    threshold=float(data.get('threshold',DEFAULT_THRESHOLD))
    scale,clusterer=model(samples,threshold)
    vector=scale.transform(matrix(samples))
    groups=clusterer.predict(vector)
    query=scale.transform(matrix([target]))
    kind=clusterer.predict(query)[0]
    members=[i for i,label in enumerate(groups) if kind==label]
    if not members: raise ValueError('无相同孔形簇')
    match=min(members,key=lambda i:float(np.linalg.norm(query[0]-vector[i])))
    return {'pair':samples[match]['code'],'size':len(members),'clusters':len(set(groups)),
            'n_samples':len(samples),'threshold':threshold,
            'rule_version':data.get('rule_version')}
