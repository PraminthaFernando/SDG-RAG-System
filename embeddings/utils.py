import torch
import torch.nn.functional as F

def average_pool(last_hidden_states, attention_mask):
    last_hidden = last_hidden_states.masked_fill(
        ~attention_mask[..., None].bool(),
        0.0
    )
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def normalize_embeddings(embeddings):
    return F.normalize(embeddings, p=2, dim=1)