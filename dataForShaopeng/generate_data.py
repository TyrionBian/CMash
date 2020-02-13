import numpy as np
from CMash import MinHash as MH
import seaborn
import matplotlib.pyplot as plt
# Data prep

# In bash:
#mkdir dataForShaopeng
#cd dataForShaopeng/
#mkdir data
#cd data
#wget https://ucla.box.com/shared/static/c1g8xjc9glh68oje9e549fjqj0y8nc17.gz && tar -zxvf c1g8xjc9glh68oje9e549fjqj0y8nc17.gz && rm c1g8xjc9glh68oje9e549fjqj0y8nc17.gz  # grabbed this from the Metalign setup_data.sh
#ls | xargs -I{} sh -c 'readlink -f {} >> ../file_names.txt'
#cd ..
#head -n 10 file_names.txt > file_names_10.txt
#head -n 100 file_names.txt > file_names_100.txt
#head -n 1000 file_names.txt > file_names_1000.txt
#cd ../scripts/
#python MakeStreamingDNADatabase.py ../dataForShaopeng/file_names_10.txt ../dataForShaopeng/TrainingDatabase_10_k_60.h5 -n 1000 -k 60 -v
#python MakeStreamingDNADatabase.py ../dataForShaopeng/file_names_100.txt ../dataForShaopeng/TrainingDatabase_100_k_60.h5 -n 1000 -k 60 -v
#python MakeStreamingDNADatabase.py ../dataForShaopeng/file_names_1000.txt ../dataForShaopeng/TrainingDatabase_1000_k_60.h5 -n 1000 -k 60 -v


def cluster_matrix(A_eps, A_indicies, cluster_eps=.01):
    """
    This function clusters the indicies of A_eps such that for a given cluster, there is another element in that cluster
    with similarity (based on A_eps) >= cluster_eps for another element in that same cluster. For two elements of
    distinct clusters, their similarity (based on A_eps) < cluster_eps.
    :param A_eps: The jaccard or jaccard_count matrix containing the similarities
    :param A_indicies: The basis of the matrix A_eps (in terms of all the CEs)
    :param cluster_eps: The similarity threshold to cluster on
    :return: (a list of sets of indicies defining the clusters, LCAs of the clusters)
    """
    #A_indicies_numerical = np.where(A_indicies == True)[0]
    A_indicies_numerical = A_indicies
    # initialize the clusters
    clusters = []
    for A_index in range(len(A_indicies_numerical)):
        # Find nearby elements
        nearby = set(np.where(A_eps[A_index, :] >= cluster_eps)[0]) | set(np.where(A_eps[:, A_index] >= cluster_eps)[0])
        in_flag = False
        in_counter = 0
        in_indicies = []
        for i in range(len(clusters)):
            if nearby & clusters[i]:
                clusters[i].update(nearby)  # add the nearby indicies to the cluster
                in_counter += 1  # keep track if the nearby elements belong to more than one of the previously formed clusters
                in_indicies.append(i)  # which clusters nearby shares elements with
                in_flag = True  # tells if it forms a new cluster
        if not in_flag:  # if new cluster, then append to clusters
            clusters.append(set(nearby))
        if in_counter > 1:  # If it belongs to more than one cluster, merge them together
            merged_cluster = set()
            for in_index in in_indicies[::-1]:
                merged_cluster.update(clusters[in_index])
                del clusters[in_index]  # delete the old clusters (now merged)
            clusters.append(merged_cluster)  # append the newly merged clusters
    clusters_full_indicies = []
    for cluster in clusters:
        cluster_full_indicies = set()
        for item in cluster:
            cluster_full_indicies.add(A_indicies_numerical[item])
        clusters_full_indicies.append(cluster_full_indicies)
    # Check to make sure the clustering didn't go wrong
    if sum([len(item) for item in clusters_full_indicies]) != len(A_indicies_numerical):  # Check the correct number of indicies
        raise Exception("For some reason, the total number of indicies in the clusters doesn't equal the number of indicies you started with")
    if set([item for subset in clusters_full_indicies for item in subset]) != set(A_indicies_numerical):  # Make sure no indicies were missed or added
        raise Exception("For some reason, the indicies in all the clusters doesn't match the indicies you started with")
    return clusters_full_indicies#, cluster_LCAs(clusters_full_indicies, taxonomy)


n = 1000
cluster_eps = .01
CEs = MH.import_multiple_from_single_hdf5(f"/home/dkoslicki/Desktop/CMash/dataForShaopeng/TrainingDatabase_{n}_k_60.h5")
mat = MH.form_jaccard_matrix(CEs)
clusters_full_indicies = cluster_matrix(mat, range(n), cluster_eps=cluster_eps)
cluster_sizes = [len(x) for x in clusters_full_indicies]
max_cluster_loc = np.argmax(cluster_sizes)
max_cluster_indicies = list(clusters_full_indicies[max_cluster_loc])
print(len(max_cluster_indicies))
sub_mat = mat[max_cluster_indicies,:][:,max_cluster_indicies]
sub_CEs = [CEs[x] for x in max_cluster_indicies]
out_file_names = [x.input_file_name.decode('utf-8') for x in sub_CEs]
fid = open('/home/dkoslicki/Desktop/CMash/dataForShaopeng/to_select.txt', 'w')
for name in out_file_names:
    fid.write(f"{name}\n")
fid.close()
seaborn.heatmap(sub_mat)
plt.show()
seaborn.clustermap(sub_mat)
plt.show()
# to check the kinds of organisms
#cat to_select.txt  | xargs -I{} sh -c 'zcat {} | head -n 1'