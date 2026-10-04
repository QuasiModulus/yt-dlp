from .common import InfoExtractor
from ..utils import (
    float_or_none,
    int_or_none,
    traverse_obj,
    unified_timestamp,
)


class ServusIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:www\.)?
                        (?:
                            servus\.com/(?:(?:at|de)/p/[^/]+|tv/videos)|
                            (?:servustv|pm-wissen)\.com/(?:[^/]+/)?(?:v(?:ideos)?|page)
                        )
                        /(?P<id>[aA]{2}-?\w+|\d+-\d+)
                    '''
    _TESTS = [{
        # URL schema v3
        'url': 'https://www.servustv.com/natur/v/aa-28bycqnh92111/',
        'info_dict': {
            'id': 'AA-28BYCQNH92111',
            'ext': 'mp4',
            'title': 'Klettersteige in den Alpen',
            'description': 'md5:86d0c9eb3b2b6d7cdff247d1ba997ace',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 2823.28,
            'timestamp': 1655752333,
            'upload_date': '20220620',
            'series': 'Bergwelten',
            'season': 'Season 11',
            'season_number': 11,
            'episode': 'Episode 8',
            'episode_number': 8,
            'categories': ['Natur'],
        },
        'params': {'skip_download': 'm3u8'},
    }, {
        # URL schema v4
        'url': 'https://www.servustv.com/de/page/AA-28BYCQNH92111/vie-ferrate-klettersteige-in-den-alpen',
        'only_matching': True,
    }, {
        'url': 'https://www.servustv.com/natur/v/aa-1xg5xwmgw2112/',
        'only_matching': True,
    }, {
        'url': 'https://www.servustv.com/natur/v/aansszcx3yi9jmlmhdc1/',
        'only_matching': True,
    }, {
        # URL schema v2
        'url': 'https://www.servustv.com/videos/aa-1t6vbu5pw1w12/',
        'only_matching': True,
    }, {
        # URL schema v1
        'url': 'https://www.servus.com/de/p/Die-Gr%C3%BCnen-aus-Sicht-des-Volkes/AA-1T6VBU5PW1W12/',
        'only_matching': True,
    }, {
        'url': 'https://www.servus.com/at/p/Wie-das-Leben-beginnt/1309984137314-381415152/',
        'only_matching': True,
    }, {
        'url': 'https://www.servus.com/tv/videos/aa-1t6vbu5pw1w12/',
        'only_matching': True,
    }, {
        'url': 'https://www.servus.com/tv/videos/1380889096408-1235196658/',
        'only_matching': True,
    }, {
        'url': 'https://www.pm-wissen.com/videos/aa-24mus4g2w2112/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url).upper()

        webpage = self._download_webpage(url, video_id)
        card = traverse_obj(self._search_nextjs_v13_data(webpage, video_id, fatal=False), (
            ..., 'featuredCollectionCards', lambda _, v: v['id'] == video_id, any)) or {}

        video = self._download_json(
            f'https://play.redbull.com/init/v1/stv/de/at/personal_computer/http/{video_id}',
            video_id, 'Downloading video JSON')
        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            video['manifest_url'], video_id, 'mp4', m3u8_id='hls')

        season_number, episode_number = self._search_regex(
            r'S(\d+)\s*E(\d+)', traverse_obj(card, (
                'header_badges', lambda _, v: v['type'] == 'episode_info', 'value', {str}, any)) or '',
            'episode info', group=(1, 2), default=(None, None))

        return {
            **self._search_json_ld(webpage, video_id, expected_type='VideoObject', default={}),
            'id': video_id,
            'season_number': int_or_none(season_number),
            'episode_number': int_or_none(episode_number),
            'formats': formats,
            'subtitles': subtitles,
            **traverse_obj(card, {
                'title': ('title', {str}),
                'description': (('long_description', 'short_description'), {str}, filter, any),
                'duration': ('duration', {float_or_none(scale=1000)}),
                'timestamp': ('start_time', {unified_timestamp}),
                'series': ('show_name', {str}),
                'categories': ('content_color', ..., {str}, filter, all, filter),
            }),
        }
