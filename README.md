# medchat

A retrieval-augemented generation (RAG) Q/A chatbot designed for use with medical journal articles.

The complete pipeline for this application is outlined briefly below and described in greater detail in the `notebooks/` folder, which contains a series of Jupyter notebooks documenting the development and logic of each stage. Note that while the code in the `src` may differ slightly from that in the notebooks (to integrate with the broader application structure) the code in the notebooks is functionally the same as what is powering the app.


## Requirements

- Docker
- Docker Compose
- [Nvidia Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) 
- **Optional**: [Git LFS](https://git-lfs.com/) (for downloading models from huggingface)

## Downloading Models from Huggingface

Example for BioMistral-7b-DARE:

1. Find model on HuggingFace: https://huggingface.co/BioMistral/BioMistral-7B-DARE
2. Run the following commands (updated with your model's url) from a the models directory:
    ```bash
    git lfs install
    git clone https://huggingface.co/BioMistral/BioMistral-7B-DARE
    ```