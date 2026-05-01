import pandas as pd
import os
import glob

input_folder = r"C:\Users\Raiqis\OneDrive\Desktop\Bank\Raw Data"
output_folder = r"C:\Users\Raiqis\OneDrive\Desktop\Bank\Output"
os.makedirs(output_folder, exist_ok=True)

columns = [
    "CERT", "NAME", "STALP", "STNAME", "CITY", "ASSET", "DEP",
    "NETINC", "ROA", "ROE", "NIM", "NIMY", "EEFFR", "LNLSNET",
    "REPDTE", "NUMEMP", "EQ", "LIAB", "INTINC", "EINTEXP",
    "RBCRWAJ", "DEPUNINS", "COREDEP", "NONII", "NONIX"
]

quarterly_files = glob.glob(os.path.join(input_folder, "20?? Q?.csv"))

frames = []
for file in quarterly_files:
    basename = os.path.basename(file)
    stem = basename.replace(".csv", "")
    year = int(stem[:4])
    quarter = stem[5:]

    df = pd.read_csv(file, low_memory=False)
    df.columns = df.columns.str.strip()

    available = [c for c in columns if c in df.columns]
    df = df[available].copy()

    df["Year"] = year
    df["Quarter"] = quarter

    frames.append(df)

master = pd.concat(frames, ignore_index=True)

for col in ["ASSET", "DEP", "NETINC", "ROA", "ROE", "NIM", "NIMY", "EEFFR",
            "LNLSNET", "NUMEMP", "EQ", "LIAB", "INTINC", "EINTEXP",
            "RBCRWAJ", "DEPUNINS", "COREDEP", "NONII", "NONIX"]:
    master[col] = pd.to_numeric(master[col], errors="coerce")

master = master[master["ASSET"] > 0]
master = master[master["Year"].between(2018, 2025)]

master["Loan to Deposit Ratio"] = (master["LNLSNET"] / master["DEP"]) * 100
master["Uninsured Deposit Pct"] = (master["DEPUNINS"] / master["DEP"]) * 100
master["Equity to Assets"] = (master["EQ"] / master["ASSET"]) * 100

master["Asset Size Category"] = pd.cut(
    master["ASSET"],
    bins=[0, 100000, 1000000, 10000000, float("inf")],
    labels=["Community", "Mid Size", "Regional", "Large"]
)

master.rename(columns={
    "CERT": "Bank ID",
    "NAME": "Bank Name",
    "STALP": "State",
    "STNAME": "State Name",
    "CITY": "City",
    "ASSET": "Total Assets",
    "DEP": "Total Deposits",
    "NETINC": "Net Income",
    "ROA": "Return on Assets",
    "ROE": "Return on Equity",
    "NIM": "Net Interest Margin",
    "NIMY": "Net Interest Margin YTD",
    "EEFFR": "Efficiency Ratio",
    "LNLSNET": "Net Loans",
    "NUMEMP": "Employees",
    "EQ": "Equity",
    "LIAB": "Total Liabilities",
    "INTINC": "Interest Income",
    "EINTEXP": "Interest Expense",
    "RBCRWAJ": "Risk Based Capital Ratio",
    "DEPUNINS": "Uninsured Deposits",
    "COREDEP": "Core Deposits",
    "NONII": "Non Interest Income",
    "NONIX": "Non Interest Expense",
    "REPDTE": "Report Date"
}, inplace=True)

master.to_csv(os.path.join(output_folder, "FDIC Bank Data 2018-2025.csv"), index=False)

yearly = master.groupby("Year").agg({
    "Bank ID": "nunique",
    "Total Assets": "mean",
    "Return on Assets": "mean",
    "Return on Equity": "mean",
    "Net Interest Margin": "mean",
    "Efficiency Ratio": "mean",
    "Risk Based Capital Ratio": "mean",
    "Uninsured Deposit Pct": "mean",
    "Net Income": "sum"
}).reset_index()
yearly.columns = ["Year", "Total Banks", "Avg Assets", "Avg ROA", "Avg ROE",
                  "Avg NIM", "Avg Efficiency Ratio", "Avg Capital Ratio",
                  "Avg Uninsured Deposit Pct", "Total Net Income"]
yearly.to_csv(os.path.join(output_folder, "FDIC Year Over Year Summary.csv"), index=False)

state = master.groupby(["State", "Year"]).agg({
    "Bank ID": "nunique",
    "Return on Assets": "mean",
    "Risk Based Capital Ratio": "mean",
    "Total Assets": "sum",
    "Uninsured Deposit Pct": "mean"
}).reset_index()
state.columns = ["State", "Year", "Total Banks", "Avg ROA", "Avg Capital Ratio",
                 "Total Assets", "Avg Uninsured Deposit Pct"]
state.to_csv(os.path.join(output_folder, "FDIC State Summary.csv"), index=False)

size = master.groupby(["Asset Size Category", "Year"]).agg({
    "Bank ID": "nunique",
    "Return on Assets": "mean",
    "Return on Equity": "mean",
    "Risk Based Capital Ratio": "mean",
    "Efficiency Ratio": "mean",
    "Uninsured Deposit Pct": "mean"
}).reset_index()
size.columns = ["Asset Size Category", "Year", "Total Banks", "Avg ROA", "Avg ROE",
                "Avg Capital Ratio", "Avg Efficiency Ratio", "Avg Uninsured Deposit Pct"]
size.to_csv(os.path.join(output_folder, "FDIC Bank Size Analysis.csv"), index=False)

failures_path = os.path.join(input_folder, "Bank Failures.csv")
if os.path.exists(failures_path):
    failures = pd.read_csv(failures_path, encoding="latin1")
    failures.columns = failures.columns.str.strip()
    failures.to_csv(os.path.join(output_folder, "FDIC Bank Failures.csv"), index=False)
    print("Bank Failures file processed.")

print("Pipeline complete. Output files:")
for f in os.listdir(output_folder):
    print(f" - {f}")
