import streamlit as st
import pandas as pd

st.set_page_config(page_title="Product Sheet Comparator", layout="wide")
st.title("Product Sheet Comparator (Drag & Drop)")

st.write("""
- **Upload the most recent product table as "New Table" and your current catalog as "Old Table".**
- **Product ID** (Column A) is used for comparison.
- Results:  
    - **Add:** Products in New but not in Old  
    - **Delete:** Products in Old but not in New  
    - **Price Change:** Products in both but with different price
    - **Formulas for columns N/O**: Adds '=L2.url' and '=M2.url'
""")

uploaded_new = st.file_uploader("Upload New Table (CSV)", type="csv", key="new")
uploaded_old = st.file_uploader("Upload Old Table (CSV)", type="csv", key="old")

if uploaded_new and uploaded_old:
    new_df = pd.read_csv(uploaded_new, dtype=str).fillna("")
    old_df = pd.read_csv(uploaded_old, dtype=str).fillna("")

    # Trim both to rows with valid Product IDs (nonempty col A)
    new_df = new_df[new_df.iloc[:, 0].str.strip() != ""]
    old_df = old_df[old_df.iloc[:, 0].str.strip() != ""]

    # Set up key columns
    new_df = new_df.reset_index(drop=True)
    old_df = old_df.reset_index(drop=True)
    new_ids = set(new_df.iloc[:, 0])
    old_ids = set(old_df.iloc[:, 0])

    # Products to Add
    to_add = new_df[new_df.iloc[:, 0].isin(new_ids - old_ids)]
    # Products to Delete
    to_delete = old_df[old_df.iloc[:, 0].isin(old_ids - new_ids)]
    # Products in Both
    common = new_df[new_df.iloc[:, 0].isin(new_ids & old_ids)]

    # Find price changes (if 'Price' column present, case-insensitive)
    price_col_new = next((c for c in new_df.columns if 'price' in c.lower()), None)
    price_col_old = next((c for c in old_df.columns if 'price' in c.lower()), None)
    price_changes = pd.DataFrame()
    if price_col_new and price_col_old:
        merged = pd.merge(new_df, old_df, left_on=new_df.columns[0], right_on=old_df.columns[0], suffixes=('_new', '_old'))
        price_changes = merged[merged[price_col_new] != merged[price_col_old]]

    # Output Formulas for N/O if desired
    output_df = new_df.copy()
    last_row = len(output_df)
    output_df["N_formula"] = [f"=L{i+2}.url" for i in range(last_row)]
    output_df["O_formula"] = [f"=M{i+2}.url" for i in range(last_row)]

    st.subheader("Products to ADD")
    if len(to_add):
        st.dataframe(to_add[[to_add.columns[0], to_add.columns[1]]], use_container_width=True)
    else:
        st.success("No new products to add.")

    st.subheader("Products to DELETE")
    if len(to_delete):
        st.dataframe(to_delete[[to_delete.columns[0], to_delete.columns[1]]], use_container_width=True)
    else:
        st.success("No products to delete.")

    if not price_changes.empty:
        st.subheader("Products with Price Change")
        display_cols = [merged.columns[0], 'Strain Name_new' if 'Strain Name_new' in merged.columns else merged.columns[1], price_col_new, price_col_old]
        st.dataframe(price_changes[display_cols], use_container_width=True)

    st.subheader("Download Output Table (with formulas in N/O)")
    output_download = output_df.copy()
    # Move formulas to columns N/O if those columns exist
    cols = list(output_download.columns)
    if len(cols) >= 15:
        output_download.iloc[:, 13] = output_download["N_formula"]
        output_download.iloc[:, 14] = output_download["O_formula"]
    else:
        # Insert at end if less columns
        output_download["N"] = output_download["N_formula"]
        output_download["O"] = output_download["O_formula"]
    # Remove temp columns
    output_download = output_download.drop(columns=["N_formula", "O_formula"])
    st.download_button(
        "Download Modified Table",
        data=output_download.to_csv(index=False),
        file_name="output_with_formulas.csv",
        mime="text/csv"
    )

    st.caption("All operations above disregard rows below 'FOR COA and MEDIA REFERENCE ONLY' if you pre-trim your uploads.")
else:
    st.info("Please upload both new and old product CSV files to begin.
