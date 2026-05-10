import networkx as nx

def build_attack_graph(mapped_logs):
    G = nx.DiGraph()

    for i in range(len(mapped_logs)-1):
        src = mapped_logs[i]["technique_id"]
        dst = mapped_logs[i+1]["technique_id"]
        G.add_edge(src, dst)

    return G