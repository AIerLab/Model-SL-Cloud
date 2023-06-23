import os
from typing import Tuple

import torch
import torch.nn as nn
from abc import ABC, abstractmethod
from torch.utils.data import DataLoader

from src.comn import AbstractClient

class AbstractModel(nn.Module, ABC):

    def __init__(self, client: AbstractClient, model_dir: str) -> None:
        """
        client: client instance
        model_dir: the folder for model state dict, pt file
        """
        super(AbstractModel, self).__init__()
        self.client = client
        self.model_dir = model_dir

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        pass

    @abstractmethod
    def model_train(self, dataloader: DataLoader, epochs: int, device: torch.device = None):
        pass

    @abstractmethod
    def model_test(self, dataloader: DataLoader, device: torch.device = None) -> Tuple[float, float]:
        pass

    def save_local(self, epoch: int = None, loss: float = None, optimizer_state_dict: dict = None) -> None:
        """
        Save to local.
        """
        PATH = os.path.join(self.model_dir, f"{type(self).__name__}.pt")
        torch.save({
            'epoch': epoch,
            'model_state_dict': self.state_dict(),
            'optimizer_state_dict': optimizer_state_dict,
            'loss': loss,
        }, PATH)
