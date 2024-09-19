from flask import Flask, render_template, send_file
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO

app = Flask(__name__)

base_url = 'https://capellisport.com/collections/womens-tops'

def scrape_products():
    all_products = []
    page_number = 1    

    while True:
        page_url = f"{base_url}?page={page_number}"
        response = requests.get(page_url)

        if response.status_code != 200:
            print(f"Failed to retrieve page {page_number}. Status code: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, 'lxml')
        product_titles = [title.get_text(strip=True) for title in soup.find_all('div', class_='grid-product__title')]
        product_prices = [price.get_text(strip=True) for price in soup.find_all('div', class_='grid-product__price')]

        if not product_titles:
            print("No more products found.")
            break

        for title, price in zip(product_titles, product_prices):
            all_products.append({'title': title, 'price': price})

        next_page = soup.find('span', class_='next')
        if not next_page:
            break

        page_number += 1

    return all_products

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scrape')
def scrape():
    products = scrape_products()
    enumerated_products = [{'index': idx+1, 'title': p['title'], 'price': p['price']} for idx, p in enumerate(products)]
    return render_template('scrape.html', products=enumerated_products)

@app.route('/export')
def export():
    products = scrape_products()
    df = pd.DataFrame(products)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Products')

    output.seek(0)

    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     download_name='products.xlsx', as_attachment=True)

if __name__ == '__main__':
    app.run(port=3000, debug=True)