from newsapi import NewsApiClient
import pandas as pd
from datetime import datetime, timedelta
import statistics
import google.auth
from google.cloud import language_v1 as language


class StockNews:
    def __init__(self) -> None:
        self.apiKey = "695420fc828541cb8b3b3589c778a226"
        self.newsapi = NewsApiClient(api_key=self.apiKey)
        self.credentials, project_id = google.auth.load_credentials_from_file(r"GoogleCredintials.json")
        self.newsArticles = None
        self.client = language.LanguageServiceClient(credentials=self.credentials)

    def getNewsArticles(self, topic, count, pastDays):
        today = datetime.today()
        pastDays = datetime.today() - timedelta(days=pastDays)

        headlines = self.newsapi.get_everything(q=topic,
                                                qintitle=topic,
                                                from_param=pastDays,
                                                to=today,
                                                sort_by="popularity",
                                                language='en',
                                                page_size=count
                                                )

        df = pd.DataFrame(headlines["articles"])
        self.newsArticles = df[["title", "description", "url"]]

        return self.newsArticles

    def getSentiment(self, text):
        doc = language.Document(content=text, language='en', type_=language.Document.Type.PLAIN_TEXT)
        textSentiment = self.client.analyze_sentiment(
            document=doc,
            encoding_type='UTF32'
        )
        SentimentScore = textSentiment.document_sentiment.score
        return SentimentScore

    def get_sentiment_score(self):
        descCombined = ""
        for desc in self.newsArticles['description']:
            descCombined = descCombined + "\r" + desc
        score = self.getSentiment(descCombined)
        if score >= 0:
            rating = 'Positve'
        else:
            rating = 'Negative'

        score = score * 100
        print(rating)
        print(score)
        return rating, round(score, 0)
