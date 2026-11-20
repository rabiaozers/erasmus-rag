"""Upload the public demo to a Hugging Face Space and store the Groq key as a Space secret.

Before: `huggingface-cli login` (once) and `python export_index.py` (creates demo/chunks.json, demo/embeddings.npy).
Run:    python deploy_space.py
"""
from huggingface_hub import CommitOperationAdd, HfApi

from rag import groq_api_key

SPACE = "rabiaozers/erasmus-assistant"
FILES = {                                   # path in the Space : path in this project
    "Dockerfile": "space/Dockerfile",
    "README.md": "space/README.md",
    "requirements.txt": "space/requirements.txt",
    "app.py": "app.py",
    "rag.py": "rag.py",
    "retrieval.py": "retrieval.py",
    "memory_store.py": "memory_store.py",
    "web/index.html": "web/index.html",
    "demo/chunks.json": "demo/chunks.json",
    "demo/embeddings.npy": "demo/embeddings.npy",
}

api = HfApi()
api.create_repo(SPACE, repo_type="space", space_sdk="docker", exist_ok=True)
api.add_space_secret(SPACE, "GROQ_API_KEY", groq_api_key())        # never uploaded as a file
api.create_commit(
    SPACE, repo_type="space", commit_message="Deploy the Erasmus+ assistant demo",
    operations=[CommitOperationAdd(path_in_repo=dst, path_or_fileobj=src) for dst, src in FILES.items()],
)
print(f"Deployed: https://huggingface.co/spaces/{SPACE}  (the build takes ~5 minutes)")
