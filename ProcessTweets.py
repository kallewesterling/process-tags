import spacy, json
from GeoLocator import Location



GEO_BLOCKLIST_TXT = './configuration/block_list.txt'
GEO_MAPPING_YAML = './configuration/location_mapping.yml'


'''
with open('../GeoLocator/test/archive/country_boundingboxes.yaml', 'r') as f:
    COUNTRY_GEOJSON = yaml.safe_load(f)
'''


class AnalysisTools():

  def __init__(self, tweet):
    self.tweet = tweet
    self._potential_names = None
    self.geo = self._setup_geo()

  @property
  def potential_names(self):
    if not self._potential_names: self._potential_names = self._find_potential_names()
    return(self._potential_names)

  def _find_potential_names(self):
      nlp = spacy.load("en_core_web_sm")
      potential_names = []
      doc = nlp(self.tweet.full_text)
      previous_token, previous_token_ = False, ""
      for token in doc:
        if token.pos_ == "PROPN":
          if previous_token:
            potential_names.append(f"{previous_token_} {token}")
          else:
            previous_token = True
            previous_token_ = token
        else:
          previous_token = False
          previous_token_ = ""

      potential_names = [x for x in potential_names if not 'http' in x] # clear out any links
      return(list(set(potential_names)))

  def inside_boundingbox(self, boundingbox={'lat': {'min': 0, 'max': 0}, 'lng': {'min': 0, 'max': 0}}):
    if not 'lat' in boundingbox or not 'lng' in boundingbox: raise RuntimeError("Must provide correct dict.")
    if not 'min' in boundingbox['lat'] or not 'max' in boundingbox['lat']: raise RuntimeError("Must provide correct dict.")
    if not 'min' in boundingbox['lng'] or not 'max' in boundingbox['lng']: raise RuntimeError("Must provide correct dict.")

    if boundingbox['lat']['min'] > boundingbox['lat']['max']: raise RuntimeError("Latitude: min must be smaller than max")
    if boundingbox['lng']['min'] > boundingbox['lng']['max']: raise RuntimeError("Longitude: min must be smaller than max")

    if not 'lat' in self.geo and not 'lng' in self.geo: return(False)

    if (boundingbox['lat']['max'] > self.geo['lat'] > boundingbox['lat']['min']) and (boundingbox['lng']['max'] > self.geo['lng'] > boundingbox['lng']['min']):
      return(True)
    else:
      return(False)

  def inside_country(self, country_code = None):
    boundingbox = {
      'lat': {
            'min': COUNTRY_BOUNDING_BOXES[country_code][1][1],
            'max': COUNTRY_BOUNDING_BOXES[country_code][1][3]
        },
      'lng': {
          'min': COUNTRY_BOUNDING_BOXES[country_code][1][0],
          'max': COUNTRY_BOUNDING_BOXES[country_code][1][2]
      }
    }
    return(self.inside_boundingbox_geopy(boundingbox=boundingbox))


  def inside_boundingbox_geopy(self, boundingbox={'lat': {'min': 0, 'max': 0}, 'lng': {'min': 0, 'max': 0}}):
    if not 'lat' in boundingbox or not 'lng' in boundingbox: raise RuntimeError("Must provide correct dict.")
    if not 'min' in boundingbox['lat'] or not 'max' in boundingbox['lat']: raise RuntimeError("Must provide correct dict.")
    if not 'min' in boundingbox['lng'] or not 'max' in boundingbox['lng']: raise RuntimeError("Must provide correct dict.")

    if boundingbox['lat']['min'] > boundingbox['lat']['max']: raise RuntimeError("Latitude: min must be smaller than max")
    if boundingbox['lng']['min'] > boundingbox['lng']['max']: raise RuntimeError("Longitude: min must be smaller than max")

    from shapely.geometry import Polygon, Point

    if not 'lat' in self.geo and not 'lng' in self.geo: return(False)

    poly = Polygon([(boundingbox['lat']['min'], boundingbox['lng']['min']), (boundingbox['lat']['min'], boundingbox['lng']['max']), (boundingbox['lat']['max'], boundingbox['lng']['max']), (boundingbox['lat']['max'], boundingbox['lng']['min'])])
    p = Point(self.geo['lat'], self.geo['lng'])
    return(p.within(poly))

  def _setup_geo(self):
    errors = 0
    geo = {}
    if self.tweet.geo:
      geo = {
        'lat': self.tweet.geo['coordinates'][0],
        'lng': self.tweet.geo['coordinates'][1],
        'inferred': False,
        'geolocator': None
      }
    else:
      if self.tweet.user.location is not None:
        with open(GEO_BLOCKLIST_TXT, "r") as f: block_list = f.read().split("\n")
        location = Location(self.tweet.user.location, block=block_list, replacements_yaml=GEO_MAPPING_YAML)
        if location.data is not None and 'error' not in location.data:
          geo = {
            'lat': location.data.get('lat', None),
            'lng': location.data.get('lng', None),
            'inferred': True,
            'geolocator': location.data.get('geolocator', None)
          }
    try:
      geo['lat'] = float(geo['lat'])
      geo['lng'] = float(geo['lng'])
    except:
      pass
    return(geo)


def _expand_contractions(text, c_re=None):
    with open("./configuration/contractions.yml") as f:
        contractions = yaml.load(stream=f)
    if c_re is None: c_re = re.compile('(%s)' % '|'.join(contractions.keys()))
    def replace(match):
        return contractions[match.group(0)]
    return(c_re.sub(replace, text))




with open('./data/countries.geojson', 'r') as f:
    COUNTRY_GEOJSON = json.load(f)

def get_country_poly(country_code):
  for c in COUNTRY_GEOJSON['features']:



