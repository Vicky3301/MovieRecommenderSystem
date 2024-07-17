import streamlit as st
import pickle as pkl
import pandas as pd
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


loaded_chunks = []

# Load each chunk and append it to the list
i = 0
while True:
    try:
        with open(f'similarity_chunk_{i}.pkl', 'rb') as file:
            chunk = pickle.load(file)
            loaded_chunks.append(chunk)
        i += 1
    except FileNotFoundError:
        break

# Concatenate the chunks back into the full similarity matrix
similarity= np.vstack(loaded_chunks)







movies_dict = pkl.load(open("movies_dict.pkl", 'rb'))
movies = pd.DataFrame(movies_dict)

def fetch_poster(movie_id):
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    try:
        response = session.get('https://api.themoviedb.org/3/movie/{}?api_key=22c225fdbfdc669303e015e9f5c526f0&language=en-US'.format(movie_id))
        response.raise_for_status()
        data = response.json()
        return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching poster: {e}")
        return None

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    recommended_movies_poster = []
    for i in movie_list:
        movie_id = movies.iloc[i[0]].movie_id
        recommended_movies.append(movies.iloc[i[0]].title)
        poster = fetch_poster(movie_id)
        if poster:
            recommended_movies_poster.append(poster)
        else:
            recommended_movies_poster.append('')  # Add a placeholder or default image URL if necessary
    return recommended_movies, recommended_movies_poster

# Streamlit app
st.title('Movie Recommender System')

selected_movie_name = st.selectbox("Select a movie", movies['title'].values)

if st.button("Recommend"):
    names, posters = recommend(selected_movie_name)

    col1, col2, col3, col4, col5 = st.columns(5)
    if names:
        with col1:
            st.text(names[0])
            st.image(posters[0] if posters[0] else "https://via.placeholder.com/150")
        with col2:
            st.text(names[1])
            st.image(posters[1] if posters[1] else "https://via.placeholder.com/150")
        with col3:
            st.text(names[2])
            st.image(posters[2] if posters[2] else "https://via.placeholder.com/150")
        with col4:
            st.text(names[3])
            st.image(posters[3] if posters[3] else "https://via.placeholder.com/150")
        with col5:
            st.text(names[4])
            st.image(posters[4] if posters[4] else "https://via.placeholder.com/150")
