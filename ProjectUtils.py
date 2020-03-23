import pandas as pd
import webarchive, bs4, os
import numpy as np

""" Some classes that are expected from the NoFrills site """
cart_entry_class = 'cart-entry__content cart-entry__content--product-name'
qty_class = 'quantity-selector__quantity__input'
unit_price_class = 'price__value cart-entry__content__price__value'
htm_unit_price_class = 'price price--unit-price cart-entry__content__price cart-entry__content__price--unit-price'
taxes_class = 'tax__button'

# a convenience fnc for grabbing the needed files
get_webarchive_file_names = lambda: [file for file in os.listdir('data/') if
                                     file.endswith('.webarchive') or file.endswith('.htm')]


def ensure_dir(fp):
    """ Simply make sure that a folder rexists """
    if not os.path.exists(fp):
        os.mkdir(fp)


def parse_file_as_df(fp):
    """ Read in a .webarchive or a .htm file as a dataframe """
    ensure_dir('temp/')

    is_htm = fp.endswith('.htm') == True

    if is_htm:
        html_file = load_file(fp)
    else:
        archive = webarchive.open(fp)
        archive.extract("temp/temp.html")
        html_file = load_file('temp/temp.html')

    soup = bs4.BeautifulSoup(html_file, 'html.parser')

    query = {}

    items = soup.find_all('div', {'class': cart_entry_class})
    qtys = soup.find_all('input', {'class': qty_class})
    prices = soup.find_all('span', {'class': unit_price_class})
    if is_htm:
        prices = soup.find_all('span', {'class': htm_unit_price_class})
    taxes = soup.find_all('button', {
        'class': taxes_class})  # saving as a number because I'll only get 1 tax value per person, not per item

    convert_tag_to_float = lambda list_of_tags: [float(tag.text.replace('$', '').replace('ea', '').replace('kg', ''))
                                                 for tag in list_of_tags]
    get_value_as_int_from_tag = lambda list_of_tags: [int(elem['value'].rstrip('kg')) for elem in qtys]
    get_text_from_tag = lambda list_of_tags: [tag.text for tag in list_of_tags]

    query['items'] = get_text_from_tag(items)
    query['qtys'] = get_value_as_int_from_tag(qtys)
    # prices returns all prices so grab every other one to get unit prices
    query['prices'] = convert_tag_to_float(prices[1::2])
    if is_htm:
        query['prices'] = convert_tag_to_float(prices)

    taxes = convert_tag_to_float(taxes)
    return pd.DataFrame(query), taxes[0]  # return the df and the taxes


def load_file(fp):
    """ Simply load a file """
    with open(fp, mode='r+') as file:
        return file.read()


def prepare_csv(data):
    """
    converts a dictionary to a csv file
    dict is expected to be of the form:

    data = {'person':list of str,'data':list of data frames,'taxes':list of floats}

    """
    data_df = pd.DataFrame(data)
    people = data_df['person'].values.tolist()

    total_tag = ' (total)'
    qty_tag = ' (qty)'

    get_df = lambda name: data_df[data_df['person'] == name]['data'].values[
        0]  # 0th index because I'm expecting only 1 value
    get_taxes = lambda name: data_df[data_df['person'] == name]['taxes'].values[0]

    # build a dict to capture important info and rename to look nicer
    csv_data = {'Items': [],
                'Quantity': [],
                'Unit Price': []}

    # TODO: clean this up with list comps
    for person in people:
        df = get_df(person)
        csv_data['Items'] += df['items'].values.tolist()
        csv_data['Unit Price'] += df['prices'].values.tolist()
        csv_data['Quantity'] += df['qtys'].values.tolist()

    # create df and calculate totals
    csv_data = pd.DataFrame(csv_data)
    csv_data = csv_data.groupby('Items').agg({'Quantity': np.sum, 'Unit Price': np.mean})
    csv_data['Total Item Price'] = csv_data['Quantity'] * csv_data['Unit Price']

    # add a column for each person to see how much they are getting of each item
    for person in people:
        total_str = person + total_tag
        qtys_str = person + qty_tag
        df = get_df(person)
        df = df.set_index('items')
        csv_data = csv_data.join(df['qtys'], how='outer').rename(columns={'qtys': qtys_str}).fillna(0)
        csv_data[total_str] = csv_data['Unit Price'] * csv_data[qtys_str]

    csv_data = csv_data.reset_index()  # temorarily move the item index away
    csv_data = csv_data.append(pd.Series(0, index=csv_data.columns),
                               ignore_index=True)  # add a row for taxes for each person
    csv_data = csv_data.append(csv_data.sum(axis=0, numeric_only=True), ignore_index=True)  # add totals row
    csv_data.iloc[-2, 0] = 'Taxes:'  # name the last entry in Items as TOTALS so the row makes sense
    csv_data.iloc[-1, 0] = 'Grand Totals:'  # name the last entry in Items as TOTALS so the row makes sense
    csv_data = csv_data.set_index('index')
    for person in people:
        csv_data.loc['Grand Totals:', person + total_tag] += get_taxes(person)
        csv_data.loc['Taxes:', person + total_tag] += get_taxes(person)

    csv_data.to_csv('Shopping.csv')
    print(csv_data)
