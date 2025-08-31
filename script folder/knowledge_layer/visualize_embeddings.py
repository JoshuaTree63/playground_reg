import json
import os
import numpy as np
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

def visualize_embeddings(json_path, terms_to_visualize):
    """
    Loads embeddings from a JSON file, reduces their dimensionality using PCA,
    and creates a 2D scatter plot to visualize their semantic relationships.

    Args:
        json_path (str): The path to the knowledge_base.json file.
        terms_to_visualize (list): A list of exact term strings to plot.
    """
    # --- 1. Load and Filter Data ---
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Knowledge base file not found at: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        knowledge_base = json.load(f)

    # Filter for the specific terms and collect their embeddings and labels
    embeddings = []
    labels = []
    for item in knowledge_base:
        if item['term'] in terms_to_visualize:
            embeddings.append(item['embedding'])
            labels.append(item['term'])

    if not embeddings:
        print("Warning: None of the specified terms were found in the knowledge base.")
        print(f"Terms looked for: {terms_to_visualize}")
        return

    # --- 2. Reduce Dimensionality ---
    # Convert to a NumPy array for scikit-learn
    X = np.array(embeddings, dtype=np.float32)

    # Use PCA to reduce from 384 to 2 dimensions
    pca = PCA(n_components=2)
    X_reduced = pca.fit_transform(X)

    # --- 3. Create the Plot ---
    plt.figure(figsize=(10, 8))
    plt.scatter(X_reduced[:, 0], X_reduced[:, 1], alpha=0.7)

    # Add labels to each point
    for i, label in enumerate(labels):
        plt.annotate(label, (X_reduced[i, 0], X_reduced[i, 1]), textcoords="offset points", xytext=(0,10), ha='center')

    plt.title('2D Visualization of Financial Term Embeddings (via PCA)')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    # Define the path to your knowledge base
    kb_path = os.path.join(os.path.dirname(__file__), 'knowledge_base.json')
    # Specify the terms you want to see on the map
    terms = ["Start Date", "Construction Duration", "Tax Rate"]
    visualize_embeddings(kb_path, terms)