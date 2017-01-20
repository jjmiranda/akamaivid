"""TO-DO: Write a description of what this XBlock is."""

import pkg_resources

from xblock.core import XBlock
from xblock.fields import Scope, Integer, String
from xblock.fragment import Fragment
import binascii
import hashlib
import hmac
import os
import re
import time
import urllib

# Force the local timezone to be GMT.
os.environ['TZ'] = 'GMT'
time.tzset()

class AkamaiTokenError(Exception):
    def __init__(self, text):
        self._text = text

    def __str__(self):
        return 'AkamaiTokenError:%s' % self._text

    def _getText(self):
        return str(self)
    text = property(_getText, None, None,
        'Formatted error text.')


class AkamaiTokenConfig:
    def __init__(self):
        self.ip = ''
        self.start_time = None
        self.window = 300
        self.acl = ''
        self.session_id = ''
        self.data = ''
        self.url = ''
        self.salt = ''
        self.field_delimiter = '~'
        self.algo = 'sha256'
        self.param = None
        self.key = 'aabbccddeeff00112233445566778899'
        self.early_url_encoding = False


class AkamaiToken:
    def __init__(self, token_type=None, token_name='hdnts', ip=None,
                 start_time=None, end_time=None, window_seconds=None, url=None,
                 acl=None, key=None, payload=None, algorithm='sha256',
                 salt=None, session_id=None, field_delimiter=None,
                 acl_delimiter=None, escape_early=False,
                 escape_early_upper=False, verbose=False):
        self._token_type = token_type
        self._token_name = token_name
        self._ip = ip
        self._start_time = start_time
        self._end_time = end_time
        self._window_seconds = window_seconds
        self._url = url
        self._acl = acl
        self._key = key
        self._payload = payload
        self._algorithm = algorithm
        if not self._algorithm:
            self._algorithm = 'sha256'
        self._salt = salt
        self._session_id = session_id
        self._field_delimiter = field_delimiter
        if not self._field_delimiter:
            self._field_delimiter = '~'
        self._acl_delimiter = acl_delimiter
        if not self._acl_delimiter:
            self._acl_delimiter = '!'
        self._escape_early = escape_early
        self._escape_early_upper = escape_early_upper
        self._verbose = verbose
        self._warnings = []

    def _getWarnings(self):
        return self._warnings

    warnings = property(_getWarnings, None, None,
        'List of warnings from the last generate request')

    def escapeEarly(self, text):
        if self._escape_early or self._escape_early_upper:
            # Only escape the text if we are configured for escape early.
            new_text = urllib.quote_plus(text)
            if self._escape_early_upper:
                def toUpper(match):
                    return match.group(1).upper()
                return re.sub(r'(%..)', toUpper, new_text)
            else:
                def toLower(match):
                    return match.group(1).lower()
                return re.sub(r'(%..)', toLower, new_text)

        # Return the original, unmodified text.
        return text

    def generate_token(self, token_config):
        """
        Backwards compatible interface.

        """
        # Copy the config parameters where they need to be.
        self._token_name = token_config.param
        self._ip = token_config.ip
        self._start_time = token_config.start_time
        self._end_time = 0
        self._window_seconds = token_config.window
        self._url = token_config.url
        self._acl = token_config.acl
        self._key = token_config.key
        self._payload = token_config.data
        self._algorithm = token_config.algo
        if not self._algorithm:
            self._algorithm = 'sha256'
        self._salt = token_config.salt
        self._session_id = token_config.session_id
        self._field_delimiter = token_config.field_delimiter
        if not self._field_delimiter:
            self._field_delimiter = '~'
        self._acl_delimiter = '!'
        self._escape_early = bool(str(token_config.early_url_encoding).lower()
            in ('yes', 'true'))
        return self.generateToken()

    def generateToken(self):
        if not self._token_name:
            self._token_name = 'hdnts'

        if not self._algorithm:
            self._algorithm = 'sha256'

        if str(self._start_time).lower() == 'now':
            # Initialize the start time if we are asked for a starting time of
            # now.
            self._start_time = int(time.mktime(time.gmtime()))
        elif self._start_time is not None:
            try:
                self._start_time = int(self._start_time)
            except:
                raise AkamaiTokenError('start_time must be numeric or now')

        if self._end_time is not None:
            try:
                self._end_time = int(self._end_time)
            except:
                raise AkamaiTokenError('end_time must be numeric.')

        if self._window_seconds is not None:
            try:
                self._window_seconds = int(self._window_seconds)
            except:
                raise AkamaiTokenError('window_seconds must be numeric.')

        if self._end_time <= 0:
            if self._window_seconds > 0:
                if self._start_time is None:
                    # If we have a duration window without a start time,
                    # calculate the end time starting from the current time.
                    self._end_time = int(time.mktime(time.gmtime())) + \
                        self._window_seconds
                else:
                    self._end_time = self._start_time + self._window_seconds
            else:
                raise AkamaiTokenError('You must provide an expiration time or '
                    'a duration window.')

        if self._end_time < self._start_time:
            self._warnings.append(
                'WARNING:Token will have already expired.')

        if self._key is None or len(self._key) <= 0:
            raise AkamaiTokenError('You must provide a secret in order to '
                'generate a new token.')

        if ((self._acl is None and self._url is None) or
            self._acl is not None and self._url is not None and
            (len(self._acl) <= 0) and (len(self._url) <= 0)):
            raise AkamaiTokenError('You must provide a URL or an ACL.')

        if (self._acl is not None and self._url is not None and
            (len(self._acl) > 0) and (len(self._url) > 0)):
            raise AkamaiTokenError('You must provide a URL OR an ACL, '
                'not both.')

        if self._verbose:
            print('''
Akamai Token Generation Parameters
Token Type      : %s
Token Name      : %s
Start Time      : %s
Window(seconds) : %s
End Time        : %s
IP              : %s
URL             : %s
ACL             : %s
Key/Secret      : %s
Payload         : %s
Algo            : %s
Salt            : %s
Session ID      : %s
Field Delimiter : %s
ACL Delimiter   : %s
Escape Early    : %s
Generating token...''' % (
    ''.join([str(x) for x in [self._token_type] if x is not None]),
    ''.join([str(x) for x in [self._token_name] if x is not None]),
    ''.join([str(x) for x in [self._start_time] if x is not None]),
    ''.join([str(x) for x in [self._window_seconds] if x is not None]),
    ''.join([str(x) for x in [self._end_time] if x is not None]),
    ''.join([str(x) for x in [self._ip] if x is not None]),
    ''.join([str(x) for x in [self._url] if x is not None]),
    ''.join([str(x) for x in [self._acl] if x is not None]),
    ''.join([str(x) for x in [self._key] if x is not None]),
    ''.join([str(x) for x in [self._payload] if x is not None]),
    ''.join([str(x) for x in [self._algorithm] if x is not None]),
    ''.join([str(x) for x in [self._salt] if x is not None]),
    ''.join([str(x) for x in [self._session_id] if x is not None]),
    ''.join([str(x) for x in [self._field_delimiter] if x is not None]),
    ''.join([str(x) for x in [self._acl_delimiter] if x is not None]),
    ''.join([str(x) for x in [self._escape_early] if x is not None])))

        hash_source = ''
        new_token = ''

        if self._ip:
            new_token += 'ip=%s%c' % (self.escapeEarly(self._ip),
                self._field_delimiter)

        if self._start_time is not None:
            new_token += 'st=%d%c' % (self._start_time, self._field_delimiter)

        new_token += 'exp=%d%c' % (self._end_time, self._field_delimiter)

        if self._acl:
            new_token += 'acl=%s%c' % (self.escapeEarly(self._acl),
                self._field_delimiter)

        if self._session_id:
            new_token += 'id=%s%c' % (self.escapeEarly(self._session_id),
                self._field_delimiter)

        if self._payload:
            new_token += 'data=%s%c' % (self.escapeEarly(self._payload),
                self._field_delimiter)

        hash_source += new_token
        if self._url and not self._acl:
            hash_source += 'url=%s%c' % (self.escapeEarly(self._url),
                self._field_delimiter)

        if self._salt:
            hash_source += 'salt=%s%c' % (self._salt, self._field_delimiter)

        if self._algorithm.lower() not in ('sha256', 'sha1', 'md5'):
            raise AkamaiTokenError('Unknown algorithm')
        token_hmac = hmac.new(
            binascii.a2b_hex(self._key),
            hash_source.rstrip(self._field_delimiter),
            getattr(hashlib, self._algorithm.lower())).hexdigest()
        new_token += 'hmac=%s' % token_hmac

        return '%s=%s' % (self._token_name, new_token)

def generateToken(window, acl="/i/testervideo_,270,360,720,mp4.csmil*"):
    generator = AkamaiToken(
        None,
        None,
        None,
        None,
        None,
        window,
        None,
        acl,
        "D6B36D21FE7E75C487C361B6E51CE0BA",
        None,
        None,
        None,
        None,
        None,
        None,
        False,
        False,
        False)
    return generator.generateToken()

class AkamaiVidXBlock( XBlock):
    """
    TO-DO: document what your XBlock does.
    """

    display_name = String(help="El titulo",
        default="Akamai Video",
        scope=Scope.content
    )

    token = String(
        default="aabbccddeeffgghh112334455",
        scope = Scope.user_state,
        help="El token para ver videos de akamai.")

    title = String(
        default="Akamai Video XBlock",
        scope = Scope.content,
        help="El nombre del video de akamai.")

    vttFile = String(
        default="",
        scope = Scope.content,
        help="El link del archivo vtt.")

    acl = String(
        default="testervideo_,270,360,720,.mp4.csmil",
        scope = Scope.content,
        help="El acl del video de akamai.")

    image = String(
        default="http://www.ehl.edu/sites/ehl.edu/files/styles/1312x560/public/work_at_ehl_staff2.jpg",
        scope = Scope.content,
        help="La ruta del acl del video de akamai.")

    # Fields are defined on the class.  You can access them in your code as
    # self.<fieldname>.


    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    # TO-DO: change this view to display your data your own way.
    def studio_view(self, context=None):
        """
        The primary view of the AkamaiVidXBlock, shown to students
        when viewing courses.
        """
        html = self.resource_string("static/html/akamaivid_studio.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/akamaivid.css"))
        frag.add_javascript(self.resource_string("static/js/src/akamaivid_edit.js"))
        frag.initialize_js('AkamaiVidEditXBlock')
        return frag

    def student_view(self, context=None):
        """
        The primary view of the AkamaiVidXBlock, shown to students
        when viewing courses.
        """
        self.token = generateToken(300, "/i/" + self.acl + "*")
        html = self.resource_string("static/html/akamaivid.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/akamaivid.css"))
        frag.add_javascript(self.resource_string("static/js/src/jwplayer2.js"))
        frag.add_javascript(self.resource_string("static/js/src/akamaivid.js"))
        frag.initialize_js('AkamaiVidXBlock')
        return frag

    @XBlock.json_handler
    def studio_submit(self, submissions, suffix=''):
        if len(submissions['title']) > 0:
            self.title = submissions['title']

        if len(submissions['file']) > 4:
            self.acl = submissions['file']

        if len(submissions['image']) > 0:
            self.image = submissions['image']

        if len(submissions['vttFile']) > 5:
            self.vttFile = submissions['vttFile']
        return {
            'result': 'success',
        }


    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("AkamaiVidXBlock",
             """<akamaivid/>
             """),
            ("Multiple AkamaiVidXBlock",
             """<vertical_demo>
                <akamaivid/>
                <akamaivid/>
                <akamaivid/>
                </vertical_demo>
             """),
        ]

def aclFromFile(file):
    return "/i/" + file + "*"
