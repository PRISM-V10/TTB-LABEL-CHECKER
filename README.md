# TTB Label Checker

A prototype tool to help TTB compliance agents quickly verify alcohol label applications against label images, checking brand name, ABV, and government warning text.

## Setup

1. Clone this repository:
git clone https://github.com/PRISM-V10/TTB-LABEL-CHECKER.git
cd TTB-LABEL-CHECKER

2. Create and activate a virtual environment:
python3 -m venv venv
source venv/bin/activate

3. Install dependencies:
pip install -r requirements.txt

4. Install Tesseract OCR (required for text extraction):
brew install tesseract


## Run

streamlit run app.py


The app will open in your browser at `localhost:8501`.

## Approach, Tools, and Assumptions

**OCR approach:** Text is extracted locally using Tesseract via pytesseract, run twice per image (once normal, once with colors inverted) since label backgrounds vary between light and dark. Whichever pass returns more extracted text is used, which handles both standard labels and light-on-dark designs without needing manual pre-processing.

**Local OCR instead of a cloud vision API:** This was a deliberate choice based on the stakeholder notes, specifically that Treasury's network blocks many outbound domains, and a prior vendor's cloud ML endpoints got blocked by the firewall in production. Running OCR locally avoids that failure mode entirely and keeps the app self-contained.

**Matching logic:** Brand name uses fuzzy matching (85% similarity threshold) so that formatting differences like capitalization don't cause false rejections, per the senior compliance agent's "Stone's Throw" vs "STONE'S THROW" example. The government warning check is intentionally strict rather than fuzzy: it requires the literal phrase "GOVERNMENT WARNING" to appear in all-caps, since the junior agent's example showed a title-case warning should be rejected even if the wording is otherwise correct.

**Assumptions and limitations:**
- Single-image upload only; no support for separate front/back label images in one submission.
- OCR accuracy depends on image quality. Clear, well-lit, front-facing label photos work reliably. Heavily stylized labels (e.g., curved glass, low-contrast foil text) may return little or no extracted text, consistent with the brief's note that poorly-photographed labels may be out of scope for this prototype.
- This is a standalone proof of concept and does not integrate with COLA, per Marcus's guidance that this should remain a separate prototype.
- No PII or label data is stored persistently; all processing happens in-memory during each session.
