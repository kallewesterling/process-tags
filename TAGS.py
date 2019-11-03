import json, string, csv, yaml, time, progressbar, re, html2text
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
    def __init__(self, ids=[], suppress_warnings=False, progressbar=True):
        self.suppress_warnings = suppress_warnings
        self.ids = ids
        self.progressbar = progressbar
        self.tweets = []
        
        if self.progressbar: bar = progressbar.ProgressBar(maxval=len(self.ids)).start()
        for i, id in enumerate(ids):
            if self.progressbar: bar.update(i)
            tweet = Tweet(id, suppress_warnings=self.suppress_warnings)
            self.tweets.append(tweet)
        if self.progressbar: bar.finish()
            
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

    h = html2text.HTML2Text()
    h.ignore_links = True
    h.bypass_tables = True
    
    text = h.handle(text)
                                                     
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
            text = _expand_contractions(text.replace("’", "'"))

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

def _expand_contractions(text, c_re=None):
    with open("./configuration/contractions.yml") as f:
        contractions = yaml.load(stream=f)
    if c_re is None: c_re = re.compile('(%s)' % '|'.join(contractions.keys()))
    def replace(match):
        return contractions[match.group(0)]
    return(c_re.sub(replace, text))