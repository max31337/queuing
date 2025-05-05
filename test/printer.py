import sys
import os
import time
from unittest.mock import MagicMock

# Add the project root directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import win32print
import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import QueueEntry
from app.schemas import QueueStatus

# ESC/POS commands for text size
ESC = b'\x1b'
GS = b'\x1d'

# Commands for bold/large text
bold_on = ESC + b'\x21\x30'  # Double height & width
bold_off = ESC + b'\x21\x00'  # Normal text

# Optional: Bigger font using GS !
big_on = GS + b'\x21\x11'  # Larger font (height and width)
big_off = GS + b'\x21\x00'  # Back to normal

# Configure these
printer_name = "POS58 Printer(3)"

# Counters
total_counter = 0
inquiry_counter = 0
deposit_counter = 0
withdrawal_counter = 0

# Mock Serial Class
class MockSerial:
    def __init__(self):
        self.input = "INQ"  # Simulated single Arduino input
        self.has_returned = False  # Track if input has been returned

    def readline(self):
        # Simulate reading a single line from the Arduino
        if not self.has_returned:
            self.has_returned = True
            return self.input.encode('utf-8')  # Return as bytes
        else:
            time.sleep(1)  # Simulate waiting for input
            return b''  # No more input

# Replace serial.Serial with MockSerial
ser = MockSerial()
print("Simulating Arduino input...")

# Function to save to the database
def save_to_database(transaction_type: str, trans_no: int, timestamp: str):
    db: Session = SessionLocal()
    try:
        # Get today's date
        today = datetime.date.today()

        # Check the last queue entry for the same type and date
        last_queue = (
            db.query(QueueEntry)
            .filter(QueueEntry.type == transaction_type, QueueEntry.date == today)
            .order_by(QueueEntry.id.desc())
            .first()
        )

        # Reset the queue number if it's a new day
        next_number = (int(last_queue.queue_number[3:]) + 1) if last_queue else 1

        # Generate the formatted queue number
        prefix = {
            "Inquiry": "INQ",
            "Deposit": "DEP",
            "Withdrawal": "WIT"
        }.get(transaction_type, "UNK")  # Default to "UNK" if type is unknown
        formatted_queue_number = f"{prefix}{next_number:03d}"

        # Save to the database
        queue_entry = QueueEntry(
            type=transaction_type,
            queue_number=formatted_queue_number,  # Save the formatted queue number
            status=QueueStatus.waiting,  # Default status
            timestamp=datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S"),
            date=today  # Save today's date
        )
        db.add(queue_entry)
        db.commit()
        db.refresh(queue_entry)
        print(f"Saved to database: {queue_entry}")
        return formatted_queue_number  # Return the formatted queue number
    except Exception as e:
        print(f"Error saving to database: {e}")
    finally:
        db.close()

while True:
    try:
        line = ser.readline().decode('utf-8').strip()
        if line in ["INQ", "DEP", "WDL"]:
            total_counter += 1
            trans_no = 0

            if line == "INQ":
                transaction_type = "Inquiry"
                inquiry_counter += 1
                trans_no = inquiry_counter
            elif line == "DEP":
                transaction_type = "Deposit"
                deposit_counter += 1
                trans_no = deposit_counter
            elif line == "WDL":
                transaction_type = "Withdrawal"
                withdrawal_counter += 1
                trans_no = withdrawal_counter

            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Save to the database
            formatted_queue_number = save_to_database(transaction_type, trans_no, now)

            # Format the receipt text
            receipt_text = (
                bold_on.decode() + "MyBank Express\n" + bold_off.decode() +
                "\n" +
                big_on.decode() + f"{total_counter:03d}\n" + big_off.decode() +
                "\n" +
                f"""Transaction: {transaction_type}
{transaction_type} No.: {trans_no:02d}
Queue Number: {formatted_queue_number}
Date: {now}

Please wait for your turn.
Thank you!
\n\n\n
"""
            )

            print("Printing receipt:")
            print(receipt_text)

            raw_data = receipt_text.encode('utf-8')

            # Send receipt to the printer
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                hJob = win32print.StartDocPrinter(hPrinter, 1, ("Queue Receipt", None, "RAW"))
                win32print.StartPagePrinter(hPrinter)
                win32print.WritePrinter(hPrinter, raw_data)
                win32print.EndPagePrinter(hPrinter)
                win32print.EndDocPrinter(hPrinter)
            finally:
                win32print.ClosePrinter(hPrinter)
    except Exception as e:
        print(f"Error: {e}")