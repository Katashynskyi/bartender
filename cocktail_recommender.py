import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import sqlite3
import ast
from typing import List, Dict, Any
from dataclasses import dataclass
from openai import OpenAI
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

@dataclass
class Cocktail:
    id: int
    name: str
    alcoholic: str
    category: str
    glass_type: str
    instructions: str
    ingredients: List[str]
    measures: List[str]
    thumbnail: str

class CocktailRecommender:
    def __init__(self, csv_path: str, openai_api_key: str = None):
        self.df = pd.read_csv(csv_path)
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        # Use OpenAI API key from environment variables if not provided
        self.openai_client = OpenAI(api_key=openai_api_key or os.getenv('OPENAI_API_KEY'))
        self.init_database()
        self.init_faiss_index()
        
    def init_database(self):
        """Initialize SQLite database for user history"""
        self.conn = sqlite3.connect(':memory:', check_same_thread=False)
        
        # Create tables for user history
        self.conn.execute('''
            CREATE TABLE user_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                query_type TEXT,
                query TEXT,
                ingredients TEXT
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE favorite_ingredients (
                ingredient TEXT PRIMARY KEY,
                count INTEGER DEFAULT 1
            )
        ''')
        
        self.conn.commit()
    
    def init_faiss_index(self):
        """Initialize FAISS index for ingredient-based search"""
        # Create ingredient vectors for each cocktail
        ingredient_vectors = []
        self.all_ingredients = set()
        
        for _, row in self.df.iterrows():
            ingredients = set(ast.literal_eval(row['ingredients']))
            self.all_ingredients.update(ingredients)
        
        self.ingredient_to_idx = {ing: idx for idx, ing in enumerate(self.all_ingredients)}
        
        # Create binary vectors for ingredients
        for _, row in self.df.iterrows():
            vector = np.zeros(len(self.all_ingredients), dtype=np.float32)
            ingredients = set(ast.literal_eval(row['ingredients']))
            for ing in ingredients:
                if ing in self.ingredient_to_idx:
                    vector[self.ingredient_to_idx[ing]] = 1
            ingredient_vectors.append(vector)
        
        # Initialize FAISS index
        self.ingredient_vectors = np.array(ingredient_vectors, dtype=np.float32)
        self.index = faiss.IndexFlatL2(len(self.all_ingredients))
        self.index.add(self.ingredient_vectors)
    
    def _row_to_cocktail(self, row) -> Cocktail:
        """Convert DataFrame row to Cocktail object"""
        return Cocktail(
            id=row['id'],
            name=row['name'],
            alcoholic=row['alcoholic'],
            category=row['category'],
            glass_type=row['glassType'],
            instructions=row['instructions'],
            thumbnail=row['drinkThumbnail'],
            ingredients=ast.literal_eval(row['ingredients']),
            measures=ast.literal_eval(row['ingredientMeasures'])
        )
    
    def ingredient_based_search(self, ingredients: List[str], k: int = 5) -> List[Cocktail]:
        """Search cocktails by ingredients using FAISS"""
        # Create query vector
        query_vector = np.zeros(len(self.all_ingredients), dtype=np.float32)
        for ing in ingredients:
            if ing in self.ingredient_to_idx:
                query_vector[self.ingredient_to_idx[ing]] = 1
        
        # Search using FAISS
        D, I = self.index.search(query_vector.reshape(1, -1), k)
        
        # Get results
        results = []
        for idx in I[0]:
            cocktail = self._row_to_cocktail(self.df.iloc[idx])
            results.append(cocktail)
        
        # Log the search
        self.log_query("ingredient_search", ingredients=ingredients)
        
        return results
    
    def similar_cocktail_search(self, cocktail_name: str, k: int = 5) -> Dict[str, Any]:
        """Find similar cocktails using GPT"""
        try:
            # Format cocktail data for context
            cocktail_data = self.df.apply(
                lambda row: f"{row['name']}: {row['category']} drink with {', '.join(ast.literal_eval(row['ingredients']))}",
                axis=1
            ).str.cat(sep='\n')
            
            # Create prompt
            prompt = f"""Given the following cocktail database:
{cocktail_data}

Find cocktails similar to "{cocktail_name}" based on ingredients and style. 
Explain why they are similar and return only the cocktail names."""
            
            # Get GPT response
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a cocktail expert. Provide similar cocktails with brief explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # Extract cocktail names from response
            response_text = response.choices[0].message.content
            
            # Find mentioned cocktails in our database
            mentioned_cocktails = []
            for _, row in self.df.iterrows():
                if row['name'].lower() in response_text.lower():
                    cocktail = self._row_to_cocktail(row)
                    mentioned_cocktails.append(cocktail)
                if len(mentioned_cocktails) >= k:
                    break
            
            # Log the search
            self.log_query("similar_cocktail", query=cocktail_name)
            
            return {
                'explanation': response_text,
                'cocktails': mentioned_cocktails
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def log_query(self, query_type: str, query: str = "", ingredients: List[str] = None):
        """Log user queries to SQLite"""
        ingredients_str = json.dumps(ingredients) if ingredients else None
        self.conn.execute(
            'INSERT INTO user_history (query_type, query, ingredients) VALUES (?, ?, ?)',
            (query_type, query, ingredients_str)
        )
        
        # Update favorite ingredients if applicable
        if ingredients:
            for ing in ingredients:
                self.conn.execute('''
                    INSERT INTO favorite_ingredients (ingredient, count)
                    VALUES (?, 1)
                    ON CONFLICT(ingredient) DO UPDATE SET count = count + 1
                ''', (ing,))
        
        self.conn.commit()
    
    def get_favorite_ingredients(self, limit: int = 5) -> List[tuple]:
        """Get most frequently searched ingredients"""
        cursor = self.conn.execute('''
            SELECT ingredient, count FROM favorite_ingredients
            ORDER BY count DESC LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_search_history(self, limit: int = 10) -> List[Dict]:
        """Get recent search history"""
        cursor = self.conn.execute('''
            SELECT timestamp, query_type, query, ingredients
            FROM user_history ORDER BY timestamp DESC LIMIT ?
        ''', (limit,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'timestamp': row[0],
                'query_type': row[1],
                'query': row[2],
                'ingredients': json.loads(row[3]) if row[3] else None
            })
        return history

# Example usage
if __name__ == "__main__":
    # The OpenAI API key will be loaded from the .env file
    recommender = CocktailRecommender('cocktails.csv')
    
    # Example: Search by ingredients
    results = recommender.ingredient_based_search(['Vodka', 'Orange juice'])
    print("Cocktails with Vodka and Orange juice:")
    for cocktail in results:
        print(f"- {cocktail.name}")
    
    # Example: Find similar cocktails
    similar = recommender.similar_cocktail_search("Margarita")
    print("\nSimilar to Margarita:")
    print(similar['explanation'])
    
    # Example: Get favorite ingredients
    print("\nMost searched ingredients:")
    for ing, count in recommender.get_favorite_ingredients():
        print(f"- {ing}: {count} searches")