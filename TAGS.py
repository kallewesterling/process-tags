import json, string, csv, tweepy, yaml, time, progressbar, re

from pprint import pprint
from pathlib import Path
from time import sleep

from nltk.corpus import stopwords


# Set up cache directories
tweet_cache_dir = Path('/Users/kallewesterling/_twitter_cache/tweets/')
user_cache_dir = Path('/Users/kallewesterling/_twitter_cache/users/')

if not tweet_cache_dir.is_dir(): tweet_cache_dir.mkdir(parents=True)
if not user_cache_dir.is_dir(): user_cache_dir.mkdir(parents=True)


class document():
    def __init__(self, path, suppress_warnings=False):
        self.path = Path(path)
        self.suppress_warnings = suppress_warnings
        self._all_ids = None

    @property
    def ids(self):
        if self._all_ids is None:
            self._all_ids = self.get_ids()
        return(self._all_ids)

    def get_ids(self, file=None):
        if file is None: file = self.path
        
        if not Path(file).is_file(): raise RuntimeError(f"File {file} does not exist.")

        all_ids = []
        with Path(file).open("r") as f:
            reader = csv.DictReader(f, delimiter='\t')
            for i, rows in enumerate(reader):
                if not rows['created_at'] and not rows['from_user'] and not rows['text']: pass # skip empty rows
                try:
                    id_int = int(rows['id_str'])
                    all_ids.append(id_int)
                except:
                    if not self.suppress_warnings: print(f"Warning: ID ({rows['id_str']}) could not be interpreted as number.")
        return(list(set(all_ids)))

class Tweet():
    def __init__(self, id_str, suppress_warnings=False):
        self.cache_dir = tweet_cache_dir
        self.suppress_warnings = suppress_warnings
        
        self.id_str = str(id_str)
        self._json = get_json_from_cache(self.id_str, self.cache_dir)
        
        self.error_handle()
        
        self.created_at = self._json.get('created_at', None)
        self.full_text = self._json.get('full_text', None)
        self.truncated = self._json.get('truncated', None)
        self.entities = self._json.get('entities', None)
        self.source = self._json.get('source', None)
        self.in_reply_to_status_id_str = self._json.get('in_reply_to_status_id_str', None)
        self.in_reply_to_user_id_str = self._json.get('in_reply_to_user_id_str', None)
        self.in_reply_to_screen_name = self._json.get('in_reply_to_screen_name', None)
        self.user = self._json.get('user', None)
        self.geo = self._json.get('geo', None)
        self.coordinates = self._json.get('coordinates', None)
        self.place = self._json.get('place', None)
        self.contributors = self._json.get('contributors', None)
        self.is_quote_status = self._json.get('is_quote_status', None)
        self.retweet_count = self._json.get('retweet_count', None)
        self.favorite_count = self._json.get('favorite_count', None)
        self.possibly_sensitive = self._json.get('possibly_sensitive', None)
        self.lang = self._json.get('lang', None)
        self.json_source = self._json.get('json_source', None)
                  
        if isinstance(self.user, dict): self.user = self.user['id_str']
        self.user = User(self.user)

    def error_handle(self):
        if 'error' in self._json:
            error = self._json['error'].replace("'",'"')
            try:
                error = json.loads(error)
                if not self.suppress_warnings: print(f"Warning: Error in tweet ID {self.id_str}. Message: {error[0]['message']} (Twitter error {error[0]['code']})")
            except ValueError:
                print(f"Tried to display error message! {error}")

class User():
    def __init__(self, id_str):
        self.cache_dir = user_cache_dir
        
        self.id_str = str(id_str)
        self._json = get_json_from_cache(self.id_str, self.cache_dir)
        
        self.contributors_enabled = self._json.get('contributors_enabled', None)
        self.created_at = self._json.get('created_at', None)
        self.description = self._json.get('description', None)
        self.entities = self._json.get('entities', None)
        self.favourites_count = self._json.get('favourites_count', None)
        self.followers_count = self._json.get('followers_count', None)
        self.friends_count = self._json.get('friends_count', None)
        self.geo_enabled = self._json.get('geo_enabled', None)
        self.has_extended_profile = self._json.get('has_extended_profile', None)
        self.is_translation_enabled = self._json.get('is_translation_enabled', None)
        self.is_translator = self._json.get('is_translator', None)
        self.json_source = self._json.get('json_source', None)
        self.lang = self._json.get('lang', None)
        self.listed_count = self._json.get('listed_count', None)
        self.location = self._json.get('location', None)
        self.name = self._json.get('name', None)
        self.screen_name = self._json.get('screen_name', None)
        self.protected = self._json.get('protected', None)
        self.time_zone = self._json.get('time_zone', None)
        self.translator_type = self._json.get('translator_type', None)
        self.url = self._json.get('url', None)
        self.utc_offset = self._json.get('utc_offset', None)
        self.verified = self._json.get('verified', None)
                  
class TweetSet():
    def __init__(self, ids=[], suppress_warnings=False):
        self.suppress_warnings = suppress_warnings
        self.ids = ids
        self.tweets = []
        
        bar = progressbar.ProgressBar(max_value=len(self.ids)).start()
        for i, id in enumerate(ids):
            bar.update(i)
            tweet = Tweet(id, suppress_warnings=self.suppress_warnings)
            self.tweets.append(tweet)
        bar.finish()
            
    def __repr__(self):
        return(f"TweetSet consisting of {len(self.tweets)} tweets.")
    

def get_json_from_cache(id_str, cache_dir):
    tweet_cache = cache_dir / id_str
    if not tweet_cache.is_file():
        raise RuntimeError(f"File {id} could not be opened.")
    else:
        with open(tweet_cache, "r") as f:
            _json = json.load(f)
        return(_json)


# imported from my instagram module
def clean_text(text, **kwargs):
    if len(kwargs) == 0: kwargs['set_all'] = True # If no keyword arguments are provided, we will clean out everything

    lower=False
    no_links=False
    no_digits=False
    expand_contractions=False
    remove_stopwords=False
    if "lower" in kwargs and kwargs['lower']: lower = True
    if "no_links" in kwargs and kwargs['no_links']: no_links = True
    if "no_digits" in kwargs and kwargs['no_digits']: no_digits = True
    if "expand_contractions" in kwargs and kwargs['expand_contractions']: expand_contractions = True
    if "remove_stopwords" in kwargs and kwargs['remove_stopwords']: remove_stopwords = True

    strip_emoji=True
    no_hash=True
    no_at=True
    no_punc=True
    strip_spaces=True
    if "strip_emoji" in kwargs and kwargs['strip_emoji']: strip_emoji = True
    if "no_hash" in kwargs and kwargs['no_hash']: no_hash = True
    if "no_at" in kwargs and kwargs['no_at']: no_at = True
    if "no_punc" in kwargs and kwargs['no_punc']: no_punc = True
    if "strip_spaces" in kwargs and kwargs['strip_spaces']: strip_spaces = True

    if "set_all" in kwargs and kwargs['set_all']:
        lower=True
        no_links=True
        no_digits=True
        no_at=True
        no_hash=True
        expand_contractions=True
        remove_stopwords=True
    elif "set_all" in kwargs and not kwargs['set_all']:
        lower=False
        no_links=False
        no_digits=False
        no_at=False
        no_hash=False
        expand_contractions=False
        remove_stopwords=False

    if "strip_emoji" in kwargs and not kwargs['strip_emoji']: strip_emoji = False

    def special_replacements(text):
        replacements = {
            "motherf ing": "motherf-ing"
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return(text)

    if text is not None:
        text = str(text).replace("\n"," ")

        if no_links: text = re.sub(r"(?i)\b((?:[a-z][\w-]+:(?:\/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}\/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))", "", text) # also replace www.????.co/m
        if lower: text = text.lower()

        if no_hash: text = re.sub(r"#[\w-]+", "", text)
        if no_at: text = re.sub(r"@[\w-]+", "", text)
        if no_digits: text = re.sub(r"[{}]".format(string.digits)," ", text)

        if strip_emoji:
            returnString=""
            for character in text:
                try:
                    character.encode("ascii")
                    returnString += character
                except UnicodeEncodeError:
                    returnString += ' '
            text = returnString

        if expand_contractions:
            text = expandContractions(text.replace("’", "'"))

        if no_punc:
            text = re.sub("[{}]".format(string.punctuation)," ", text)
            text = re.sub("[¡“”’]"," ", text)

        if remove_stopwords:
            stops = stopwords.words('english')
            stops.extend([
                'pm',
                'w',
                'rd',
                'th',
                'jan',
                'feb',
                'mar',
                'apr',
                'may',
                'jun',
                'jul',
                'aug',
                'sep',
                'oct',
                'nov',
                'dec',
                'mon',
                'tue',
                'wed',
                'thu',
                'fri',
                'sat',
                'sun'
            ])
            stops = set(stops)
            filtered_words = [word for word in text.split() if word not in stops]
            text = " ".join(filtered_words)

        if strip_spaces:
            text = re.sub(" +"," ", text)
            text = text.strip()

        text = special_replacements(text)

        return(text)
    else:
        return(None)

def expandContractions(text, c_re=None):
    cList = {
        "ain't": "am not",
        "aren't": "are not",
        "can't": "cannot",
        "can't've": "cannot have",
        "'cause": "because",
        "could've": "could have",
        "couldn't": "could not",
        "couldn't've": "could not have",
        "didn't": "did not",
        "doesn't": "does not",
        "don't": "do not",
        "hadn't": "had not",
        "hadn't've": "had not have",
        "hasn't": "has not",
        "haven't": "have not",
        "he'd": "he would",
        "he'd've": "he would have",
        "he'll": "he will",
        "he'll've": "he will have",
        "he's": "he is",
        "how'd": "how did",
        "how'd'y": "how do you",
        "how'll": "how will",
        "how's": "how is",
        "i'd": "i would",
        "i'd've": "i would have",
        "i'll": "i will",
        "i'll've": "i will have",
        "i'm": "i am",
        "i've": "i have",
        "isn't": "is not",
        "it'd": "it had",
        "it'd've": "it would have",
        "it'll": "it will",
        "it'll've": "it will have",
        "it's": "it is",
        "let's": "let us",
        "ma'am": "madam",
        "mayn't": "may not",
        "might've": "might have",
        "mightn't": "might not",
        "mightn't've": "might not have",
        "must've": "must have",
        "mustn't": "must not",
        "mustn't've": "must not have",
        "needn't": "need not",
        "needn't've": "need not have",
        "o'clock": "of the clock",
        "oughtn't": "ought not",
        "oughtn't've": "ought not have",
        "shan't": "shall not",
        "sha'n't": "shall not",
        "shan't've": "shall not have",
        "she'd": "she would",
        "she'd've": "she would have",
        "she'll": "she will",
        "she'll've": "she will have",
        "she's": "she is",
        "should've": "should have",
        "shouldn't": "should not",
        "shouldn't've": "should not have",
        "so've": "so have",
        "so's": "so is",
        "that'd": "that would",
        "that'd've": "that would have",
        "that's": "that is",
        "there'd": "there had",
        "there'd've": "there would have",
        "there's": "there is",
        "they'd": "they would",
        "they'd've": "they would have",
        "they'll": "they will",
        "they'll've": "they will have",
        "they're": "they are",
        "they've": "they have",
        "to've": "to have",
        "wasn't": "was not",
        "we'd": "we had",
        "we'd've": "we would have",
        "we'll": "we will",
        "we'll've": "we will have",
        "we're": "we are",
        "we've": "we have",
        "weren't": "were not",
        "what'll": "what will",
        "what'll've": "what will have",
        "what're": "what are",
        "what's": "what is",
        "what've": "what have",
        "when's": "when is",
        "when've": "when have",
        "where'd": "where did",
        "where's": "where is",
        "where've": "where have",
        "who'll": "who will",
        "who'll've": "who will have",
        "who's": "who is",
        "who've": "who have",
        "why's": "why is",
        "why've": "why have",
        "will've": "will have",
        "won't": "will not",
        "won't've": "will not have",
        "would've": "would have",
        "wouldn't": "would not",
        "wouldn't've": "would not have",
        "y'all": "you all",
        "y'alls": "you alls",
        "y'all'd": "you all would",
        "y'all'd've": "you all would have",
        "y'all're": "you all are",
        "y'all've": "you all have",
        "you'd": "you had",
        "you'd've": "you would have",
        "you'll": "you you will",
        "you'll've": "you you will have",
        "you're": "you are",
        "you've": "you have",
        "aint": "am not",
        "arent": "are not",
        "cant": "cannot",
        "couldve": "could have",
        "couldnt": "could not",
        "didnt": "did not",
        "doesnt": "does not",
        "dont": "do not",
        "hadnt": "had not",
        "hasnt": "has not",
        "havent": "have not",
        "isnt": "is not",
        "shouldve": "should have",
        "shouldnt": "should not",
        "thats": "that is",
        "theyd": "they would",
        "theyre": "they are",
        "theyve": "they have",
        "whats": "what is",
        "wheres": "where is",
        "youll": "you you will",
        "youre": "you are",
        "youve": "you have",
    }
    if c_re is None: c_re = re.compile('(%s)' % '|'.join(cList.keys()))
    def replace(match):
        return cList[match.group(0)]
    return c_re.sub(replace, text)
