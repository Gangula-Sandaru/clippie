import unittest
from unittest.mock import patch
from clipboard.monitor import ClipboardMonitor
from utils.notifier import notifier


class TestMonitorSensitiveFlow(unittest.TestCase):

    def test_sensitive_detection_triggers_notification_and_skips_db(self):
        received_notifications = []

        def on_notify(cat, msg):
            received_notifications.append((cat, msg))

        notifier.sensitive_detected.connect(on_notify)

        sensitive_text = "My secret password is: password=SuperSecretPassword123"

        with patch("clipboard.monitor.get_clipboard_sequence", side_effect=[100, 101, 101]), \
             patch("pyperclip.paste", return_value=sensitive_text), \
             patch("clipboard.monitor.ImageGrab.grabclipboard", return_value=None), \
             patch("clipboard.monitor.add_item") as mock_add_item, \
             patch("time.sleep", side_effect=[None, StopIteration]):

            monitor = ClipboardMonitor()
            try:
                monitor.run()
            except StopIteration:
                pass

        # Verify add_item was NEVER called for sensitive text
        mock_add_item.assert_not_called()

        # Verify notification signal was emitted
        self.assertGreaterEqual(len(received_notifications), 1)
        cat, msg = received_notifications[0]
        self.assertEqual(cat, "Password / Credential")
        self.assertIn("Password / Credential", msg)

    def test_normal_text_saves_to_db_and_does_not_notify(self):
        received_notifications = []

        def on_notify(cat, msg):
            received_notifications.append((cat, msg))

        notifier.sensitive_detected.connect(on_notify)

        normal_text = "Just a friendly normal note to copy."

        with patch("clipboard.monitor.get_clipboard_sequence", side_effect=[100, 101, 101]), \
             patch("pyperclip.paste", return_value=normal_text), \
             patch("clipboard.monitor.ImageGrab.grabclipboard", return_value=None), \
             patch("clipboard.monitor.add_item") as mock_add_item, \
             patch("time.sleep", side_effect=[None, StopIteration]):

            monitor = ClipboardMonitor()
            try:
                monitor.run()
            except StopIteration:
                pass

        # Verify add_item was called
        mock_add_item.assert_called_once_with(normal_text)

        # Verify NO sensitive notification was emitted
        self.assertEqual(len(received_notifications), 0)

    def test_repeated_copy_of_same_sensitive_item_notifies_each_time(self):
        """User copies the exact same sensitive info again — notification must show every single time."""
        received_notifications = []

        def on_notify(cat, msg):
            received_notifications.append((cat, msg))

        notifier.sensitive_detected.connect(on_notify)

        same_sensitive_text = "Card: 4532 0151 1283 0366"
        # Init gets 100. Loop 1 gets 101. Loop 2 gets 102.
        sequence_numbers = [100, 101, 102, 102]

        with patch("clipboard.monitor.get_clipboard_sequence", side_effect=sequence_numbers), \
             patch("pyperclip.paste", return_value=same_sensitive_text), \
             patch("clipboard.monitor.ImageGrab.grabclipboard", return_value=None), \
             patch("clipboard.monitor.add_item") as mock_add_item, \
             patch("time.sleep", side_effect=[None, None, StopIteration]):

            monitor = ClipboardMonitor()
            try:
                monitor.run()
            except StopIteration:
                pass

        # Verify add_item was NEVER called
        mock_add_item.assert_not_called()

        # Verify notification was emitted for BOTH copies of the same card number!
        self.assertEqual(len(received_notifications), 2)
        self.assertEqual(received_notifications[0][0], "Credit Card Number")
        self.assertEqual(received_notifications[1][0], "Credit Card Number")


if __name__ == "__main__":
    unittest.main()
