import time, os, json, hashlib, gi, csv
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from datetime import datetime, timedelta

LOG_FILE = 'time_log.json'

def calculate_hash(entry, prev_hash=''):
    entry = {k: v for k, v in entry.items() if k != 'hash'}
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

def round_to_quarter_hour(dt):
    new_minute = (dt.minute // 15 + (1 if dt.minute % 15 >= 8 else 0)) * 15
    return dt.replace(minute=new_minute, second=0) if new_minute < 60 else (dt.replace(minute=0, second=0) + timedelta(hours=1))

def export_to_csv(log):
    with open('time_log.csv', 'w', newline='') as csvfile:
        fieldnames = ['Date', 'Day of Week', 'Start Time', 'End Time', 'Rounded Start Time', 'Rounded End Time', 'Time Difference']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for i in range(0, len(log), 2):
            if log[i]['type'] == 'in' and (i + 1 < len(log) and log[i + 1]['type'] == 'out'):
                start_time = datetime.strptime(log[i]['time'], '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(log[i + 1]['time'], '%Y-%m-%d %H:%M:%S')
                rounded_start_time = round_to_quarter_hour(start_time)
                rounded_end_time = round_to_quarter_hour(end_time)
                time_difference = (rounded_end_time - end_time) - (rounded_start_time - start_time)
                writer.writerow({
                    'Date': start_time.strftime('%Y-%m-%d'),
                    'Day of Week': start_time.strftime('%A'),
                    'Start Time': start_time.strftime('%H:%M:%S'),
                    'End Time': end_time.strftime('%H:%M:%S'),
                    'Rounded Start Time': rounded_start_time.strftime('%H:%M:%S'),
                    'Rounded End Time': rounded_end_time.strftime('%H:%M:%S'),
                    'Time Difference': str(time_difference)
                })

class TimeClockApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Time Clock")
        self.set_border_width(10)
        self.log = load_log()
        self.box = Gtk.Box(spacing=6, orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)

        for label, callback in [("Clock In", self.on_clock_in), ("Clock Out", self.on_clock_out), ("Verify Logs", self.on_verify_logs), ("Export to CSV", self.on_export_to_csv)]:
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
            self.show_message("Error", "You must clock out before clocking in again.")

    def on_clock_out(self, widget):
        if self.log and self.log[-1]['type'] == 'in':
            self.log_action(clock(self.log, 'out'), "Clocked out at")
        else:
            self.show_message("Error", "You must clock in before clocking out.")

    def on_verify_logs(self, widget):
        try:
            load_log()
            self.show_message("Log Verification", "All logs are valid.")
        except ValueError as e:
            self.show_message("Log Verification", str(e))

    def on_export_to_csv(self, widget):
        export_to_csv(self.log)
        self.show_message("Export to CSV", "Log has been exported to time_log.csv")

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

def main():
    app = TimeClockApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == '__main__':
    main()
