import pickle
from time import sleep

import torch
from model import AbstractModel
from queue import Queue

from helper import IN_QUEUE, OUT_QUEUE, CONDITION


class SplitServerLayer(AbstractModel):
    def __init__(self, model_dir: str, device=None, first_layer=False, last_layer=False):
        super().__init__(model_dir)
        # get all model layers
        self.first_layer = first_layer
        self.last_layer = last_layer

    def forward(self, input_dict: dict) -> torch.Tensor:
        hidden_states = input_dict["hidden_states"]

        CONDITION.acquire()
        device = hidden_states.device

        if not self.first_layer:
            # pickle the tensor data
            serialized_data = pickle.dumps(input_dict)
            # Send the result to the server
            data = {"byte_data": serialized_data, "stage": "forward"}
            OUT_QUEUE.put(data)
            CONDITION.notify()
            print("[LAYER]: Send intermediate result back.")

        CONDITION.wait()
        data = IN_QUEUE.get()
        print("[LAYER]: Receive intermediate result.")
        # print(repr(serialized_data))
        hidden_states = pickle.loads(data["byte_data"])

        if type(hidden_states) is str:  # FIXME why this here?
            CONDITION.wait()
            data = IN_QUEUE.get()
            # print(repr(serialized_data))
            hidden_states = pickle.loads(data["byte_data"])
            hidden_states.to(device)
        CONDITION.release()

        return hidden_states  # suppose to return the hidden states which is changed.

    def backward(self, grad: torch.Tensor):
        if not self.last_layer:
            while not self.out_queue.empty():
                pass
            # pickle the tensor data
            serialized_data = pickle.dumps(grad)
            # Send the result to the server
            data = {"byte_data": serialized_data, "stage": "backward"}
            self.out_queue.put(data)  # FIXME

        while self.in_queue.empty():
            pass
        data = self.in_queue.get()
        # print(repr(serialized_data))
        grad = pickle.loads(data["byte_data"])
        grad = grad.to(self.device)

        return grad
