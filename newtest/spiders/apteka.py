import scrapy
import re
from datetime import datetime


class AptekaSpider(scrapy.Spider):
    name = "apteka"
    allowed_domains = ["apteka-ot-sklada.ru"]
    start_urls = ["https://apteka-ot-sklada.ru/catalog"]

    def start_requests(self):
        coocies = {'view': 'cells', '_userGUID': '0', 'city': '92'}
        for num in range(0, 120, 12):
            # я здесть не стал делать как в задании добавить в список ссылки категории,тут просто 10 страниц пустил
            url = f'https://apteka-ot-sklada.ru/catalog?start={num}'
            yield scrapy.Request(url, cookies=coocies, callback=self.parse_pages)

    def parse_pages(self, response):
        coocies = {'view': 'cells', '_userGUID': '0', 'city': '92'}
        response_text = 'div.goods-card__name.text.text_size_default.text_weight_medium > a::attr("href")'
        for i in response.css(response_text).extract():
            url = response.urljoin(i)
            yield scrapy.Request(url, cookies=coocies, callback=self.parse)

    def parse(self, response, **kwargs):
        # теги для нахождения нужных html заголовок
        response_list = [
            '//*[@id="__layout"]/div/div[2]/main/section[1]/div/div[2]/div[1]/div[1]/img/@src',
            '//*[@id="__layout"]/div/div[2]/main/section[1]/div/aside/div/div[1]/ul/li[1]/a/span/text()',
            'div.goods-offer-panel > div:nth-child(1) > div.goods-offer-panel__price',
            '//*[@id="__layout"]/div/div[2]/main/header/div[2]/div[2]/ul/li/span/text()',
            'div.ui-breadcrumbs.text.text_weight_medium.page-header__breadcrumbs.text.text_size_caption > ul',
            'div.goods-gallery__sidebar > ul',
            '//*[@id="description"]/div',
            '//*[@id="__layout"]/div/div[2]/main/header/h1/span/text()',
            '//*[@id="__layout"]/div/div[2]/main/header/h1/span/text()',
        ]

        tags_list = list()
        section_list = list()
        count = list()
        dis_price = None
        price = None
        sale_tag = None
        in_stock = False
        code = response.url.split('_')
        main_img = response.xpath(response_list[0]).get()
        more_img = list()

        # проверка товара в налаичи либо
        if response.xpath(response_list[1]).get():
            in_stock = True

        # проверка на скидку,если нет просто цена,если есть уже идет вычисление %
        for dis_price_tex in response.css(response_list[2]).extract():
            count = [x for x in re.sub(r"<[^>]+>", "", dis_price_tex, flags=re.S).replace('\n', '').split('  ') if x != '' and x != ' ']
        if len(count) == 1:
            price = count[0]
        else:
            dis_price = count[0]
            price = count[1]
            new_price = dis_price.replace('₽', '')
            old_price = price.replace('₽', '')
            sale_tag = f'{round(((float(old_price) - float(new_price)) / float(old_price)) * 100, 2)} %'

        # проверка тегов
        for tags in response.xpath(response_list[3]).extract():
            try:
                new_tag = str(tags).replace('\n', '')
                tags_list.append(new_tag.replace(' ', ''))
            except ValueError:
                pass

        # тут забираются категории
        for section in response.css(response_list[4]).extract():
            try:
                section_list = re.sub(r"<[^>]+>", "", section, flags=re.S).replace('  ', '/').split('/')

            except ValueError:
                pass

        # здесь забираются все картинки
        for img_text in str(response.css(response_list[5]).extract()).split('\"'):
            if img_text.startswith('/images'):
                more_img.append(img_text.split(' ')[0])

        # тут пришлось избавться от литералов,я не нашел у скрапи такую функцию
        description = re.sub(r"<[^>]+>", "", response.xpath(response_list[6]).get(), flags=re.S)
        replace_text = description.replace('\n', ' ')
        replace_text = replace_text.replace('\r', ' ')
        replace_text = replace_text.replace('\t', ' ')
        replace_text = replace_text.replace('   ', '')

        # словарь где собирает все данные и преобразуется в json
        item = {
            'timestamp': datetime.now().time(),
            'RPC': code[len(code) - 1],  # код товара не нашел,я просто из ссылки добавил
            'url': response.url,
            'title': response.xpath(response_list[7]).get(),
            'marketing_tags': tags_list,
            'brand': response.xpath(response_list[8]).get().split(' ')[0],
            'section': section_list,
            'price_data': {
                'current': dis_price,
                'original': price,
                'sale_tag': sale_tag
            },
            'stock': {
                'in_stock': in_stock,
                'count': '0'  # остаток не нашаел на сайте
            },
            'assets': {
                'main_image': response.urljoin(main_img),
                'set_images': [response.urljoin(x) for x in list(set(more_img))],
                'view360': [],  # не нашел на сайте
                'video': []  # не нашел на сайте
            },
            'metadata': {
                '__description': replace_text
            },
            'variants': 'int'  # не нашел такого пункта
        }
        yield item
