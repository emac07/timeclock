import time, os, json, hashlib, gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

LOG_FILE = 'time_log.json'

def calculate_hash(entry, prev_hash=''):
    entry = entry.copy()
    entry.pop('hash', None)
    return hashlib.sha256((json.dumps(entry, sort_keys=True) + prev_hash).encode()).hexdigest()

def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r') as f:
        log = json.load(f)['log']
    prev_hash = ''
    for entry in log:
        if entry['hash'] != calculate_hash(entry, prev_hash):
            raise ValueError('Log file has been tampered with')
        prev_hash = entry['hash']
    return log

def save_log(log):
    prev_hash = ''
    for entry in log:
        entry['hash'] = calculate_hash(entry, prev_hash)
        prev_hash = entry['hash']
    with open(LOG_FILE, 'w') as f:
        json.dump({'log': log}, f, indent=4)

def clock(log, entry_type):
    entry = {'type': entry_type, 'time': time.strftime('%Y-%m-%d %H:%M:%S')}
    log.append(entry)
    save_log(log)
    return entry['time']

class TimeClockApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Time Clock")
        self.set_border_width(10)
        self.log = load_log()
        self.box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)

        for label, callback in [("Clock In", self.on_clock_in), ("Clock Out", self.on_clock_out), ("Verify Logs", self.on_verify_logs)]:
            button = Gtk.Button(label=label)
            button.connect("clicked", callback)
            self.box.pack_start(button, True, True, 0)

        self.log_view = Gtk.TextView(editable=False, cursor_visible=False)
        self.box.pack_start(Gtk.Label(label="Log:"), True, True, 0)
        self.box.pack_start(self.log_view, True, True, 0)
        self.update_log_view()

    def on_clock_in(self, widget):
        if not self.log or self.log[-1]['type'] == 'out':
            self.log_action(clock(self.log, 'in'), "Clocked in at")
        else:
            self.show_error("You must clock out before clocking in again.")

    def on_clock_out(self, widget):
        if self.log and self.log[-1]['type'] == 'in':
            self.log_action(clock(self.log, 'out'), "Clocked out at")
        else:
            self.show_error("You must clock in before clocking out.")

    def on_verify_logs(self, widget):
        try:
            load_log()
            self.show_message("Log Verification", "All logs are valid.")
        except ValueError as e:
            self.show_message("Log Verification", str(e))

    def log_action(self, time, action):
        self.update_log_view()
        print(f'{action} {time}')

    def update_log_view(self):
        log_buffer = self.log_view.get_buffer()
        log_buffer.set_text('\n'.join([f"{entry['type'].capitalize()} at {entry['time']}" for entry in self.log]))

    def show_message(self, title, message):
        dialog = Gtk.MessageDialog(transient_for=self, flags=0, message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, text=title)
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def show_error(self, message):
        dialog = Gtk.MessageDialog(transient_for=self, flags=0, message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK, text="Error")
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

def main():
    app = TimeClockApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
