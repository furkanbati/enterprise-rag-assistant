import chromadb

from config import CHROMA_PATH, COLLECTION_NAME

client = chromadb.PersistentClient(path=CHROMA_PATH)

collection = client.get_collection(COLLECTION_NAME)

result = collection.get()

print(f"Toplam kayıt: {len(result['documents'])}")

print("\nİlk metadata:")
print(result["metadatas"][0])

print("\nİlk doküman:")
print(result["documents"][0][:200])