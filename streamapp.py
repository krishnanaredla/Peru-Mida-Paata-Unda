import streamlit as st
from app import getSongs, getConfig
import pandas as pd

st.title("Get telugu songs with specified words")
st.write("Enter person name/word to search for")
words = st.text_input("Lyric word", "Sravani", max_chars=15)


if st.button("Get Songs"):
    config = getConfig("config.yaml")
    tracks = getSongs(words, config)
    df = pd.DataFrame(tracks)
    if len(tracks) == 1:
        st.table(df)
    else:
        df = df.drop_duplicates(subset=["Song"], keep="first")[
            ~df["Album"].str.contains("Hits")
        ]
        st.table(df)
