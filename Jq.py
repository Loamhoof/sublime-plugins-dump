from contextlib import closing
import os.path
import subprocess
import tempfile

import sublime_plugin
from sublime import Region


PLUGIN_DIR = os.path.dirname(os.path.realpath(__file__))
BIN_PATH = os.path.join(PLUGIN_DIR, 'jq-linux64')
STATES_DIR = os.path.join(PLUGIN_DIR, 'jq-states')
STATE_FILE = os.path.join(STATES_DIR, 'saved-state')

history = []
history_index = None
current_input = None
caption = "Command:"
default_command = "."


class Jq(sublime_plugin.TextCommand):
    def run(self, edit):
        tmp_file = tempfile.TemporaryFile()
        whole_file = Region(0, self.view.size())
        with closing(tmp_file):
            jq_input = self.view.substr(whole_file).encode('utf-8')
            tmp_file.write(jq_input)
            tmp_file.seek(0)
            jq_output = subprocess.check_output([BIN_PATH, history[-1]], stdin=tmp_file)
        self.view.replace(edit, whole_file, jq_output.decode('utf-8'))


class JqPanel(sublime_plugin.TextCommand):
    def run(self, _):
        global history_index, current_input

        self.panel = self.view.window().show_input_panel(caption, default_command,
            on_done=self.on_done,
            on_change=self.on_change,
            on_cancel=self.on_cancel
        )
        self.panel.settings().set('JqInputPanel', True)
        history_index = 0
        current_input = default_command

    def on_change(self, command):
        global current_input

        if history_index == 0:
            current_input = command

    def on_done(self, command):
        self.panel.settings().set('JqInputPanel', False)
        history.append(command)
        self.view.run_command('jq')

    def on_cancel(self):
        self.panel.settings().set('JqInputPanel', False)


class JqHistory(sublime_plugin.TextCommand):
    def run(self, edit, backwards=False):
        global history_index

        history_index += 1 if backwards else -1
        history_index %= len(history) + 1

        region_to_replace = Region(0, self.view.size())

        self.view.replace(edit, region_to_replace, ([current_input] + history)[-history_index])


class JqSaveState(sublime_plugin.TextCommand):
    def run(self, _):
        with open(STATE_FILE, mode='w') as saved_state_file:
            to_save = self.view.substr(Region(0, self.view.size()))
            saved_state_file.write(to_save)


class JqLoadState(sublime_plugin.TextCommand):
    def run(self, edit):
        with open(STATE_FILE, mode='r') as saved_state_file:
            self.view.replace(edit, Region(0, self.view.size()), saved_state_file.read())
        self.view.run_command('set_file_type', {'syntax': 'Packages/JavaScript/JSON.sublime-syntax'})


try:
    os.mkdir(STATES_DIR)
except FileExistsError:
    pass
