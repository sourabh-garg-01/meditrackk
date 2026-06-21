# Meditrackk

Meditrackk is a local-first medical timeline app for organizing healthcare
documents by date. Upload bills, prescriptions, reports, invoices, OPD slips,
or discharge summaries, and the app extracts useful metadata before adding the
document to a chronological timeline.

## MVP Features

- Upload JPG, JPEG, PNG, WEBP, and PDF files
- Run OCR locally with PaddleOCR
- Pre-process images with OpenCV before OCR
- Extract event date, hospital/lab name, patient name, amount, category, and title
- Fall back to upload date when a document date cannot be found
- Store everything locally in SQLite
- Edit extracted metadata before saving
- View timeline events sorted by event date
- Open the original uploaded document from the timeline

## Tech Stack

- Streamlit
- SQLite
- PaddleOCR
- OpenCV
- Pillow
- dateparser

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure

```text
meditrackk/
  app.py
  requirements.txt
  database/
  uploads/
  thumbnails/
  services/
  db/
  models/
  pages/
  utils/
```

## Local Storage

The app stores data only on your machine:

- Uploaded documents: `uploads/`
- Generated thumbnails: `thumbnails/`
- SQLite database: `database/meditrackk.db`

No authentication, cloud storage, paid APIs, or OpenAI dependency are used.
