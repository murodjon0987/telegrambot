import random

"""
O'zbekistondagi mashhur xarakterlar va dinamik, ko'p variantli parodiya qutlovlari.
Har bir generatsiyada matn har xil va betakror bo'lib chiqadi!
"""

CHARACTERS = {
    "boyvachcha": {
        "name": "💰 Saxiy Boyvachcha Otaxon",
        "badge": "VIP Boshliq",
        "desc": "Dollar sochadigan, 'muammo yo'q jigar' deydigan saxiy millioner uslubida.",
        "icon": "💎"
    },
    "gai": {
        "name": "👮 Katta Leytenant (GAI / Tergovchi)",
        "badge": "Qat'iy Nazorat",
        "desc": "Protokol tuzuvchi, 'hujjatlarni taqdim eting' deb hazillashadigan organ xodimi.",
        "icon": "🚨"
    },
    "savdogar": {
        "name": "🍏 Bozorlik Shovvoz Akaxon (Malika/O'rikzor)",
        "badge": "Top Savdogar",
        "desc": "'O'zimni yaqinimga beradigan narxda', qizg'in savdo uslubidagi qutlov.",
        "icon": "📱"
    },
    "shoir": {
        "name": "📜 Xalq Donishmandi & Shoir Bobo",
        "badge": "Yuqori Adabiyot",
        "desc": "Qofiyali, chuqur falsafiy va kulgili baytlar bilan bezatilgan tabrik.",
        "icon": "✍️"
    },
    "mafioz": {
        "name": "🕶️ Xorijdagi 'Shef' (Don Karleone)",
        "badge": "Maxfiy Elita",
        "desc": "Qora ko'zoynakli, qat'iy va katta doiradagi nufuzli biznesmen uslubi.",
        "icon": "💼"
    }
}

REASONS = {
    "birthday": "🎂 Tug'ilgan kun",
    "car": "🚗 Yangi avtomobil olish",
    "wedding": "💍 To'y / Uylanish",
    "job": "💼 Yangi ish / Mansab",
    "travel": "✈️ Sayohat / Chet elga ketish",
    "general": "🎉 Shunchaki do'stona xursandchilik"
}

# -------------------------------------------------------------
# KO'P VARIANTLI DINAMIK MATNLAR BAZASI (Doim yangi tabrik)
# -------------------------------------------------------------
TEMPLATES = {
    "boyvachcha": {
        "birthday": [
            """💎 **ASSALOMU ALAYKUM, {r_name} JIGARIM!** 💎

Eshitdim, bugun sanda katta bayram emish! Pasportdagi yoshing bittaga ko'payibdi, lekin cho'ntagingdagi hisobing 10 barobar ko'paysin!

Man sanga nima deyman:
Har bitta bosgan qadaming $100 lik kupyura ustiga tushsin. Uyda qozon qaynayversin, garajingda esa kamida ikkita eng so'nggi model 'Inomarka' joy talashsin!

Sog'lik — Malibu 2 dan tez,
Baxt — Dubaydagi fontandan baland bo'lsin!
Hisob raqamingdagi nolllarni sanashga telefoningning quvvati yetmasin!

Hurmat bilan va cheksiz dollarli salom bilan:
👑 **Saxiy Boyvachcha Otaxoningiz**
*(Sanga shu qutlovni qadrdoning {s_name} maxsus yubordi!)*""",

            """💵 **VOY-VOY-VOY! {r_name} SHOHONA TUG'ILGAN KUN MUBORAK!** 💵

Jigar, eshitib darhol bitta samolyotni burib, senga salom yo'llayapman!
Yoshing ulg'aygani sari nufuzing xuddi oltin quymasidek qimmatlashsin!

Xudo xohlasa:
• Ertalabki nonushta — Antalyada,
• Tushlik — Parijda,
• Kechki osh — Toshkentda eng yaqin jigarlar davrasida bo'lsin!

Cho'ntagingdagi dollarlar shunaqangi qalin bo'lsinki, o'tirganingda qiynalib o'tirgin!
Salomat bo'l, doim peshonang yorug' bo'lsin!

Hurmat ila: **Boyvachcha Otaxon** 🍾
*(Birodaring {s_name} nomidan)*""",

            """✨ **QANI, BIR QARSAK BO'LSIN! {r_name} BUGUN TUG'ILGAN!** ✨

Assalomu alaykum, eng qimmatbaho insonim!
Bugun Toshkentdan to Nyu-Yorkkacha bo'lgan barcha bankomatlar sening nomingga xizmat qilsin!

Dushmaning ko'rib xafa bo'lsin,
Do'stlaring ko'rib havas qilsin!
Uy to'la bola-chaqa, hovli to'la baraka bo'lsin!

Har yili shunaqa dabdaba bilan, faqat eng zo'r kayfiyatda nishonlash nasib qilsin!
Yuz yoshga kirgin, jigar!

Sening sodiq boyvachchang: **Saxiy Otaxon** 💎
*(Do'sting {s_name} doim yoningda!)*"""
        ],

        "car": [
            """🚗 **VAALAYKUM ASSALOM, {r_name} BOYVACHCHA!** 🚗

Obbo, tagdagi 'toychoq' muborak bo'lsin! Mashinani eng zo'ri nasib qilibdi-ku!
Faqat bir narsa: Radarlar seni ko'rib kamerasi o'chib qolsin, GAI xodimlari esa qo'l ko'tarib faqat 'Oq yo'l, shef!' deb turishsin!

Baki doim 98-benzinda to'la bo'lsin,
Balonlari teshilmasin,
Salonidan doim yangi qimmat atir hidi anqib tursin!

To'y-hashamlarga mingin, faqat yaxshi kunlarga yursin!
Hurmat bilan: **Saxiy Boyvachcha** 🚀
*(Qadrdoning {s_name} nomidan)*""",

            """🚘 **{r_name}, YANGI OTING MUBORAK BO'LSIN!** 🚘

Eshitdim, tagga yangi mashina minibsan! Endi ko'chalarda faqat 'signal' chalib yurish qolibdi-da!
Moshinang xuddi uchar gilamday silliq yursin,
Probegi faqat baxt sari aylansin!

Moy almashtirishga borganingda usta faqat 'Hammasi ideal!' deb hayratda qolsin!
Katta yo'llarda omad hamrohing bo'lsin!

Hurmat bilan: **Boyvachcha Otaxon** 🏎️"""
        ],

        "wedding": [
            """💍 **O-HO-HO! {r_name} UKAMIZ OILA QURYAPTI!** 💍

Shunday qilib, bo'ydoqlik saflaridan bitta qimmatbaho generalimiz chiqib ketdi-da!
Ilohim, ostonangdan baraka arimasin. Kelin bilan qo'sha qarib, chaqaloqlarning qiy-chuvidan hovlingizga sig'may ketinglar!

Oilaviy byudjetingiz xuddi Markaziy Bankning rezerviday to'lib-toshsin!
Sevgi va muhabbat hech qachon arimasin!

Hurmat bilan: **Saxiy Boyvachcha** 🥂
*(Dardingni biladigan do'sting {s_name} dan)*""",

            """👑 **{r_name}, TO'Y MUBORAK BO'LSIN, JIGAR!** 👑

Mana bu haqiqiy mardning ishi bo'ldi! Ikki yoshning qo'llari abadiy birga bo'lsin!
Uyingizga kirgan har bir mehmon faqat havas bilan boqsin!
Tug'ilajak farzandlaringiz ham xuddi o'zingizdek mard va saxiy insonlar bo'lib yetishsin!

To'yona mendan — eng zo'r tilaklar bilan: **Saxiy Boyvachcha** 🎉"""
        ],

        "job": [
            """💼 **QANI, BIR QARSAK BO'LSIN! {r_name} MANSABGA MINDI!** 💼

Eshitdim, yangi kabinet, yangi charm kreslo! Endi buyruqlarni qahva ichib beradigan vaqtlar kelibdi-da, a?
Kreslong shunaqangi qulay bo'lsinki, faqat kattaroq daromad keltiradigan qarorlar chiqarasan!

Oyliging ko'pligidan kassirlar sanashdan charchasin!
Omad, jigar!
Hurmat bilan: **Saxiy Boyvachcha** 📈""",

            """👔 **{r_name}, YANGI LAVOZIM QUTLUG' BO'LSIN!** 👔

Katta ishlarga — katta qadamlar! Sen bu lavozimga 100% loyiq eding!
Har bir loyihang muvaffaqiyatli chiqsin, rahbarlar faqat senga suyansin!
Karyerang osmono'par binolarday baland bo'lsin!

Hurmat bilan: **Saxiy Boyvachcha** ⭐"""
        ],

        "travel": [
            """✈️ **{r_name}, OQ YO'L, DUNYO KEZAR BOYVACHCHA!** ✈️

Passportga yangi muhrlar, hayotga esa unutilmas taassurotlar to'lsin!
Samolyotning 'Business Class' joylari faqat sen uchun bo'lsin!
Borgan joylaringda faqat yaxshi odamlar uchrasin, chamadoning sovg'alarga to'lib qaytsin!

Salom bilan: **Boyvachcha Otaxon** 🏖️"""
        ],

        "general": [
            """✨ **SALOM, {r_name}! KAYFIYATLAR QANDAY?** ✨

Senga hech qanday sababsiz, shunchaki xursandchilik uchun eng zo'r tilaklarni yo'llayapman!
Hayoting xuddi 5 yulduzli lyuks mehmonxonaday dabdabali, rejalaring esa Shveysariya soatiday aniq bo'lsin!

Hurmat bilan: **Boyvachcha Otaxon** 💎
*(Do'sting {s_name} yodiga tushding)*""",

            """🌟 **{r_name} JIGARIM, SHUNCHAKI BIR QUCHOQ SALOM!** 🌟

Ishlar qalay, kayfiyatlar 100% mi?
Doim shunday yorug' yuz bilan, hech kimga egilmay, boshni baland ko'tarib yurgin!
Boylik va omad har doim yoningda bo'lsin!

Hurmat ila: **Boyvachcha** 🤝"""
        ]
    },

    "gai": {
        "birthday": [
            """🚨 **DIQQAT! PROTOKOL № 777: TUG'ILGAN KUN SABABLI TO'XTATILDINGIZ!** 🚨

Fuqaro: **{r_name}**!
Siz ushbu kunda 'Cheksiz quvonch va baxt' zonasida tezlikni me'yoridan 200 km/soatga oshirganingiz uchun to'xtatildingiz!

JARIMA O'RNIGA QUYIDAGI MAJBURIY JAZO BELGILANADI:
1. 100 yil davomida har kuni kamida 10 marotaba samimiy kulib yurish!
2. Har qanday g'am-tashvishni zudlik bilan 'jarima maydonchasi'ga jo'natish!
3. Cho'ntakda hech qachon 'hujjatsiz' kam pul bilan yurmaslik!

Guvohnoma muddati: CHEKSIZ!
Xizmatni o'tovchi: **Katta Leytenant Qattiqqo'lov** 🚔
*(Sizni do'stingiz {s_name} shaxsan 'ushlab berdi')*""",

            """👮‍♂️ **ISMI: {r_name} | MODDA: YOSHNING YANA BITTAGA OSHISHI!** 👮‍♂️

Hurmatli fuqaro! Tekshiruv natijasida sizning hayotingizda baxt ko'rsatkichi 100% dan oshib ketgani ma'lum bo'ldi!
Qaror qabul qilindi:
Siz umrbod sog'lom va omadli bo'lishga HUKM QILINDINGIZ! Qaror ustidan shikoyat qilib bo'lmaydi!

Tabassum qiling, fotoradar suratga olmoqda! 📸
Inspektor: **GAI Xodimi**"""
        ],

        "car": [
            """🚨 **DIQQAT, HAYDOVCHI {r_name}! HUJJATLARNI KO'RSATING!** 🚨

Yangi transport vositangiz 'O'ta hashamatli va havas qilsa arzigulik' moddasi bo'yicha to'xtatildi!
Qaror: Balonlaringiz hech qachon mix ko'rmasin, tezlik kameralari siz o'tganingizda chiroyli selfi deb o'ylab suratga olmasin!

Ko'cha harakati qoidalariga amal qiling, lekin omad yo'lida qizil chiroqqa to'xtamang!
Inspektor: **GAI Xodimi** 🛑""",

            """🚔 **HAYDOVCHI {r_name}, TOYCHOQ MUBORAK!** 🚔

Guvohnomangiz toza, moshinangiz toza, yo'lingiz doimo bexatar bo'lsin!
Faqat bir iltimos: baxt va omad yo'lida tezlikni me'yoridan oshirishga ruxsat beriladi!

Hurmat bilan: **Katta Leytenant** 🚦"""
        ],

        "general": [
            """🚨 **PROFILAKTIK OGOHLANTIRISH: {r_name}!** 🚨

Sizning yuzingizda jiddiylik alomatlari aniqlandi! Zudlik bilan tabassum qiling, aks holda bayramona moddalar bilan javobgarlikka tortilasiz!
Do'stingiz {s_name} sizga tinchlik va sihat-salomatlik tilab yo'lladi! 🚔"""
        ]
    },

    "savdogar": {
        "birthday": [
            """📱 **ASSALOMU ALAYKUM, {r_name} AKAM! BUGUN SIZGA ENG ZO'R 'SKIDKA'!** 📱

Akam, toshkentcha aytganda — bugun sizning modelingiz chiqqan kun ekan!
Zavoddan yangi chiqqan 'Original 100% batareya' kabi energiyangiz hech qachon 1% ga tushmasin!

Hayotingizda 'brak' kunlar bo'lmasin,
Xarajatlaringiz 'optom' narxda,
Daromadlaringiz esa 'eng qimmat chakana' narxda tushsin!

Sizga eng yaqin akaxon sifatida o'zim kafolat beraman: Baxtingizga 100 yil garantiya!
Hurmat bilan: **Malika & O'rikzor Shovvozlari** 📦
*(Shu zo'r taklifni sizga {s_name} ilindi)*""",

            """🍎 **AKAM {r_name}! BUGUN BOZORDA BOSHQA GAP YO'Q!** 🍎

Tug'ilgan kuningiz bilan!
Sizdek xaridorgir, qimmatbaho va asl insonlar bozorda ham, hayotda ham kamdan-kam uchraydi!
Savdo doimo chaqqon, kassa doimo to'la bo'lsin!

Hurmat ila: **Bozorchi Akangiz** 🤝"""
        ],

        "car": [
            """🚗 **VOY BO'Y, {r_name}! TOYCHOQNI O'ZIMIZDAN OLGANDAY BO'LIPSIZ-KU!** 🚗

Muborak bo'lsin, akam! Birinchi qo'l, probeq halol, kraskasi toza bo'lsin!
Moshinangiz faqat to'ylarga, dam olishlarga va xursandchilikka xizmat qilsin!

Hurmat bilan: **Shovvoz Savdogar** 📱"""
        ],

        "general": [
            """🍏 **AKAM {r_name}, SIZGA ENG SARALANGAN TILAKLAR!** 🍏

Bozorning eng shirin olmasiday totli umr, eng sifatli tovariday mustahkam sog'lik tilayman!
Savdo doim barakali bo'lsin!
Salom bilan: **Savdogar Akangiz**"""
        ]
    },

    "shoir": {
        "birthday": [
            """📜 **BAYTI SHARIF: {r_name} SHARAFIGA BITILGAN QASIDA** 📜

Quyosh ham charqladi bugun o'zgacha,
Quvonch to'lib toshsin tongdan kezgacha.
Umringiz bog'lari so'lmasin aslo,
Dardingiz ketolsin hatto o'zgacha!

Yuz yoshga kiringiz mag'rur va omon,
Sizday insonlarni asrasin Zamon!
Cho'ntakda hamisha yashil dollarlar,
Yurakda yashasin orzuyu-armon!

Qalam tebratdi: **Shoir & Donishmandi Davron** ✍️
*(Ushbu baytni aziz do'stingiz {s_name} sizga tuhfa etdi)*""",

            """📖 **{r_name} GA ATALGAN YURAK SO'ZLARI** 📖

Bahor gullaridek ochilsin ko'ngil,
Toleyingiz bo'lsin hamisha yorug'.
Ezgu niyatlarga yetingiz dadil,
Har bir kuningizga yog'ilsin qutlug'!

Ehtirom ila: **Shoir Bobo** 📜"""
        ],

        "general": [
            """📜 **DO'STLIK HAQIDA HIKMAT: {r_name} GA!** 📜

Chin do'st gavhar erur, topilmas oson,
Sizday fidoyiga qoyil har inson.
Baxt va saodatga to'lsin uyingiz,
Baland parvoz etsin doim o'yingiz!

Ehtirom ila: **Donishmand** ✍️"""
        ]
    },

    "mafioz": {
        "birthday": [
            """🕶️ **BU SHAXSIY EMAS, {r_name}... BU SHUNCHAKI HURMAT!** 🕶️

Sitsiliyadan to Toshkentgacha bo'lgan barcha do'stlar nomidan:
Tug'ilgan kuning muborak, janob {r_name}!

Senga rad etib bo'lmaydigan bitta taklifim bor:
Dushmanlaring oldingda tiz cho'ksin,
Hamkorlaring so'zingni ikki qilmasin,
Va oilang doimo eng yuqori darajadagi himoyada bo'lsin!

Katta oilamiz seni qadrlaydi.
Hurmat ila: **Don Karleone (Shef)** 💼
*(Xabarni yetkazuvchi konseleori: {s_name})*""",

            """🍸 **JANOB {r_name}, QADEH SIZNING SHARAFINGIZGA KO'TARILDI!** 🍸

Haqiqiy nufuz — pul bilan emas, so'zning ustidan chiqish bilan o'lchanadi.
Sizga har qanday muzokaralarda g'alaba va tinch-omonlik tilayman!

Bizning hurmatimiz cheksiz.
Salom bilan: **Shef** 🕶️"""
        ],

        "general": [
            """🕶️ **JANOB {r_name}, SHEF SIZGA SALOM YO'LLADI!** 🕶️

Bizning qoidamiz oddiy: Omad — doimo biz bilan!
Sizga katta ishlarda muvaffaqiyat va yuksak nufuz tilayman.

Hurmat bilan: **Shef** 💼"""
        ]
    }
}

def generate_greeting(char_key: str, recipient_name: str, reason_key: str, sender_name: str = "Do'stingiz") -> str:
    """Tanlangan obraz, qabul qiluvchi va sabab bo'yicha dinamik, tasodifiy (har safar har xil) eksklyuziv tabrik matnini generatsiya qiladi."""
    
    r_name = recipient_name.strip().capitalize()
    s_name = sender_name.strip()
    
    char_dict = TEMPLATES.get(char_key, TEMPLATES["boyvachcha"])
    reason_options = char_dict.get(reason_key, char_dict.get("birthday", []))
    
    # Agar ushbu sabab uchun ro'yxat bo'sh bo'lsa, umumiy yoki tug'ilgan kun ro'yxatidan olamiz
    if not reason_options:
        reason_options = char_dict.get("birthday", [f"Tabriklaymiz, {r_name}!"])
        
    # Tasodifiy bittasini tanlash (har doim bir xil bo'lmasligi uchun)
    selected_template = random.choice(reason_options)
    
    # Ismlarni formatlash
    greeting = selected_template.format(r_name=r_name, s_name=s_name)
    return greeting
