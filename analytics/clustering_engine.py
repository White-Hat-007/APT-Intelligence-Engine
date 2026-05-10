from sklearn.cluster import KMeans
import numpy as np

def cluster_campaigns(fingerprints, n_clusters=2):
    if len(fingerprints) < n_clusters:
        n_clusters = len(fingerprints)

    vectors = np.array([fp["vector"] for fp in fingerprints])

    if len(set(map(tuple, vectors))) < n_clusters:
        n_clusters = len(set(map(tuple, vectors)))

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(vectors)

    return labels