import streamlit as st
from PIL import Image, ImageOps
import pytesseract
from rapidfuzz import fuzz
import pandas as pd

GOVERNMENT_WARNING = (
    "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not "
    "drink alcoholic beverages during pregnancy because of the risk of birth defects. "
    "(2) Consumption of alcoholic beverages impairs your ability to drive a car or "
    "operate machinery, and may cause health problems."
)

def extract_text(image):
    gray = ImageOps.grayscale(image)
    text_normal = pytesseract.image_to_string(gray)
    text_inverted = pytesseract.image_to_string(ImageOps.invert(gray))
    if len(text_inverted.strip()) > len(text_normal.strip()):
        return text_inverted
    return text_normal

def check_brand(extracted_text, app_brand):
    if not app_brand:
        return "SKIPPED", None
    score = fuzz.partial_ratio(app_brand.lower(), extracted_text.lower())
    return ("MATCH" if score >= 85 else "REVIEW"), score

def check_abv(extracted_text, app_abv):
    if not app_abv:
        return "SKIPPED"
    abv_clean = str(app_abv).replace(" ", "").lower()
    text_clean = extracted_text.replace(" ", "").lower()
    return "MATCH" if abv_clean in text_clean else "REVIEW"

def check_warning(extracted_text):
    norm_extracted = " ".join(extracted_text.split())
    norm_expected = " ".join(GOVERNMENT_WARNING.split())
    wording_score = fuzz.partial_ratio(norm_expected.lower(), norm_extracted.lower())
    if wording_score < 90:
        return "REJECT"
    elif "GOVERNMENT WARNING" in norm_extracted:
        return "MATCH"
    else:
        return "REJECT"

def overall_verdict(brand_status, abv_status, warning_status):
    statuses = [brand_status, abv_status, warning_status]
    if "REJECT" in statuses:
                return "REJECT"
    if "REVIEW" in statuses:
        return "REVIEW"
    return "PASS"

st.title("TTB Label Checker")

tab1, tab2 = st.tabs(["Single Label", "Batch Upload"])

with tab1:
    st.write("Upload a label image and enter the application data to verify a match.")
    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader("Label image", type=["png", "jpg", "jpeg"], key="single_image")
        if uploaded_file is not None:
            image = ImageOps.exif_transpose(Image.open(uploaded_file)).convert("RGB")
            st.image(image, caption="Uploaded label", use_container_width=True)

    with col2:
        st.subheader("Application data")
        app_brand = st.text_input("Brand name (from application)")
        app_abv = st.text_input("Alcohol content / ABV (from application)")

    if uploaded_file is not None:
        extracted_text = extract_text(image)

        with st.expander("Show raw extracted text"):
            st.text(extracted_text)

        if st.button("Verify label"):
            st.subheader("Results")
            brand_status, brand_score = check_brand(extracted_text, app_brand)
            abv_status = check_abv(extracted_text, app_abv)
            warning_status = check_warning(extracted_text)

            if brand_status == "MATCH":
                st.success(f"Brand name: MATCH — confidence {brand_score}")
            elif brand_status == "REVIEW":
                st.warning(f"Brand name: REVIEW — '{app_brand}' not confidently found (confidence {brand_score})")

            if abv_status == "MATCH":
                st.success(f"ABV: MATCH — {app_abv}")
            elif abv_status == "REVIEW":
                st.warning(f"ABV: REVIEW — '{app_abv}' not found on label")

            if warning_status == "MATCH":
                st.success("Government warning: MATCH")
            else:
                st.error("Government warning: REJECT")

with tab2:
    st.write("Upload multiple label images plus a CSV of application data to verify a batch.")
    st.caption("CSV columns required: filename, brand_name, abv (filename must match the uploaded image's filename, e.g. label1.jpg)")

    csv_file = st.file_uploader("Application data CSV", type=["csv"], key="batch_csv")
    image_files = st.file_uploader(
        "Label images", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="batch_images"
    )

    if csv_file is not None and image_files:
        df = pd.read_csv(csv_file)
        images_by_name = {f.name: f for f in image_files}

        if st.button("Verify batch"):
            results = []
            progress = st.progress(0)

            for i, row in df.iterrows():
                filename = row["filename"]
                brand = row.get("brand_name", "")
                abv = row.get("abv", "")

                if filename not in images_by_name:
                    results.append({
                        "filename": filename, "brand_name": brand, "abv": abv,
                        "verdict": "ERROR", "notes": "No matching image uploaded"
                    })
                    continue

                img_file = images_by_name[filename]
                image = ImageOps.exif_transpose(Image.open(img_file)).convert("RGB")
                extracted_text = extract_text(image)

                brand_status, brand_score = check_brand(extracted_text, brand)
                abv_status = check_abv(extracted_text, abv)
                warning_status = check_warning(extracted_text)
                verdict = overall_verdict(brand_status, abv_status, warning_status)

                results.append({
                    "filename": filename,
                    "brand_name": brand,
                    "brand_match": brand_status,
                    "abv": abv,
                    "abv_match": abv_status,
                    "warning": warning_status,
                    "verdict": verdict,
                })
                progress.progress((i + 1) / len(df))

            results_df = pd.DataFrame(results)
            st.subheader("Batch results")
            st.dataframe(results_df, use_container_width=True)

            review_count = (results_df["verdict"] == "REVIEW").sum()
            reject_count = (results_df["verdict"] == "REJECT").sum()
            st.caption(f"{review_count} need review, {reject_count} rejected, out of {len(results_df)} total")