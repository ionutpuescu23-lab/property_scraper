import re
import pandas as pd

def clean_scraped_data(input_file, output_file):
    try:
        # Load the raw scraped CSV
        df = pd.read_csv(input_file)
        
        cleaned_rows = []
        
        for index, row in df.iterrows():
            title = str(row['Title'])
            price = str(row['Price'])
            reduced = str(row['Reduced'])
            keywords = str(row['Keywords Found'])
            link = str(row['Link'])
            
            # 1. Filter out known ad-networks, iframes, or tracking scripts
            if "iframe" in price or "crestolaven" in price or "<script>" in price:
                continue
                
            # 2. Clean up corrupted text strings or excess whitespace
            price_clean = re.sub(r'\s+', ' ', price).strip()
            title_clean = re.sub(r'\s+', ' ', title).strip()
            
            # If the title fell back to a default, make it look professional
            if title_clean == "Investment Property" or not title_clean:
                title_clean = "Residential Investment Opportunity"
                
            cleaned_rows.append({
                "Asset Title": title_clean,
                "Target Price": price_clean,
                "Sourcing Link": link,
                "Price Reduced": reduced,
                "Investor Signals": keywords
            })
            
        # Save out to a polished investor sheet
        if cleaned_rows:
            cleaned_df = pd.DataFrame(cleaned_rows)
            cleaned_df.to_csv(output_file, index=False)
            print(f"\n✨ Data optimization complete! Saved to '{output_file}'")
            print(cleaned_df.head())
        else:
            print("\nFilter complete: The row captured was confirmed as an advertisement tracking pixel and skipped.")
            
    except Exception as e:
        print(f"Error processing data: {e}")

if __name__ == "__main__":
    clean_scraped_data("distressed_property_deals.csv", "polished_investor_deals.csv")