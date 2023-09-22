import pickle
from collections import OrderedDict
from queue import Queue
from threading import Thread, Condition
from time import sleep

import torch.nn
from transformers import AutoTokenizer, AutoModel
import json
import os

import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel

from model import SplitServerModel
from model.chatglm_6b_split_server import ChatGLMForConditionalGeneration, ChatGLMTokenizer, ChatGLMConfig
from splitlearn import SplitServer
from splitlearn import SplitSocket


def main():
    SERVER_DIR = "../tmp/server"

    # Init data and model.
    model = SplitServerModel(SERVER_DIR)
    server = SplitSocket("localhost", 10086)

    def run():
        while True:
            # try:
            response = model.process()
            print("Response:" + response)
            # except:
            #     print("Error")

    t1 = Thread(target=run)
    t2 = Thread(target=server.run)

    t1.start()
    t2.start()

    t1.join()
    t2.join()


if __name__ == "__main__":
    main()
