import copy
import time
from PyQt5 import QtWidgets

import logging
logger = logging.getLogger(__name__)

from ..api import ApiBase

class ApiError(Exception):
    def __init__(self, reason):
        Exception.__init__(self)
        self.reason = reason


class AliasViewer:
    def __init__(self):
        self.api = ApiBase('/data/player')

    # TODO refactor once async api is implemented
    def _api_request(self, link):
        self.api.request({''})
        try:
            with urllib.request.urlopen(link) as response:
                return json.loads(response.read().decode())
        except urllib.error.URLError as e:
            raise ApiError("Failed to get link {}: {}".format(link, e.reason))
        except json.decoder.JSONDecodeError as e:
            raise ApiError("Failed to decode incoming JSON")

    def _parse_time(self, t):
        return time.strptime(t, "%Y-%m-%dT%H:%M:%SZ")

    def player_id_by_name(self, checked_name):
        api_link = 'https://api.faforever.com/data/player' \
                   '?filter=login=={name}' \
                   '&fields[player]='
        query = api_link.format(name=checked_name)
        response = self._api_request(query)
        if response is None or len(response['data']) == 0:
            return None
        return int(response['data'][0]['id'])

    def names_previously_known(self, user_id):
        queryDict = {'include': 'names',
                     'fields[player]': 'login',
                     'fields[nameRecord]': 'name,changeTime'}
        api_link = 'https://api.faforever.com/data/player/{id_}' \
        query = api_link.format(id_=user_id)
        response = self._api_request(query)
        if response is None or 'included' not in response:
            return []

        aliases = []
        for name in response['included']:
            if name['type'] != 'nameRecord':
                continue
            nick_name = name['attributes']['name']
            try:
                nick_time = self._parse_time(name['attributes']['changeTime'])
            except ValueError:
                continue
            aliases.append({'name': nick_name, 'time': nick_time})

        player = response['data']
        aliases.append({'name': player['attributes']['login'],
                        'time': None})
        return aliases

    def name_used_by_others(self, checked_name):
        query = {'include' : 'names',
                 'filter' : '(login=={name},names.name=={name})'.format(name=checked_name),
                 'fields[player]' : 'login,names',
                 'fields[nameRecord]' : 'name,changeTime'}
        self._api_request(query)
        if response is None or 'data' not in response:
            return []

        players = [p for p in response['data'] if p['type'] == 'player']
        if 'included' not in response:
            names = []
        else:
            names = [n for n in response['included'] if n['type'] == 'nameRecord'
                     and n['attributes']['name'] == checked_name]
        result = []

        for p in players:
            p_login = p['attributes']['login']
            p_id = p['id']
            if 'relationships' not in p:
                p_name_ids = []
            else:
                p_name_ids = set(n['id'] for n in p['relationships']['names']['data'])
            p_names = [n for n in names if n['id'] in p_name_ids]
            result_entry = {'name': p_login, 'id': p_id}

            if p_login == checked_name:
                result_entry['time'] = None
                result.append(copy.copy(result_entry))
            for name in p_names:
                try:
                    t = self._parse_time(name['attributes']['changeTime'])
                    result_entry['time'] = t
                    result.append(copy.copy(result_entry))
                except ValueError:
                    continue
        return result


class AliasFormatter:
    def __init__(self):
        pass

    def nick_times(self, times):
        past_times = [t for t in times if t['time'] is not None]
        current_times = [t for t in times if t['time'] is None]

        past_times.sort(key=lambda t: t['time'])
        name_format = "{}"
        past_format = "{}"
        current_format = "now"
        past_strings = [(name_format.format(e['name']),
                        past_format.format(time.strftime('%Y-%m-%d &nbsp; %H:%M', e['time'])))
                        for e in past_times]
        current_strings = [(name_format.format(e['name']),
                           current_format)
                           for e in current_times]
        return past_strings + current_strings

    def nick_time_table(self, nicks):
        table = '<br/><table border="0" cellpadding="0" cellspacing="1" width="220"><tbody>' \
                '{}' \
                '</tbody></table>'
        head = '<tr><th align="left"> Name</th><th align="center"> used until</th></tr>'
        line_fmt = '<tr><td>{}</td><td align="right">{}</td></tr>'
        lines = [line_fmt.format(*n) for n in nicks]
        return table.format(head + "".join(lines))

    def name_used_by_others(self, others, original_user=None):
        if others is None:
            return ''

        others = [u for u in others if u['name'] != original_user]
        if len(others) == 0 and original_user is None:
            return 'The name has never been used.'
        if len(others) == 0 and original_user is not None:
            return 'The name has never been used by anyone else.'

        return 'The name has previously been used by:{}'.format(
                self.nick_time_table(self.nick_times(others)))

    def names_previously_known(self, response):
        if response is None:
            return ''

        if len(response) == 0:
            return 'The user has never changed their name.'
        return 'The player has previously been known as:{}'.format(
                self.nick_time_table(self.nick_times(response)))


class AliasWindow:
    def __init__(self, parent_widget, api, formatter):
        self._parent_widget = parent_widget
        self._api = AliasViewer()
        self._fmt = AliasFormatter()

    @classmethod
    def build(cls, parent_widget, **kwargs):
        api = AliasViewer()
        formatter = AliasFormatter()
        return cls(parent_widget, api, formatter)

    def view_aliases(self, name, id_=None):
        player_aliases = None
        self._api.name_used_by_others(name, self.on_aliases_response)

    def on_aliases_response(self, other_users):
        try:
            if id_ is None:
                users_now = [u for u in other_users if u['time'] is None]
                if len(users_now) > 0:
                    id_ = users_now[0]['id']
            if id_ is not None:
                player_aliases = self._api.names_previously_known(id_)
        except ApiError as e:
            logger.error(e.reason)
            warning_text = ("Failed to query the FAF API:<br/>"
                            "<i>{exception}</i><br/>"
                            "Some info may be incomplete!")
            warning_text = warning_text.format(exception=e.reason)
            QtWidgets.QMessageBox.warning(self._parent,
                                          "API read error",
                                          warning_text)

        if player_aliases is None and other_users is None:
            return

        alias_format = self._fmt.names_previously_known(player_aliases)
        others_format = self._fmt.name_used_by_others(other_users, name)
        result = '{}<br/><br/>{}'.format(alias_format, others_format)
        QtWidgets.QMessageBox.about(self._parent_widget,
                                    "Aliases : {}".format(name),
                                    result)


class AliasSearchWindow:
    def __init__(self, parent_widget, alias_window):
        self._parent_widget = parent_widget
        self._alias_window = alias_window
        self._search_window = None

    @classmethod
    def build(cls, parent_widget, **kwargs):
        alias_window = AliasWindow.build(parent_widget, **kwargs)
        return cls(alias_window)

    def search_alias(self, name):
        self._alias_window.view_aliases(name)
        self._search_window = None

    def run(self):
        self._search_window = QtWidgets.QInputDialog(self._parent_widget)
        self._search_window.setInputMode(QtWidgets.QInputDialog.TextInput)
        self._search_window.textValueSelected.connect(self.search_alias)
        self._search_window.setLabelText("User name / alias:")
        self._search_window.setWindowTitle("Alias search")
        self._search_window.open()
