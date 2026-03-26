import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def preprocess_query(query: str, remove_stopwords: bool = True) -> str:
    """
    Preprocess the input query for better retrieval.
    
    Steps:
    - Lowercase
    - Remove punctuation
    - Tokenize
    - Remove stopwords (optional)
    - Lemmatize words
    - Join back to string
    
    Args:
        query (str): User input query
        remove_stopwords (bool): Whether to remove stopwords
    
    Returns:
        str: Cleaned and preprocessed query
    """
    
    query = query.lower()
    
    query = re.sub(r'[^\w\s]', ' ', query)
    
    tokens = nltk.word_tokenize(query)
    
    if remove_stopwords:
        tokens = [word for word in tokens if word not in stop_words]
    
    tokens = [lemmatizer.lemmatize(word) for word in tokens]
    
    preprocessed_query = ' '.join(tokens)
    
    return preprocessed_query
