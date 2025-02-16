import streamlit as st
from cocktail_recommender import CocktailRecommender, Cocktail
import os
from typing import List

def display_cocktail(cocktail: Cocktail):
    """Display a cocktail card"""
    with st.container():
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if cocktail.thumbnail:
                st.image(cocktail.thumbnail, use_container_width=True)
        
        with col2:
            st.subheader(cocktail.name)
            st.write(f"Category: {cocktail.category}")
            st.write(f"Type: {cocktail.alcoholic}")
            st.write(f"Glass: {cocktail.glass_type}")
            
            st.write("**Ingredients:**")
            for measure, ingredient in zip(cocktail.measures, cocktail.ingredients):
                st.write(f"- {measure} {ingredient}")
            
            st.write("**Instructions:**")
            st.write(cocktail.instructions)
        
        st.divider()

def main():
    st.set_page_config(page_title="Cocktail Recommender", layout="wide")
    st.title("🍸 Smart Cocktail Recommender")

    # Initialize recommender
    @st.cache_resource
    def init_recommender():
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = st.secrets.get("OPENAI_API_KEY", None)
        return CocktailRecommender("cocktails.csv", api_key)

    recommender = init_recommender()

    # Sidebar for history and stats
    with st.sidebar:
        st.header("📊 History & Stats")
        
        # Show favorite ingredients
        st.subheader("Most Searched Ingredients")
        favorites = recommender.get_favorite_ingredients()
        for ing, count in favorites:
            st.write(f"- {ing}: {count} searches")
        
        # Show recent searches
        st.subheader("Recent Searches")
        history = recommender.get_search_history()
        for entry in history:
            if entry['query_type'] == 'ingredient_search':
                st.write(f"🔍 Searched for cocktails with: {', '.join(entry['ingredients'])}")
            else:
                st.write(f"🔍 Found similar to: {entry['query']}")

    # Main content - Tabs switched
    tab1, tab2 = st.tabs(["Similar Cocktails", "Ingredient Search"])
    
    with tab1:
        st.header("Find Similar Cocktails")
        cocktail_name = st.text_input(
            "Enter a cocktail related questions:",
            placeholder="e.g., Margarita"
        )
        
        if cocktail_name:
            with st.spinner("Thinking..."):
                results = recommender.similar_cocktail_search(cocktail_name)
                
                if 'error' in results:
                    st.error(f"An error occurred: {results['error']}")
                else:
                    st.write("### Why these cocktails are similar:")
                    st.write(results['explanation'])
                    
                    st.write("### Recommended cocktails:")
                    for cocktail in results['cocktails']:
                        display_cocktail(cocktail)
    
    with tab2:
        st.header("Search by Ingredients")
        ingredients = st.multiselect(
            "Select your favorite ingredients:",
            options=sorted(list(recommender.all_ingredients))
        )
        
        if ingredients:
            results = recommender.ingredient_based_search(ingredients)
            st.write(f"### Found {len(results)} cocktails with your ingredients:")
            for cocktail in results:
                display_cocktail(cocktail)

if __name__ == "__main__":
    main()