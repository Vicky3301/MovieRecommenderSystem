from flask import Flask, render_template, request
import pickle as pkl
import pandas as pd
import numpy as np
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os

app = Flask(__name__, template_folder=os.path.dirname(__file__))

loaded_chunks = []

# Load each chunk and append it to the list
i = 0
while True:
    try:
        with open(f'similarity_chunk_{i}.pkl', 'rb') as file:
            chunk = pkl.load(file)
            loaded_chunks.append(chunk)
        i += 1
    except FileNotFoundError:
        break

# Concatenate the chunks back into the full similarity matrix
similarity = np.vstack(loaded_chunks)

movies_dict = pkl.load(open("movies_dict.pkl", 'rb'))
movies = pd.DataFrame(movies_dict)

def fetch_poster(movie_id):
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    try:
        response = session.get(f'https://api.themoviedb.org/3/movie/{movie_id}?api_key=22c225fdbfdc669303e015e9f5c526f0&language=en-US')
        response.raise_for_status()
        data = response.json()
        return "https://image.tmdb.org/t/p/w500/" + data['poster_path']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching poster: {e}")
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

@app.route('/', methods=['GET', 'POST'])
def index():
    movie_titles = movies['title'].values
    if request.method == 'POST':
        selected_movie = request.form['movie']
        names, posters = recommend(selected_movie)
        recommendations = list(zip(names, posters))
        return render_template('index.html', movie_titles=movie_titles, recommendations=recommendations, show_recommendations=True)
    
    return render_template('index.html', movie_titles=movie_titles, recommendations=None, show_recommendations=False)

if __name__ == '__main__':
    app.run(debug=True)
