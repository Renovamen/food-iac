import os
import sys
import subprocess
import threading
import json
import numpy as np
import ast
import tempfile

import time
import shutil

# Assumes spice.jar is in the same directory as spice.py.  Change as needed.
SPICE_JAR = 'spice-1.0.jar'
TEMP_DIR = 'tmp'
CACHE_DIR = 'cache'

class Spice:
    """Main Class to compute the SPICE metric"""

    def __init__(self):
        cwd = os.path.dirname(os.path.abspath(__file__))
        cache_dir=os.path.join(cwd, CACHE_DIR, str(time.time()))
        self.cache_dir = cache_dir
        if not os.path.exists(cache_dir):
          os.makedirs(cache_dir)

    def float_convert(self, obj):
        try:
          return float(obj)
        except:
          return np.nan

    def compute_score(self, gts, res):
        assert len(gts) == len(res)

        # Prepare temp input file for the SPICE scorer
        input_data = []
        imgIds = []

        for id, hypo in enumerate(res):
            hypo = hypo
            ref = gts[id]

            # Sanity check.
            assert(type(hypo) is list)
            assert(len(hypo) >= 1)
            assert(type(ref) is list)
            assert(len(ref) >= 1)

            input_data.append({
              "image_id" : id,
              "tests" : hypo,
              "refs" : ref
            })
            imgIds.append(id)

        cwd = os.path.dirname(os.path.abspath(__file__))
        temp_dir=os.path.join(cwd, TEMP_DIR)
        if not os.path.exists(temp_dir):
          os.makedirs(temp_dir)
        in_file = tempfile.NamedTemporaryFile(delete=False, dir=temp_dir)
        in_file.write(json.dumps(input_data, indent=2).encode('utf-8'))
        in_file.close()

        # Start job
        out_file = tempfile.NamedTemporaryFile(delete=False, dir=temp_dir)
        out_file.close()
        spice_cmd = ['java', '-jar', '-Xmx8G', SPICE_JAR, in_file.name,
          '-cache', self.cache_dir,
          '-out', out_file.name,
          '-subset',
          '-silent'
        ]
        subprocess.check_call(spice_cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)))

        # Read and process results
        with open(out_file.name) as data_file:
          results = json.load(data_file)
        os.remove(in_file.name)
        os.remove(out_file.name)

        imgId_to_scores = {}
        spice_scores = []
        for item in results:
          imgId_to_scores[item['image_id']] = item['scores']
          spice_scores.append(self.float_convert(item['scores']['All']['f']))
        average_score = np.mean(np.array(spice_scores))
        scores = []
        for image_id in imgIds:
          # Convert none to NaN before saving scores over subcategories
          score_set = {}
          for category,score_tuple in imgId_to_scores[image_id].items():
            score_set[category] = {k: self.float_convert(v) for k, v in score_tuple.items()}
          scores.append(score_set)
        return average_score, scores

    def method(self):
        return "SPICE"

    def __del__(self):
        shutil.rmtree(self.cache_dir)
