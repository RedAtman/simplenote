from dataclasses import dataclass
from email.message import Message
import gzip
import io
import json
import logging
import typing
import urllib.error
import urllib.parse
import urllib.request
import zlib


__all__ = [
    "request",
    "Response",
]
__version__ = "0.0.1"
__author__ = "redatman"
__date__ = "2024-07-12"


logger = logging.getLogger()


DEFAULT_HEADERS = {
    # "Accept": "application/json",
    "Accept": "text/html,application/json,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7",
    "Content-Type": "application/json; charset=UTF-8",
    # 'Cookie': 'SESSION_COOKIE_NAME_PREFIX=redatman_',
    # "Host": "httpbin.org",
    # "Sec-Ch-Ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
    # "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "macOS",
    # "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    # "Sec-Fetch-Site": "none",
    # "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # "User-Agent": "Magic Browser",
    "Referer": "https://www.google.com/",
}


@dataclass
class ContentDecoding:
    default: typing.Callable = lambda response: response.read().decode(response.headers.get_content_charset("utf-8"))
    # TODO: need validate
    gzip: typing.Callable = lambda response: gzip.GzipFile(fileobj=io.BytesIO(response.read())).read().decode()
    # TODO: need validate
    deflate: typing.Callable = lambda response: zlib.decompress(response.read(), -zlib.MAX_WBITS)

    @staticmethod
    def br(response):
        decompressor = zlib.decompressobj(wbits=16 + zlib.MAX_WBITS)
        return decompressor.decompress(response.read()) + decompressor.flush()


class Response(typing.NamedTuple):
    status: int
    headers: Message
    body: str
    error_count: int = 0

    def json(self) -> typing.Union[typing.Dict[str, str], typing.List[typing.Dict[str, str]]]:
        """
        Decode body's JSON.

        Returns:
            Pythonic representation of the JSON object
        """
        try:
            output = json.loads(self.body)
        except json.JSONDecodeError:
            output = {}
        return output

    @property
    def data(self):
        return self.json()


def request(
    url: str,
    data: typing.Optional[typing.Dict] = None,
    params: typing.Optional[typing.Dict] = None,
    headers: typing.Optional[typing.Dict] = None,
    method: str = "GET",
    data_as_json: bool = True,
    error_count: int = 0,
) -> Response:
    if not url.casefold().startswith("http"):
        raise urllib.error.URLError("Incorrect and possibly insecure protocol in url")
    method = method.upper()
    request_data = None
    headers = headers or {}
    data = data or {}
    params = params or {}
    headers = dict(DEFAULT_HEADERS, **headers)

    if method == "GET":
        params = dict(params, **data)
        data = None

    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True, safe="/").lower()

    if data:
        if data_as_json:
            request_data = json.dumps(data).encode()
            headers["Content-Type"] = "application/json; charset=UTF-8"
        else:
            request_data = urllib.parse.urlencode(data).encode()

    logger.debug(f"url: {url}, method: {method}, headers: {headers}, data: {data}")
    httprequest = urllib.request.Request(url, data=request_data, headers=headers, method=method)

    with urllib.request.urlopen(httprequest) as httpresponse:
        try:
            # content_encoding = httpresponse.getheader("Content-Encoding", "default")
            content_encoding = httpresponse.info().get("content-encoding", "default")
            logger.debug(content_encoding)
            body = getattr(ContentDecoding, content_encoding, ContentDecoding.default)(httpresponse)
            response = Response(
                headers=httpresponse.headers,
                status=httpresponse.status,
                body=body,
            )
        except Exception as err:
            logger.error((method, url, headers, data))
            logger.exception(err)
            _body = str(err)
            _headers = Message()
            _status = 500
            error_count += 1
            if isinstance(err, urllib.error.HTTPError):
                _body = str(err.reason)
                _headers = err.headers
                _status = err.code
            elif isinstance(err, urllib.error.URLError):
                _body = str(err.reason)

            response = Response(
                body=_body,
                headers=_headers,
                status=_status,
                error_count=error_count,
            )

    return response
