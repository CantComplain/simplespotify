import simpleSpotifyCore.tokenbearers as sstb
from simpleSpotifyCore.api import SimpleSpotifyApi
from . import globalstate as gs
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import os
import webbrowser


class CodeGrabber(BaseHTTPRequestHandler):
    def do_GET(self):

        query = urllib.parse.parse_qs(self.path.strip("/?"))
        code = query.get("code")

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        if code is not None:
            self.server.sscode = code[0]
            # TODO: add text input box
            self.wfile.write(
                             b'<p style="text-align:center;"> '
                             b'           Authorization was successful! <br> '
                             b' <strong> You may return to the program now! </strong> '
                             b'</p>'
                            )

        else:
            self.wfile.write(bytes(f'''
                    <p style="text-align: center;"> 
                        Please go to the <a href="{self.server.ssauthpage}"> Authorization Page </a> to get authorized
                    </p>,
                    encoding = "utf-8"
                    '''))


def host_Local_Server(server,authpage) :
    with HTTPServer(server, CodeGrabber) as h :
        h.ssauthpage = authpage
        while getattr(h,"sscode",None) is None :
            h.handle_request()
        return h.sscode


class Oauth2(sstb.Oauth2) :

    def __init__(self,client_id,client_secret, request_session=None,redirecturl="http://localhost:8080",scopes = None, show_dialog = False,state= None):
        sstb.Oauth2.__init__(self,
                             client_id       = client_id,
                             client_secret   = client_secret,
                             request_session = request_session,
                             redirecturl     = redirecturl,
                             scopes          = scopes,
                             show_dialog     = show_dialog,
                             state           = state
                             )
        self.api = SimpleSpotifyApi(self, session = self._session)

        if gs.current_bearer is None:
            self.use_globally()

    def easy_Auth(self,server="http://localhost:8080", port=8080):
        webbrowser.open(self.get_redirect_uri())
        code = host_Local_Server((server, port), self.get_redirect_uri())
        self.exchange_code_for_token(code)

    def use_globally(self):
        gs.use_globally(self)
        return self


class Client(sstb.Client) :

    def __init__(self, client_id=None, client_secret=None, requests_session=None, scope=None, redirecturl="http://localhost:8080"):

        # SPOTIPY environment variables used for compatability
        if not client_id:
            client_id = os.getenv('SPOTIPY_CLIENT_ID')

        if not client_secret:
            client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')

        if not client_id or not client_secret:
            raise InsufficientCredentials('Insufficient Client Credentials')

        sstb.Client.__init__(self,client_id=client_id,client_secret = client_secret,requests_session=requests_session,scope=scope,
                             redirecturl=redirecturl)
        self.api = SimpleSpotifyApi(self, session = self.session)

        if gs.current_bearer is None:
            self.use_globally()

    def create_oauth2(self,scopes = None,redirecturl=None, show_dialog= False) -> Oauth2 :
        o = Oauth2(client_id = self.client_id, client_secret = self.client_secret, redirecturl = redirecturl or self.redirecturl,
                      request_session = self.session,scopes = scopes or self.scopes,show_dialog = show_dialog)
        o.api = self.api
        return o
    def use_globally(self):
        gs.use_globally(self)
        return self
    # TODO: implement global shared session  with the session property
