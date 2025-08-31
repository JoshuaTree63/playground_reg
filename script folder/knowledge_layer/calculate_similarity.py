import json
import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from itertools import combinations

def load_embeddings(json_path, terms_to_compare):
    """
    Loads embeddings for specific terms from the knowledge base.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Knowledge base file not found at: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        knowledge_base = json.load(f)

    embeddings = {}
    found_terms = set()
    for item in knowledge_base:
        term = item['term']
        if term in terms_to_compare:
            # Handle potential duplicate terms by taking the first one found
            if term not in embeddings:
                embeddings[term] = np.array(item['embedding'], dtype=np.float32)
                found_terms.add(term)

    # Check if all requested terms were found
    missing_terms = set(terms_to_compare) - found_terms
    if missing_terms:
        print(f"Warning: The following terms were not found: {', '.join(missing_terms)}")

    return embeddings

def calculate_and_display_similarity(embeddings):
    """
    Calculates and displays the cosine similarity between all pairs of embeddings.
    """
    if len(embeddings) < 2:
        print("Need at least two terms to calculate similarity.")
        return

    # Use itertools.combinations to get all unique pairs of terms
    term_pairs = combinations(embeddings.keys(), 2)

    print("\n--- Cosine Similarity Scores (1 = most similar, 0 = unrelated) ---\n")

    for term1, term2 in term_pairs:
        # Reshape vectors to be 2D arrays for the cosine_similarity function
        vec1 = embeddings[term1].reshape(1, -1)
        vec2 = embeddings[term2].reshape(1, -1)

        # Calculate cosine similarity
        sim_score = cosine_similarity(vec1, vec2)[0][0]

        print(f"Similarity between '{term1}' and '{term2}': {sim_score:.4f}")

if __name__ == "__main__":
    kb_path = os.path.join(os.path.dirname(__file__), 'knowledge_base.json')
    terms = ["Start Date", "Construction Duration", "Tax Rate", "Concession Duration"]
    term_embeddings = load_embeddings(kb_path, terms)

    if term_embeddings:
        calculate_and_display_similarity(term_embeddings)