import torch
from transformers import AutoTokenizer, AutoModel
from gensim.models import Doc2Vec
from gensim.models.doc2vec import TaggedDocument
from sklearn.metrics.pairwise import cosine_similarity
from preprocess import preprocess_text

tokenizer = AutoTokenizer.from_pretrained("roberta-base")
model = AutoModel.from_pretrained("roberta-base")


def encode_text(texts, batch_size=8):
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        encoded_inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512,
        )
        with torch.no_grad():
            outputs = model(**encoded_inputs)
        all_embeddings.extend(outputs.last_hidden_state[:, 0, :].cpu().numpy())
    return all_embeddings


def train_doc2vec_model(paragraphs, topics):
    processed_docs = preprocess_text(paragraphs + topics)
    documents = [
        TaggedDocument(doc.split(), [i]) for i, doc in enumerate(processed_docs)
    ]
    model = Doc2Vec(
        documents, vector_size=300, window=10, min_count=2, workers=4, epochs=100
    )
    return model


def infer_doc2vec_embeddings(model, texts):
    processed_texts = preprocess_text(texts)
    return [model.infer_vector(text.split()) for text in processed_texts]


def calculate_similarities(paragraph_embeddings, topic_embeddings):
    return cosine_similarity(paragraph_embeddings, topic_embeddings)


def match_topics(paragraphs, topics):
    processed_paragraphs = preprocess_text(paragraphs)
    processed_topics = preprocess_text(topics)

    bert_paragraph_embeddings = encode_text(processed_paragraphs)
    bert_topic_embeddings = encode_text(processed_topics)
    bert_similarities = calculate_similarities(
        bert_paragraph_embeddings, bert_topic_embeddings
    )

    doc2vec_model = train_doc2vec_model(paragraphs, topics)
    doc2vec_paragraph_embeddings = infer_doc2vec_embeddings(
        doc2vec_model, processed_paragraphs
    )
    doc2vec_topic_embeddings = infer_doc2vec_embeddings(doc2vec_model, processed_topics)
    doc2vec_similarities = calculate_similarities(
        doc2vec_paragraph_embeddings, doc2vec_topic_embeddings
    )

    return bert_similarities, doc2vec_similarities
