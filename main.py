from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Optional
import json
from cocktail_recommender import CocktailRecommender
import os
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize recommender
recommender = CocktailRecommender(
    "cocktails.csv",
    os.getenv("OPENAI_API_KEY")
)

class IngredientsQuery(BaseModel):
    ingredients: List[str]

class SimilarCocktailQuery(BaseModel):
    cocktail_name: str

@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    with open("static/index.html") as f:
        return f.read()

@app.get("/api/ingredients")
async def get_all_ingredients():
    """Get list of all available ingredients"""
    return {"ingredients": sorted(list(recommender.all_ingredients))}

@app.get("/api/favorites")
async def get_favorite_ingredients():
    """Get user's favorite ingredients"""
    favorites = recommender.get_favorite_ingredients()
    return {"favorites": favorites}

@app.get("/api/history")
async def get_search_history():
    """Get recent search history"""
    history = recommender.get_search_history()
    return {"history": history}

@app.post("/api/search/ingredients")
async def search_by_ingredients(query: IngredientsQuery):
    """Search cocktails by ingredients"""
    if not query.ingredients:
        raise HTTPException(status_code=400, detail="No ingredients provided")
    
    results = recommender.ingredient_based_search(query.ingredients)
    return {
        "cocktails": [
            {
                "name": c.name,
                "category": c.category,
                "alcoholic": c.alcoholic,
                "glass_type": c.glass_type,
                "instructions": c.instructions,
                "ingredients": c.ingredients,
                "measures": c.measures,
                "thumbnail": c.thumbnail
            }
            for c in results
        ]
    }

@app.post("/api/search/similar")
async def search_similar_cocktails(query: SimilarCocktailQuery):
    """Find similar cocktails"""
    if not query.cocktail_name:
        raise HTTPException(status_code=400, detail="No cocktail name provided")
    
    results = recommender.similar_cocktail_search(query.cocktail_name)
    if "error" in results:
        raise HTTPException(status_code=400, detail=results["error"])
    
    return {
        "explanation": results["explanation"],
        "cocktails": [
            {
                "name": c.name,
                "category": c.category,
                "alcoholic": c.alcoholic,
                "glass_type": c.glass_type,
                "instructions": c.instructions,
                "ingredients": c.ingredients,
                "measures": c.measures,
                "thumbnail": c.thumbnail
            }
            for c in results["cocktails"]
        ]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            response = {}
            
            # Handle different types of queries
            if "ingredients" in message:
                results = recommender.ingredient_based_search(message["ingredients"])
                response = {
                    "type": "ingredients",
                    "cocktails": [
                        {
                            "name": c.name,
                            "category": c.category,
                            "alcoholic": c.alcoholic,
                            "glass_type": c.glass_type,
                            "instructions": c.instructions,
                            "ingredients": c.ingredients,
                            "measures": c.measures,
                            "thumbnail": c.thumbnail
                        }
                        for c in results
                    ]
                }
            elif "cocktail_name" in message:
                results = recommender.similar_cocktail_search(message["cocktail_name"])
                if "error" in results:
                    response = {"type": "error", "message": results["error"]}
                else:
                    response = {
                        "type": "similar",
                        "explanation": results["explanation"],
                        "cocktails": [
                            {
                                "name": c.name,
                                "category": c.category,
                                "alcoholic": c.alcoholic,
                                "glass_type": c.glass_type,
                                "instructions": c.instructions,
                                "ingredients": c.ingredients,
                                "measures": c.measures,
                                "thumbnail": c.thumbnail
                            }
                            for c in results["cocktails"]
                        ]
                    }
            
            # Send response back to client
            await websocket.send_json(response)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)