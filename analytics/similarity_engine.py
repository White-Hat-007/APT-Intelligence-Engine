from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def compute_similarity(fp1, fp2):
    v1 = np.array(fp1["vector"]).reshape(1, -1)
    v2 = np.array(fp2["vector"]).reshape(1, -1)

    score = cosine_similarity(v1, v2)[0][0]
    return score