# 🍹 Cocktail Advisor Chat  

A **Python-based chat application** that uses **RAG (Retrieval-Augmented Generation)** and a **vector database** to provide intelligent cocktail recommendations.  

## ✨ Features  

✅ **Natural language chat interface** for cocktail queries  
✅ **Ingredient-based cocktail search** using **FAISS** vector database  
✅ **Similar cocktail recommendations** powered by **GPT**  
✅ **User history & favorite ingredients tracking**  
✅ **Real-time updates** via **WebSocket**  
✅ **REST API endpoints** for all functionality  

## 🛠️ Technical Stack  

- **Backend**: 🚀 FastAPI + WebSocket  
- **Frontend**: 🎨 HTML + Tailwind CSS  
- **Vector Database**: 📚 FAISS  
- **LLM Integration**: 🤖 OpenAI GPT  
- **Data Processing**: 📊 Pandas, NumPy  
- **Embeddings**: 🔠 Sentence Transformers  

## ⚡ Setup Instructions  

1⃣ **Clone the repository**:  
   ```bash
   git clone https://github.com/yourusername/cocktail-advisor-chat.git
   cd cocktail-advisor-chat
   ```  

2⃣ **Create & activate a virtual environment**:  
   ```bash
   python -m venv venv  
   source venv/bin/activate  # On Windows: venv\Scripts\activate  
   ```  

3⃣ **Install dependencies (UV)**:  
   ```bash
   !curl -LsSf https://astral.sh/uv/install.sh | sh
   !uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   !uv pip install sentence-transformers streamlit plotly uvicorn fastapi faiss-cpu openai websockets python-dotenv 
   ```  

4⃣ **Set up environment variables**:  
   - Create a `.env` file with:  
   ```bash
   OPENAI_API_KEY=your_api_key_here  
   ```  

5⃣ **Place the dataset**:  
   - Put `cocktails.csv` in the project root directory  

6⃣ **Run the application**:  
   ```bash
   uvicorn main:app --reload  
   ```  

7⃣ **Access the application**:  
   - Open 🌐 [http://localhost:8000](http://localhost:8000) in your browser  
   - Use the chat interface to interact with the system  



## 🔗 API Endpoints  

📌 `GET /api/ingredients` - Get all available ingredients  
📌 `GET /api/favorites` - Get user’s favorite ingredients  
📌 `GET /api/history` - Get search history  
📌 `POST /api/search/ingredients` - Search cocktails by ingredients  
📌 `POST /api/search/similar` - Find similar cocktails  
📌 `WebSocket /ws` - Real-time chat communication  

## 💬 Example Queries  

📚 **Knowledge Base**:  
- "What are the 5 cocktails containing 🍋 lemon?"  
- "What are the 5 non-alcoholic cocktails containing 🍬 sugar?"  
- "What are my favorite ingredients?"  

🧑‍🍳 **Advisor**:  
- "Recommend 5 cocktails that contain my favorite ingredients"  
- "Recommend a cocktail similar to 'Hot Creamy Bush'"  

## 🏠 Implementation Details  

1⃣ **🔍 RAG System**  
   - Uses **FAISS** for efficient ingredient-based similarity search  
   - Enhances **LLM responses** with cocktail database information  
   - Stores and utilizes **user preferences** for recommendations  

2⃣ **💀 Vector Database**  
   - **FAISS index** for ingredient vectors  
   - **In-memory SQLite** for user history & favorites  
   - **Binary vector representation** for ingredients  

3⃣ **🤖 LLM Integration**  
   - Uses **GPT** for natural language understanding  
   - Custom **prompt engineering** for cocktail recommendations  
   - **Context-aware** responses using cocktail database  

## 🗂 Project Structure  

```
cocktail-advisor-chat/
├── static/
│   └── index.html
├── main.py
├── cocktail_recommender.py
├── requirements.txt
├── cocktails.csv
└── README.md
```  

## 🚀 Future Improvements  

🔒 Add authentication for user-specific history  
⚡ Implement caching for frequent queries  
🧠 Add more sophisticated natural language parsing  
🍸 Enhance cocktail similarity metrics  
🎨 Add image generation for cocktails  

---

This version adds **emoji icons** to make the README more engaging and easier to read! 🎉 Let me know if you need any further tweaks. 🚀

