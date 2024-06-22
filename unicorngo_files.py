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
ADIDAS = 6
NEW_BALANCE_ID = 2
NEW_BALANCE_NAME = 'NEW_BALANCE'
NEW_BALANCE_LINK = 'https://unicorngo.ru/men/footwear/sneakers?brands=New%20Balance'

def products_form_categories(base_dir: Path, category: str, link: str):
    for pi in range(1, 2):
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
            print(url)
            product_session = HTMLSession()
            try:
                p = product_session.get(url)
                p.html.render()
            except Exception as e:
                print(e)
                continue
            count += 1
            txt = p.text
            file_name = f'{base_dir}/html/{category}/{url.split("/")[-1].split("?")[0]}.html'
            with open(file_name, 'w', encoding='utf-8') as base_file:
                base_file.write(txt)


def html_checker(html_dir: Path):
    for file in html_dir.glob('*'):
        # file.parent.mkdir(exist_ok=True)
        with open(file.as_posix(), 'r', encoding='utf-8') as file_:
             res = file_.read()
        yield res


def xml_creator(base_dir: Path, category_name: str):
    dt_start = str(datetime.now()).replace(':', '_')
    result_filename = base_dir / f'results/{category_name}/{dt_start}.xml'
    with open(result_filename, 'w', encoding='utf-8') as xml_file:
        xml_file.write(header)
    for file in (base_dir / 'xml' / category_name).glob('*'):
        # print('=================')
        # print(file)
        file.parent.mkdir(exist_ok=True)
        with open(file.as_posix(), 'r', encoding='utf-8') as file_:
             res = file_.read()
        print(res)
        with open(result_filename, 'a+', encoding='utf-8') as xml_file:
            xml_file.write(res)
    with open(result_filename, 'a+', encoding='utf-8') as xml_file:
        xml_file.write(header)


def start(category_id: int, category_name: str, base_dir: Path = test_dir):
    dt_start = str(datetime.now()).replace(':', '_')
    result_filename = base_dir / f'results/{category_name}/{dt_start}.xml'
    # result_filename.parent.mkdir(exist_ok=True)
    # with open(result_filename, 'w', encoding='utf-8') as xml_file:
    #     xml_file.write(header)
    for page in html_checker(base_dir / 'html' / category_name):
        p = HTML(html=page, url='https://unicorngo.ru')
        name = p.find('h1', first=True).text
        products_images = []
        description_end = p.search('product-description_content__{}"')
        if description_end:
            description = p.find(f'.product-description_content__{description_end[0]}', first=True).text
            description = re.sub(' +', ' ', description)
        else:
            description = 'Скоро здесь появится описание'
        products_images = [f'<picture>{o.attrs.get("content").replace("/origin-img/", "/cut-img/")}</picture>' for o in p.find('meta[property="og:image"]', clean=True)[::-1]]
        # print(type(p.find('meta[property="og:image"]', clean=True)[::-1]))
        # for o in :
        #     img =
        #     # print(type(img))
        #     # if len(products_images) == 5 or img == '/android-chrome-192x192.webp':
        #     #     break
        #     # if cimg != '/android-chrome-192x192.webp':
        #     products_images.append(
        #         f'<picture>{img.replace("/origin-img/", "/cut-img/")}</picture>')
        # print(products_images)
        # print('<picture>/android-chrome-192x192.webp</picture>' in images)
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
        all_info = []
        for size, sku in sizes_sku:
            str_ = r'\"skuId\":' + str(sku) + r',\"price\":{},'
            all_info.append((sku, size, us.search(str_).fixed[0]))
        first_sku = all_info[0][0]
        # with open(f'{base_dir}/xml/{first_sku}.xml', 'w', encoding='utf-8') as empty_file:
        #     empty_file.write('')
        xml_filename = base_dir / 'xml' / category_name / f'{first_sku}.xml'
        try:
            # xml_filename.touch()
            with open(xml_filename, 'r+', encoding='utf-8') as file:
                for sku, size, price in all_info:

                    try:
                        if sku == first_sku:
                            file.write(f'<offer id="{sku}-0" available="true" group_id="{first_sku}">')
                        else:
                            file.write(f'<offer id="{first_sku}-{sku}" group_id="{first_sku}">')
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
                # content = file.read()
                # with open(f'{base_dir}/xml/{category_name}/{first_sku}.xml', 'r', encoding='utf-8') as file_r:
                #     try:
                #         content = file_r.read()
                #         # print(products_images)
                #     except Exception as e:
                #         print(e)
                #         print(sku, size, price)
                #         print(products_images)
                #         print(f'Ошибка записи файла: {name}')
                # with open(result_filename, 'a', encoding='utf-8') as xml_file:
                #     xml_file.write(content)
                # print(f'{name} готово')
        except Exception as e:
            print(e)
            print(f'Не удалось записать файл: {first_sku}')
# print(f'страница {pi}')

    # with open(result_filename, 'a', encoding='utf-8') as xml_file:
    #     xml_file.write(footer)

# print('Работа скрипта:')
# print(datetime.now()-start_time)
# products_form_categories(test_dir, 'NEW_BALANCE', NEW_BALANCE_LINK)
start(NEW_BALANCE_ID, NEW_BALANCE_NAME)
xml_creator(base_dir=test_dir, category_name=NEW_BALANCE_NAME)
t = 9*9**9
# print(type(next(html_checker(Path('test/html/NEW_BALANCE/')))))
# with open(f'all_goods2/{first_sku}.xml', 'w', encoding='utf-8') as file: