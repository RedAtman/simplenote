from email.message import Message
import json
import logging
import typing
import urllib.error
import urllib.parse
import urllib.request


__all__ = [
    "request",
    "Response",
]


logger = logging.getLogger()


DEFAULT_HEADERS = {
    "Accept": "application/json",
    # "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
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
    # "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "User-Agent": "Magic Browser",
    "Referer": "https://www.google.com/",
}


class Response(typing.NamedTuple):
    body: str
    headers: Message
    status: int
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
        url += "?" + urllib.parse.urlencode(params, doseq=True, safe="/")

    if data:
        if data_as_json:
            request_data = json.dumps(data).encode()
            headers["Content-Type"] = "application/json; charset=UTF-8"
        else:
            request_data = urllib.parse.urlencode(data).encode()

    httprequest = urllib.request.Request(url, data=request_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(httprequest) as httpresponse:
            response = Response(
                headers=httpresponse.headers,
                status=httpresponse.status,
                body=httpresponse.read().decode(httpresponse.headers.get_content_charset("utf-8")),
            )
    except urllib.error.HTTPError as err:
        response = Response(
            body=str(err.reason),
            headers=err.headers,
            status=err.code,
            error_count=error_count + 1,
        )

    return response


if __name__ == "__main__":
    from pprint import pprint

    response = Response(body="{}", headers=Message(), status=200)
    print(response)
    print(response.status)
    print(response.headers)
    print(response.body)

    request_tasks = {
        "get": "https://httpbin.org/get?foo=bar",
        "post": "https://httpbin.org/post",
        "patch": "https://httpbin.org/patch",
    }

    for method, url in request_tasks.items():
        response = request(url, method=method.upper(), data={"title": "foo", "body": method.upper()})
        print(response.status)
        # print(type(response.body))
        # print(response.body)
        # print(response.json())
        pprint(response.data)
