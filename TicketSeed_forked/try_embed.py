from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
  model_name ="intfloat/multilingual-e5-small",
  # model_kwargs = {"device":"cpu"},                # gpu 무시하고 cpu 100% 연산처리를 위한 설정 (nvidia 드라이버 충돌 문제 무시)
  encode_kwargs = {"normalize_embeddings":True})

model = embeddings._client
vector = embeddings.embed_query("환불하고 싶어요")

texts = [
    "환불하고 싶은데 어떻게 하나요",                     # 0  질문
    "수령일로부터 7일 이내에 교환 및 반품이 가능합니다",  # 1  답이 있는 문장
    "평일 오후 2시 이전 결제 건은 당일 출고됩니다",       # 2  같은 섹션의 다른 문장
    "고농도 비타민C 유도체가 함유되어 있습니다" ]         # 3  전혀 다른 얘기


vectors = embeddings.embed_documents(texts)

def cos(a,b):
  return sum(x * y for x, y in zip(a,b)) 

def overlap(a,b):
  return len(set(a) & set(b)) / len(set(a) | set(b))

for i, j, label in [
    (0, 1, "환불 질문 ↔ 교환·반품 문장"),
    (0, 2, "환불 질문 ↔ 배송 문장"),
    (0, 3, "환불 질문 ↔ 비타민C 문장"),
    (1, 2, "교환·반품 문장 ↔ 배송 문장")]:
  print(f"{label} / 글자겹침: {overlap(texts[i], texts[j]):.2f} / 코사인: {cos(vectors[i], vectors[j]):.4f}")
  print(f"{label} / 글자겹침: {overlap(texts[i], texts[j]):.2f} / 코사인: {cos(vectors[i], vectors[j]):.4f}")