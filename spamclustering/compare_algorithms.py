import os
import sys
import threading
import queue
import math
import copy
import concurrent.futures

#import all algorithms
import spamclustering.algorithms.cctree as cctree
import spamclustering.algorithms.clope as clope
import spamclustering.algorithms.fptree as fptree
import spamclustering.algorithms.ctph as ctph
# import all other needed modules from spamclustering
import spamclustering.benchmarking.clusterdiff as cdiff
import spamclustering.benchmarking.difftool as dtool
import spamclustering.mailIo.mailIo as mailIo
import spamclustering.preprocess.extentedemailmessage as exm
import spamclustering.preprocess.featureselector as fs

def read_files(input_path):
    file_list = []
    out_path = ''
    if os.path.isdir(input_path):
        print('Input is directory...')
        file_list = filter(lambda i: (os.path.splitext(i)[1] == '.eml'),
                            os.listdir(input_path))
        file_list = [os.path.join(input_path, file) for file in file_list]
    else:
        file_list = [input_path]
    return file_list

def algorithm_constructor_wrapper(job_id, job_args, features, out_path):
    algo_name = job_args[0]
    algo = None
    match(algo_name):
        case "CCTree":
            algo = cctree.CcTreeClustering(features, out_path, job_args[1])
        case "FPTree":
            algo = fptree.FPTreeClustering(features, out_path, job_args[1])
        case "Clope":
            algo = clope.ClopeClustering(features, out_path, job_args[1])
        case "CTPH":
            algo = ctph.Ctph(features, out_path, job_args[1])
    algo.id = job_id
    return algo

def create_extended_mail_list(file_list):
    result = []
    error_log = []
    count = 0
    list_len = len(file_list)
    illformed_files = set()
    for f_path in file_list:
        #print('[{0}|{1}] Processing {2}'.format(count, list_len, file))
        _, message_id = os.path.split(f_path) 
        try:
            message = mailIo.readMailFromEmlFile(f_path)            
            extMessage = exm.ExtentedEmailMessage(message, f_path)
            extMessage.extract_payload()
            result.append(extMessage)
        except UnicodeEncodeError as u_error:
            error_string = \
                'Mail {} is ill formed and therefore skipped!'.format(f_path)
            error_log += error_string + str(u_error) + '\n'
            illformed_files.add(message_id)
            print(error_string)
        except ValueError as v_error:
            error_string = \
                'Mail {} produced a ValueError:{}'.format(fif_pathle,
                                                          str(v_error))
            error_log += error_string + '\n'
            error_log += "Content of mail:\n"
            error_log += str(extMessage.header_dict) + '\n'
            illformed_files.add(message_id)
            print(error_string)
        count += 1
    return (result, error_log, illformed_files)

def collect_features(mail_list):
    featureSelector = fs.FeatureSelector(mail_list)
    return featureSelector.feature_dict

def perform_clustering(algorithm):
    algorithm.do_clustering()
    print("Finished job with ID:", algorithm.id, id(algorithm))
    return algorithm.id, algorithm.cluster_dict

def parallel_benchmarking(algo_id, cluster1, cluster2):
    metrics_dict = cdiff.generate_cluster_diff( cluster1, cluster2)
    return algo_id, metrics_dict

def main():
    """
    Performs clustering with the help of a context triggered piecewise hash
    function. Files found in `<path_to_files>` are processed, similar files
    are grouped in a cluster and the cluster is then written to
    `path_to_cluster_out`.

    Run with:
    
    python -m spamclustering.example_ctph <path_to_files> 
    <path_to_cluster_out>
    
    from root directory.
    """
    argv = sys.argv
    argc = len(sys.argv)
    gold_path = ''
    out_path = ''
    if argc > 0:
        file_list = read_files(argv[1])
        if len(argv) > 2:
            if os.path.isdir(argv[2]):
                gold_path = argv[2]
            else:
                print("Path to gold standard does not contain a suitable" + 
                      "clustering. Terminating...")
                return 
        if len(argv) > 3:
            out_path = argv[3]
            if os.path.isdir(out_path):
                print('Writing output to', out_path)
            else:
                create = input(out_path + ' does not exist. Create? [y|n]')
                if create == 'y':
                    os.mkdir(out_path)

        #create objects of class extendedEmailMessage from input files
        list_of_messages = []
        error_log = []
        list_of_messages, error_log, illformed_files = \
            create_extended_mail_list(file_list)

        num_of_threads = 8
        #create threads to process files
        files_to_process = len(list_of_messages)
        files_per_thread = math.trunc(files_to_process / num_of_threads)
        thread_list = []
        thread_files = []
        offset =  0
        for x in range(0, num_of_threads-1):
            thread_files += [
                list_of_messages[0 + offset:offset + files_per_thread]
            ]
            offset += files_per_thread
        thread_files += [list_of_messages[-(files_to_process - offset):]]

        results = []
        executor = concurrent.futures.ProcessPoolExecutor(num_of_threads)
        for files in thread_files:
            results.append(executor.submit(collect_features, files))

        features = dict()
        for f in concurrent.futures.as_completed(results):
             features.update(f.result())

        concurrent.futures.wait(results)
        results.clear()

        (len(features))

        job_dict = {
            "CCTree 1" : ["CCTree", 50],
            "CCTree 2" : ["CCTree", 40],
            "CCTree 3" : ["CCTree", 30],
            "CCTree 4" : ["CCTree", 60],
            "FPTree 1" : ["FPTree", 5],
            "Clope 1" : ["Clope", 5],
            "Clope 2" : ["Clope", 3],
            "Clope 3" : ["Clope", 7.5],
            "Clope 4" : ["Clope", 10],
            "Clope 5" : ["Clope", 15],
            "Clope 6" : ["Clope", 20],
            "CTPH 1" : ["CTPH", 80],
            "CTPH 2" : ["CTPH", 70],
            "CTPH 3" : ["CTPH", 60],
            "CTPH 4" : ["CTPH", 90],
        }

        num_of_algos = len(job_dict)

        # create for each algorithm and for each configuration of an algorithm
        # a job to run concurrently
        algo_list = []
        for job_id, job_args in job_dict.items():
            algo_list.append(algorithm_constructor_wrapper(job_id,
                                                           job_args,
                                                           features, 
                                                           out_path))

        for algo in algo_list:
            results.append(executor.submit(perform_clustering, algo))

        tree = dtool.Tree(gold_path)
        start = tree.create_from_path(gold_path)
        gold_clustering = start.to_cluster_set()

        for cluster in gold_clustering:
            cluster.remove(illformed_files)
        
        count = 0
        for cluster in gold_clustering:
            for f in cluster.cluster_members:
                count += 1
        clusterings = dict()

        for f in concurrent.futures.as_completed(results):
            algo_id, clustering = f.result()
            clusterings[algo_id] = clustering
         
        concurrent.futures.wait(results)

        for algo in algo_list:
            algo.cluster_dict = clusterings[algo.id]
        
        jobs = []
        executor = concurrent.futures.ProcessPoolExecutor(num_of_threads)
        for algo_id, clustering in clusterings.items():
            other_cluster = set(cluster for _, cluster in clustering.items())
            jobs.append(executor.submit(
                    parallel_benchmarking, 
                    algo_id,
                    gold_clustering,
                    other_cluster)
            )
        
        executor.shutdown(wait=True)
        for j in concurrent.futures.as_completed(jobs):
            print(j.result())
        
        # write clusters to disk if we have an output path
        if os.path.isdir(out_path):
            for algo in algo_list:
                algo_out_path = os.path.join(algo.output_path, algo.id)
                algo.output_path = algo_out_path
                if not os.path.isdir(algo_out_path):
                    os.mkdir(algo_out_path)
                algo.write_cluster_to_disk()

if __name__ == "__main__":
    main()
