# medchat
RAG chatbot for medical Q/A


## Requirements

- Docker
- Docker Compose
- [Nvidia Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) 
- **Optional**: [Git LFS](https://git-lfs.com/) (for downloading models from huggingface)

## Downloading Models from Huggingface

Example for BioMistral-7b-DARE:

1. Find model on HuggingFace: https://huggingface.co/BioMistral/BioMistral-7B-DARE
2. Run the following commands (updated with your model's url) from a the weights directory:
    ```bash
    git lfs install
    git clone https://huggingface.co/BioMistral/BioMistral-7B-DARE
    ```