import json
import os
import torch
from sentence_transformers import SentenceTransformer, util

def perform_semantic_search(query, knowledge_base, embedding_model, top_k=5):
    """
    Performs a semantic search against the knowledge base.

    Args:
        query (str): The user's search query.
        knowledge_base (list): The list of knowledge base entries.
        embedding_model: The loaded SentenceTransformer model.
        top_k (int): The number of top results to return.

    Returns:
        list: A list of the top_k most relevant entries from the knowledge base.
    """
    # 1. Generate the embedding for the user's query
    query_embedding = embedding_model.encode(query, convert_to_tensor=True)

    # 2. Get all embeddings from the knowledge base
    kb_embeddings = torch.tensor(
        [item['embedding'] for item in knowledge_base], 
        dtype=torch.float32
    ).to(embedding_model.device)

    # 3. Calculate cosine similarity between the query and all knowledge base entries
    # The util.cos_sim function is highly optimized for this task
    cosine_scores = util.cos_sim(query_embedding, kb_embeddings)

    # 4. Find the top_k most similar entries
    # We use torch.topk to get the highest scores and their indices.
    # This is more efficient than converting to numpy and works on the GPU.
    top_scores, top_indices = torch.topk(cosine_scores[0], k=top_k)

    # 5. Format and return the results
    search_results = []
    for score, idx in zip(top_scores, top_indices):
        # .item() is used to get the integer value from the tensor
        result = knowledge_base[idx.item()]
        # Add the similarity score to the result for context
        result['similarity_score'] = score.item()
        search_results.append(result)
    
    return search_results

if __name__ == "__main__":
    # --- Setup ---
    project_root = os.path.dirname(os.path.dirname(__file__))
    kb_path = os.path.join(project_root, 'knowledge_layer', 'knowledge_base.json')

    print("Loading knowledge base and embedding model...")
    with open(kb_path, 'r', encoding='utf-8') as f:
        knowledge_base_data = json.load(f)
    
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Model loaded. You can now ask questions.")

    # --- Interactive Search Loop ---
    while True:
        user_query = input("\nEnter your financial question (or type 'exit' to quit): ")
        if user_query.lower() == 'exit':
            break
        
        results = perform_semantic_search(user_query, knowledge_base_data, model, top_k=3)
        
        print("\n--- Top 3 Relevant Terms ---")
        for res in results:
            print(f"\nTerm: {res['term']} (Score: {res['similarity_score']:.4f})")
            print(f"  Source: Sheet '{res['source_sheet']}', Table '{res['source_table']}'")
            print(f"  Definition: {res['definition']}")