import os.path
from collections import OrderedDict

import torch

import flwr as fl

from data import AbstractData, CifarData
from model import AbstractModel, DemoModel


class FedClient(fl.client.NumPyClient):
    def __init__(self, data: AbstractData, model: AbstractModel):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.epoch_num = 1

        self.model = model
        self.trainloader, self.testloader = data.trainloader, data.testloader
        self.num_examples = data.get_number_examples()

    def get_parameters(self, config):
        return [val.cpu().numpy() for _, val in self.model.state_dict().items()]

    def set_parameters(self, parameters):
        params_dict = zip(self.model.state_dict().keys(), parameters)
        state_dict = OrderedDict({k: torch.tensor(v) for k, v in params_dict})
        self.model.load_state_dict(state_dict, strict=True)

    def fit(self, parameters, config={}):
        self.set_parameters(parameters)
        self.model.model_train(self.trainloader, self.epoch_num, self.device)
        return self.get_parameters(config), self.num_examples["trainset"], {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, accuracy = self.model.model_test(self.testloader, self.device)
        print(f"loss: {loss}, accuracy{accuracy}")  # TODO refactor to log
        return float(loss), self.num_examples["testset"], {"accuracy": float(accuracy)}

    def run(self):
        fl.client.start_numpy_client(
            server_address="localhost:8080", client=self)
