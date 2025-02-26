import re
import urllib.parse
import uuid

from .common import InfoExtractor
from ..utils import (
    determine_ext,
    int_or_none,
    join_nonempty,
    parse_duration,
    parse_iso8601,
    traverse_obj,
    try_get,
)


class MLBBaseIE(InfoExtractor):
    def _real_extract(self, url):
        display_id = self._match_id(url)
        video = self._download_video_data(display_id)
        video_id = video['id']
        title = video['title']
        feed = self._get_feed(video)

        formats = []
        for playback in (feed.get('playbacks') or []):
            playback_url = playback.get('url')
            if not playback_url:
                continue
            name = playback.get('name')
            ext = determine_ext(playback_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    playback_url, video_id, 'mp4',
                    'm3u8_native', m3u8_id=name, fatal=False))
            else:
                f = {
                    'format_id': name,
                    'url': playback_url,
                }
                mobj = re.search(r'_(\d+)K_(\d+)X(\d+)', name)
                if mobj:
                    f.update({
                        'height': int(mobj.group(3)),
                        'tbr': int(mobj.group(1)),
                        'width': int(mobj.group(2)),
                    })
                mobj = re.search(r'_(\d+)x(\d+)_(\d+)_(\d+)K\.mp4', playback_url)
                if mobj:
                    f.update({
                        'fps': int(mobj.group(3)),
                        'height': int(mobj.group(2)),
                        'tbr': int(mobj.group(4)),
                        'width': int(mobj.group(1)),
                    })
                formats.append(f)
        self._sort_formats(formats)

        thumbnails = []
        for cut in (try_get(feed, lambda x: x['image']['cuts'], list) or []):
            src = cut.get('src')
            if not src:
                continue
            thumbnails.append({
                'height': int_or_none(cut.get('height')),
                'url': src,
                'width': int_or_none(cut.get('width')),
            })

        language = (video.get('language') or 'EN').lower()

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'description': video.get('description'),
            'duration': parse_duration(feed.get('duration')),
            'thumbnails': thumbnails,
            'timestamp': parse_iso8601(video.get(self._TIMESTAMP_KEY)),
            'subtitles': self._extract_mlb_subtitles(feed, language),
        }


class MLBIE(MLBBaseIE):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:[\da-z_-]+\.)*mlb\.com/
                        (?:
                            (?:
                                (?:[^/]+/)*video/[^/]+/c-|
                                (?:
                                    shared/video/embed/(?:embed|m-internal-embed)\.html|
                                    (?:[^/]+/)+(?:play|index)\.jsp|
                                )\?.*?\bcontent_id=
                            )
                            (?P<id>\d+)
                        )
                    '''
    _EMBED_REGEX = [
        r'<iframe[^>]+?src=(["\'])(?P<url>https?://m(?:lb)?\.mlb\.com/shared/video/embed/embed\.html\?.+?)\1',
        r'data-video-link=["\'](?P<url>http://m\.mlb\.com/video/[^"\']+)',
    ]
    _TESTS = [
        {
            'url': 'https://www.mlb.com/mariners/video/ackleys-spectacular-catch/c-34698933',
            'md5': '632358dacfceec06bad823b83d21df2d',
            'info_dict': {
                'id': '34698933',
                'ext': 'mp4',
                'title': "Ackley's spectacular catch",
                'description': 'md5:7f5a981eb4f3cbc8daf2aeffa2215bf0',
                'duration': 66,
                'timestamp': 1405995000,
                'upload_date': '20140722',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'https://www.mlb.com/video/stanton-prepares-for-derby/c-34496663',
            'md5': 'bf2619bf9cacc0a564fc35e6aeb9219f',
            'info_dict': {
                'id': '34496663',
                'ext': 'mp4',
                'title': 'Stanton prepares for Derby',
                'description': 'md5:d00ce1e5fd9c9069e9c13ab4faedfa57',
                'duration': 46,
                'timestamp': 1405120200,
                'upload_date': '20140711',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'https://www.mlb.com/video/cespedes-repeats-as-derby-champ/c-34578115',
            'md5': '99bb9176531adc600b90880fb8be9328',
            'info_dict': {
                'id': '34578115',
                'ext': 'mp4',
                'title': 'Cespedes repeats as Derby champ',
                'description': 'md5:08df253ce265d4cf6fb09f581fafad07',
                'duration': 488,
                'timestamp': 1405414336,
                'upload_date': '20140715',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'https://www.mlb.com/video/bautista-on-home-run-derby/c-34577915',
            'md5': 'da8b57a12b060e7663ee1eebd6f330ec',
            'info_dict': {
                'id': '34577915',
                'ext': 'mp4',
                'title': 'Bautista on Home Run Derby',
                'description': 'md5:b80b34031143d0986dddc64a8839f0fb',
                'duration': 52,
                'timestamp': 1405405122,
                'upload_date': '20140715',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
        {
            'url': 'https://www.mlb.com/video/hargrove-homers-off-caldwell/c-1352023483?tid=67793694',
            'only_matching': True,
        },
        {
            'url': 'http://m.mlb.com/shared/video/embed/embed.html?content_id=35692085&topic_id=6479266&width=400&height=224&property=mlb',
            'only_matching': True,
        },
        {
            'url': 'http://mlb.mlb.com/shared/video/embed/embed.html?content_id=36599553',
            'only_matching': True,
        },
        {
            'url': 'http://mlb.mlb.com/es/video/play.jsp?content_id=36599553',
            'only_matching': True,
        },
        {
            'url': 'https://www.mlb.com/cardinals/video/piscottys-great-sliding-catch/c-51175783',
            'only_matching': True,
        },
        {
            # From http://m.mlb.com/news/article/118550098/blue-jays-kevin-pillar-goes-spidey-up-the-wall-to-rob-tim-beckham-of-a-homer
            'url': 'http://mlb.mlb.com/shared/video/embed/m-internal-embed.html?content_id=75609783&property=mlb&autoplay=true&hashmode=false&siteSection=mlb/multimedia/article_118550098/article_embed&club=mlb',
            'only_matching': True,
        },
    ]
    _TIMESTAMP_KEY = 'date'

    @staticmethod
    def _get_feed(video):
        return video

    @staticmethod
    def _extract_mlb_subtitles(feed, language):
        subtitles = {}
        for keyword in (feed.get('keywordsAll') or []):
            keyword_type = keyword.get('type')
            if keyword_type and keyword_type.startswith('closed_captions_location_'):
                cc_location = keyword.get('value')
                if cc_location:
                    subtitles.setdefault(language, []).append({
                        'url': cc_location,
                    })
        return subtitles

    def _download_video_data(self, display_id):
        return self._download_json(
            'http://content.mlb.com/mlb/item/id/v1/%s/details/web-v1.json' % display_id,
            display_id)


class MLBVideoIE(MLBBaseIE):
    _VALID_URL = r'https?://(?:www\.)?mlb\.com/(?:[^/]+/)*video/(?P<id>[^/?&#]+)'
    _TEST = {
        'url': 'https://www.mlb.com/mariners/video/ackley-s-spectacular-catch-c34698933',
        'md5': '632358dacfceec06bad823b83d21df2d',
        'info_dict': {
            'id': 'c04a8863-f569-42e6-9f87-992393657614',
            'ext': 'mp4',
            'title': "Ackley's spectacular catch",
            'description': 'md5:7f5a981eb4f3cbc8daf2aeffa2215bf0',
            'duration': 66,
            'timestamp': 1405995000,
            'upload_date': '20140722',
            'thumbnail': r're:^https?://.+',
        },
    }
    _TIMESTAMP_KEY = 'timestamp'

    @classmethod
    def suitable(cls, url):
        return False if MLBIE.suitable(url) else super(MLBVideoIE, cls).suitable(url)

    @staticmethod
    def _get_feed(video):
        return video['feeds'][0]

    @staticmethod
    def _extract_mlb_subtitles(feed, language):
        subtitles = {}
        for cc_location in (feed.get('closedCaptions') or []):
            subtitles.setdefault(language, []).append({
                'url': cc_location,
            })

    def _download_video_data(self, display_id):
        # https://www.mlb.com/data-service/en/videos/[SLUG]
        return self._download_json(
            'https://fastball-gateway.mlb.com/graphql',
            display_id, query={
                'query': '''{
  mediaPlayback(ids: "%s") {
    description
    feeds(types: CMS) {
      closedCaptions
      duration
      image {
        cuts {
          width
          height
          src
        }
      }
      playbacks {
        name
        url
      }
    }
    id
    timestamp
    title
  }
}''' % display_id,
            })['data']['mediaPlayback'][0]


class MLBTVIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?mlb\.com/tv/g(?P<id>\d{6})'
    _NETRC_MACHINE = 'mlb'

    _TESTS = [{
        'url': 'https://www.mlb.com/tv/g661581/vee2eff5f-a7df-4c20-bdb4-7b926fa12638',
        'info_dict': {
            'id': '661581',
            'ext': 'mp4',
            'title': '2022-07-02 - St. Louis Cardinals @ Philadelphia Phillies',
        },
        'params': {
            'skip_download': True,
        },
    }]
    _access_token = None

    def _real_initialize(self):
        if not self._access_token:
            self.raise_login_required(
                'All videos are only available to registered users', method='password')

    def _perform_login(self, username, password):
        data = f'grant_type=password&username={urllib.parse.quote(username)}&password={urllib.parse.quote(password)}&scope=openid offline_access&client_id=0oa3e1nutA1HLzAKG356'
        access_token = self._download_json(
            'https://ids.mlb.com/oauth2/aus1m088yK07noBfh356/v1/token', None,
            headers={
                'User-Agent': 'okhttp/3.12.1',
                'Content-Type': 'application/x-www-form-urlencoded'
            }, data=data.encode())['access_token']

        entitlement = self._download_webpage(
            f'https://media-entitlement.mlb.com/api/v3/jwt?os=Android&appname=AtBat&did={str(uuid.uuid4())}', None,
            headers={
                'User-Agent': 'okhttp/3.12.1',
                'Authorization': f'Bearer {access_token}'
            })

        data = f'grant_type=urn:ietf:params:oauth:grant-type:token-exchange&subject_token={entitlement}&subject_token_type=urn:ietf:params:oauth:token-type:jwt&platform=android-tv'
        self._access_token = self._download_json(
            'https://us.edge.bamgrid.com/token', None,
            headers={
                'Accept': 'application/json',
                'Authorization': 'Bearer bWxidHYmYW5kcm9pZCYxLjAuMA.6LZMbH2r--rbXcgEabaDdIslpo4RyZrlVfWZhsAgXIk',
                'Content-Type': 'application/x-www-form-urlencoded'
            }, data=data.encode())['access_token']

    def _real_extract(self, url):
        video_id = self._match_id(url)
        airings = self._download_json(
            f'https://search-api-mlbtv.mlb.com/svc/search/v2/graphql/persisted/query/core/Airings?variables=%7B%22partnerProgramIds%22%3A%5B%22{video_id}%22%5D%2C%22applyEsniMediaRightsLabels%22%3Atrue%7D',
            video_id)['data']['Airings']
    
        formats, subtitles = [], {}
        for airing in airings:
            m3u8_url = self._download_json(
                airing['playbackUrls'][0]['href'].format(scenario='browser~csai'), video_id,
                headers={
                    'Authorization': self._access_token,
                    'Accept': 'application/vnd.media-service+json; version=2'
                })['stream']['complete']
            f, s = self._extract_m3u8_formats_and_subtitles(
                m3u8_url, video_id, 'mp4', m3u8_id=join_nonempty(airing.get('feedType'), airing.get('feedLanguage')))
            formats.extend(f)
            self._merge_subtitles(s, target=subtitles)

        self._sort_formats(formats)
        return {
            'id': video_id,
            'title': traverse_obj(airings, (..., 'titles', 0, 'episodeName'), get_all=False),
            'formats': formats,
            'subtitles': subtitles,
            'http_headers': {'Authorization': f'Bearer {self._access_token}'},
        }
