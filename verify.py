import os
import json
import hashlib
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

DEFAULT_LOG_FILE = 'time_log.json'

def calculate_chained_hash(entry, prev_hash):
    entry_copy = entry.copy()
    entry_copy.pop('hash', None)
    entry_str = json.dumps(entry_copy, sort_keys=True) + prev_hash
    return hashlib.sha256(entry_str.encode()).hexdigest()

def load_and_verify_log(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            data = json.load(f)
            log = data['log']
            prev_hash = ''
            for entry in log:
                expected_hash = entry['hash']
                if calculate_chained_hash(entry, prev_hash) != expected_hash:
                    return False, 'Log file has been tampered with'
                prev_hash = expected_hash
            return True, 'All logs are valid'
    else:
        return False, f'File {file_path} does not exist'

class LogVerifierApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Log Verifier")
        self.set_border_width(10)

        self.box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)

        self.file_chooser_button = Gtk.FileChooserButton(title="Select a Log File", action=Gtk.FileChooserAction.OPEN)
        self.box.pack_start(self.file_chooser_button, True, True, 0)

        self.verify_button = Gtk.Button(label="Verify Logs")
        self.verify_button.connect("clicked", self.on_verify_logs)
        self.box.pack_start(self.verify_button, True, True, 0)

        self.result_label = Gtk.Label(label="")
        self.box.pack_start(self.result_label, True, True, 0)

    def on_verify_logs(self, widget):
        file_path = self.file_chooser_button.get_filename()
        if not file_path:
            file_path = DEFAULT_LOG_FILE
        
        is_valid, message = load_and_verify_log(file_path)
        self.result_label.set_text(message)
        self.show_message_dialog(message, Gtk.MessageType.INFO if is_valid else Gtk.MessageType.ERROR)

    def show_message_dialog(self, message, message_type):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=message_type,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()

def main():
    app = LogVerifierApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
