from .common import InfoExtractor
from ..utils import (
    clean_html,
    float_or_none,
    traverse_obj,
    try_call,
)

# more info about jixie:
# [1] https://jixie.atlassian.net/servicedesk/customer/portal/2/article/1339654214?src=-1456335525,
# [2] https://scripts.jixie.media/jxvideo.3.1.min.js


class JixieBaseIE(InfoExtractor):
    def _extract_data_from_jixie_id(self, display_id, video_id, webpage):
        json_data = self._download_json(
            'https://apidam.jixie.io/api/public/stream', display_id,
            query={'metadata': 'full', 'video_id': video_id})['data']

        formats, subtitles = [], {}
        for stream in json_data['streams']:
            if stream.get('type') == 'HLS':
                fmt, sub = self._extract_m3u8_formats_and_subtitles(stream.get('url'), display_id, ext='mp4')
                if json_data.get('drm'):
                    for f in fmt:
                        f['has_drm'] = True
                formats.extend(fmt)
                self._merge_subtitles(sub, target=subtitles)
            else:
                formats.append({
                    'url': stream.get('url'),
                    'width': stream.get('width'),
                    'height': stream.get('height'),
                    'ext': 'mp4',
                })

        self._sort_formats(formats)
        return {
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            'title': json_data.get('title') or self._html_search_meta(['og:title', 'twitter:title'], webpage),
            'description': (clean_html(traverse_obj(json_data, ('metadata', 'description')))
                            or self._html_search_meta(['description', 'og:description', 'twitter:description'], webpage)),
            'thumbnails': traverse_obj(json_data, ('metadata', 'thumbnails')),
            'duration': float_or_none(traverse_obj(json_data, ('metadata', 'duration'))),
            'tags': try_call(lambda: (json_data['metadata']['keywords'] or None).split(',')),
            'categories': try_call(lambda: (json_data['metadata']['categories'] or None).split(',')),
            'uploader_id': json_data.get('owner_id'),
        }
