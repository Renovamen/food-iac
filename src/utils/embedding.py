import os
import torch
import numpy as np
from tqdm import tqdm

def init_embeddings(embeddings: torch.Tensor) -> None:
    """
    Fill embedding tensor with values from the uniform distribution.

    Args:
        embeddings (torch.Tensor): Embedding tensor
    """
    bias = np.sqrt(3.0 / embeddings.size(1))
    torch.nn.init.uniform_(embeddings, -bias, bias)


def load_embeddings(
    emb_file: str, word_map: dict, output_folder: str, output_basename: str
) -> (torch.Tensor, int):
    """
    Create an embedding tensor for the specified word map, for loading into
    the model.

    Args:
        emb_file (str): Word embeddings file (stored in GloVe format)
        word_map (dict): Word map
        output_folder (str): Path to the folder to store output files
        output_basename (str): Basename for output files

    Returns:
        embeddings (torch.Tensor): Embeddings in the same order as the words in the word map
        embed_dim (int): Dimension of embeddings
    """

    emb_basename = os.path.basename(emb_file)
    cache_path = os.path.join(output_folder, emb_basename + '_' + output_basename + '.pth.tar')

    # no cache, load embeddings from .txt file
    if not os.path.isfile(cache_path):
        # find embedding dimension
        with open(emb_file, 'r') as f:
            embed_dim = len(f.readline().split(' ')) - 1
            num_lines = len(f.readlines())

        vocab = set(word_map.keys())

        # create and initialize a tensor to hold embeddings
        embeddings = torch.FloatTensor(len(vocab), embed_dim)
        init_embeddings(embeddings)

        # read embedding file
        for line in tqdm(open(emb_file, 'r'), total = num_lines, desc = 'Loading embeddings'):
            line = line.split(' ')

            emb_word = line[0]
            embedding = list(map(lambda t: float(t), filter(lambda n: n and not n.isspace(), line[1:])))

            # ignore word if not in train_vocab
            if emb_word not in vocab:
                continue

            embeddings[word_map[emb_word]] = torch.FloatTensor(embedding)

        # create cache file so we can load it quicker the next time
        print('Saving vectors to {}'.format(cache_path))
        torch.save((embeddings, embed_dim), cache_path)

    # load embeddings from cache
    else:
        print('Loading embeddings from {}'.format(cache_path))
        embeddings, embed_dim = torch.load(cache_path)

    return embeddings, embed_dim
