#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import os

current_dir = os.path.split(os.path.abspath(__file__))[0]
root = current_dir.rsplit('/', 1)[0]
sys.path.append(root)

from benchmark import run_benchmark, benchmark_statis, benchmark_metrics

if __name__ == "__main__":
    benchmark_json = f"{root}/benchmark/ics55_benchmark.json"
    
    # run single
    # run_benchmark(benchmark_json=benchmark_json,
    #               target_dir="/nfs/home/huangzengrong/benchmark",
    #               batch_name="ics55_batch_0",
    #               design="arm9")
    
    # run batch
    run_benchmark(benchmark_json=benchmark_json,
                  target_dir="/nfs/home/huangzengrong/benchmark",
                  batch_name="ics55_batch_0")
    
    benchmark_statis(benchmark_dir="/nfs/home/huangzengrong/benchmark/ics55_batch_0")
    benchmark_metrics(benchmark_json=benchmark_json,
                     target_dir="/nfs/home/huangzengrong/benchmark",
                     batch_name="ics55_batch_0")

    exit(0)
