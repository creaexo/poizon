import re
from datetime import datetime
from pathlib import Path

from requests_html import HTML, HTMLSession

start_time = datetime.now()

header = '<?xml version="1.0" encoding="utf-8"?><yml_catalog date="2021-04-01 12:20"><shop><offers><categories><category id="2">New Balance</category></categories>'
footer = '</offers></shop></yml_catalog>'
unicorngo_html_dir = Path('unicorngo/html')
test_html_dir = Path('test/html')
test_dir = Path('test/')
ADIDAS_ID = 6
ADIDAS_NAME = 'ADIDAS'
ADIDAS_LINK = 'https://unicorngo.ru/men/footwear/sneakers?brands=adidas'
NEW_BALANCE_ID = 2
NEW_BALANCE_NAME = 'NEW_BALANCE'
NEW_BALANCE_LINK = 'https://unicorngo.ru/men/footwear/sneakers?brands=New%20Balance'

def products_form_categories(base_dir: Path, category: str, link: str, s_page: int=1, e_page: int=1):
    for pi in range(s_page, e_page + 1):
        session = HTMLSession()
        r = session.get(f'{link}&page={pi}&sort=by-relevance')
        r.html.render()
        with open(f'{base_dir}/cat/{category}{pi}.html', 'w', encoding='utf-8') as cat_file:
            cat_file.write(r.text)
        with open(f'{base_dir}/cat/{category}{pi}.html', 'r', encoding='utf-8') as cat_file:
            page = cat_file.read()
        r = HTML(html=page, url='https://unicorngo.ru')
        class_end = r.search('product-card_product_card__{} ')[0]
        class_name = f'product-card_product_card__{class_end}'
        count = 0
        all_products = r.find(f'.{class_name}')

        for i in all_products:
            url: str = i.absolute_links.pop()
            # print(url)
            product_session = HTMLSession()
            try:
                p = product_session.get(url)
                p.html.render()
            except Exception as e:
                print(e)
                continue
            count += 1
            txt = p.text
            file_name = base_dir / f'html/{category}/{url.split("/")[-1].split("?")[0]}.html'
            file_name.parent.mkdir(exist_ok=True)
            with open(file_name, 'w', encoding='utf-8') as base_file:
                base_file.write(txt)


def html_checker(html_dir: Path):
    for file in html_dir.glob('*'):
        # file.parent.mkdir(exist_ok=True)
        with open(file.as_posix(), 'r', encoding='utf-8') as file_:
             res = file_.read()
        yield res


def xml_creator(base_dir: Path, category_name: str, category_id: int):
    header = f'<?xml version="1.0" encoding="utf-8"?><yml_catalog date="2021-04-01 12:20"><shop><offers><categories><category id="{category_id}">{category_name}</category></categories>'
    footer = '</offers></shop></yml_catalog>'
    dt_start = str(datetime.now()).replace(':', '_')
    result_filename = base_dir / 'results' / category_name / f'{dt_start}.xml'
    result_filename.parent.mkdir(exist_ok=True)
    with open(result_filename, 'w', encoding='utf-8') as xml_file:
        xml_file.write(header)
    for file in (base_dir / 'xml' / category_name).glob('*'):
        file.parent.mkdir(exist_ok=True)
        with open(file.as_posix(), 'r', encoding='utf-8') as file_:
             res = file_.read()
        # print(res)
        with open(result_filename, 'a+', encoding='utf-8') as xml_file:
            xml_file.write(res)
    with open(result_filename, 'a+', encoding='utf-8') as xml_file:
        xml_file.write(footer)


def start(category_id: int, category_name: str, base_dir: Path = test_dir):
    dt_start = str(datetime.now()).replace(':', '_')
    for page in html_checker(base_dir / 'html' / category_name):
        p = HTML(html=page, url='https://unicorngo.ru')
        name = p.find('h1', first=True).text
        description_end = p.search('product-description_content__{}"')
        if description_end:
            description = p.find(f'.product-description_content__{description_end[0]}', first=True).text
            description = re.sub(' +', ' ', description)
        else:
            description = 'Скоро здесь появится описание'
        products_images = [f'<picture>{o.attrs.get("content").replace("/origin-img/", "/cut-img/")}</picture>' for o in p.find('meta[property="og:image"]', clean=True)[::-1][:5] if o.attrs.get("content") != '/android-chrome-192x192.webp']
        # print(products_images)
        class_end = p.search('product-size_list__{}"')[0]
        sizes = p.find(f'.product-size_list__{class_end}', first=True)

        sizes_sku = []
        for i in sizes.find('a'):
            sku: str = i.attrs.get('href').split('=')[-1]
            sizes_sku.append((i.text, sku))
        scripts = [i for i in p.find('script') if i.attrs == {}]
        useful_script = ''
        skus = [i[1] for i in sizes_sku]
        str_ = r'\"skuId\":' + skus[0]
        for s in scripts[::-1]:
            if str_ in s.text and 'price' in s.text:
                useful_script = s.text
                break

        us = HTML(html=useful_script)
        ordinary_info = []
        f_size_info = []
        for size, sku in sizes_sku:
            str_ = r'\"skuId\":' + str(sku) + r',\"price\":{},'
            price: str = us.search(str_).fixed[0]
            if size.isdigit():
                ordinary_info.append((sku, size, price))
            else:
                f_size_info.append((sku, size, price))
        xml_filename = ''
        ordinary_info.sort(key=lambda a: int(a[2]))
        f_size_info.sort(key=lambda b: int(b[2]))
        if len(f_size_info):
            first_sku_f = f_size_info[0][0]
            xml_filename = base_dir / 'xml' / category_name / f'{first_sku_f}.xml'
        if len(ordinary_info):
            first_sku_o = ordinary_info[0][0]
            xml_filename = base_dir / 'xml' / category_name / f'{first_sku_o}.xml'

        try:
            xml_filename.parent.mkdir(exist_ok=True)
            with open(xml_filename, 'w', encoding='utf-8') as file:
                for sku, size, price in ordinary_info:
                    try:
                        if sku == first_sku_o:
                            file.write(f'<offer id="{sku}-0" available="true" group_id="{first_sku_o}">')
                        else:
                            file.write(f'<offer id="{first_sku_o}-{sku}" group_id="{first_sku_o}">')
                        file.write(f'<categoryId>{category_id}</categoryId>')
                        file.write(f'<price>{int(int(price)*0.9)}</price>')
                        file.write('<currencyId>RUB</currencyId>')
                        file.write(f'<name>{name}</name>')
                        file.write(f'<description>{description}</description>')

                        file.write(f'<param name="Размер">{size}</param>')
                        for img_ in products_images:
                            file.write(img_)
                    except Exception:
                        print(sku, size, price)
                    finally:
                        file.write(f'</offer>')
                for sku, size, price in f_size_info:
                    try:
                        if sku == first_sku_f:
                            file.write(f'<offer id="{sku}-0" available="true" group_id="{first_sku_f}">')
                        else:
                            file.write(f'<offer id="{first_sku_f}-{sku}" group_id="{first_sku_f}">')
                        file.write(f'<categoryId>{category_id}</categoryId>')
                        file.write(f'<price>{int(int(price) * 0.9)}</price>')
                        file.write('<currencyId>RUB</currencyId>')
                        file.write(f'<name>{name}</name>')
                        file.write(f'<description>{description}</description>')

                        file.write(f'<param name="Размер (дробный)">{size}</param>')
                        for img_ in products_images:
                            file.write(img_)
                    except Exception:
                        print(sku, size, price)
                    finally:
                        file.write(f'</offer>')
        except Exception as e:
            print(e)
            print(f'Не удалось записать файл: {xml_filename}')

# products_form_categories(
#     base_dir=test_dir, category=ADIDAS_NAME, link=ADIDAS_LINK, s_page=4, e_page=7
# )
start(ADIDAS_ID, ADIDAS_NAME)
xml_creator(base_dir=test_dir, category_name=ADIDAS_NAME, category_id=ADIDAS_ID)
