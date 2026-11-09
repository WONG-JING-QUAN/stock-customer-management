# Stock & Customer Management System

A Streamlit web app for managing stock, customers and orders for a small trading business, built on a local SQLite database. The app runs under the name **WPC Plastic Management System**.

> The data in this repository (`inventory_system.db` and the backup file) is sample data for demonstration only.

## Features

| Page | What it does |
| --- | --- |
| Executive Dashboard | Key figures, including a low-stock count, with customer analysis and a product check |
| Order | Records new orders and stock adjustments, with quantities entered in packs and converted to units |
| Customer Database | Adds, edits and deletes customers |
| Inventory Database | Adds, edits and deletes products, with pack sizes, unit types and a low-stock alerts tab |
| Recycle Bin | Restores deleted sales, customers and products |

The sidebar also exports customers and inventory to CSV and creates a timestamped backup of the database in one click.

## Built with

Python, Streamlit, SQLite, pandas and Plotly.

## Run it locally

```
pip install streamlit pandas plotly
streamlit run app.py
```

On Windows you can double-click `run_app.bat` instead.

## License

© 2026 Wong Jing Quan. All Rights Reserved.
This project is shared for portfolio demonstration and educational purposes only. It may not be copied, modified, or used for any commercial purposes without explicit permission.
