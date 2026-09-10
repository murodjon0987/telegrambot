"""
O'zbekistondagi mashhur xarakterlar va parodiya qutlovlari shablonlari.
Har bir personaj o'zining betakror lug'ati, jargonlari va hazilomuz uslubiga ega.
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
    "car": "🚗 Yangi avtomobil olish (Muborak)",
    "wedding": "💍 To'y / Uylanish / Nikoh",
    "job": "💼 Yangi ish / Mansab ko'tarilishi",
    "general": "🎉 Shunchaki xursandchilik / Do'stlik hurmati"
}

def generate_greeting(char_key: str, recipient_name: str, reason_key: str, sender_name: str = "Do'stingiz") -> str:
    """Tanlangan obraz, qabul qiluvchi va sabab bo'yicha eksklyuziv tabrik matnini generatsiya qiladi."""
    
    r_name = recipient_name.strip().capitalize()
    s_name = sender_name.strip()
    
    templates = {
        "boyvachcha": {
            "birthday": f"""💎 **ASSALOMU ALAYKUM, {r_name} JIGARIM!** 💎

Eshitdim, bugun sanda bitta katta bayram emish! Pasportdagi yoshing bittaga ko'payibdi, lekin cho'ntagingdagi hisobing 10 barobar ko'paysin! 

Man sanga nima deyman:
Har bitta bosgan qadaming $100 lik kupyura ustiga tushsin. Uyda qozon qaynasin, garajingda esa kamida ikkita eng so'nggi model 'Inomarka' turib, joy talashsin! 

Sog'lik — Malibu 2 dan tez,
Baxt — Dubaydagi fontandan baland bo'lsin! 
Hisob raqamingdagi nolllarni sanashga kalkulyatoringning zaryadi yetmasin!

Hurmat bilan va cheksiz dollarli salom bilan:
👑 **Saxiy Boyvachcha Otaxoningiz**
*(Sanga shu qutlovni qadrdoning {s_name} maxsus buyurtma qildi!)*""",

            "car": f"""🚗 **VAALAYKUM ASSALOM, {r_name} BOYVACHCHA!** 🚗

Obbo, tagdagi 'toychoq' muborak bo'lsin! Mashinani dodasi nasib qilibdi-ku!
Faqat bir narsa: Radarlar sani ko'rib kamerasi o'chib qolsin, GAI xodimlari esa qo'l ko'tarib faqat 'Oq yo'l, shef!' deb turishsin!

Baki doim 98-benzinda to'la bo'lsin,
Balonlari teshilmasin,
Salonidan doim yangi qimmat atir hidi anqib tursin!

Tabbriklayman, to'y-hashamlarga mingin!
Hurmat bilan: **Saxiy Boyvachcha**
*(Qadrdoning {s_name} nomidan)*""",

            "wedding": f"""💍 **O-HO-HO! {r_name} UKAMIZ OILA QURYAPTI!** 💍

Shunday qilib, bo'ydoqlik saflaridan bitta qimmatbaho generalimiz chiqib ketdi-da! 
Ilohim, ostonangdan baraka arimasin. Kelin bilan qo'sha qarib, chaqaloqlarning qiy-chuvidan uyingizga sig'may ketinglar!

Oilaviy byudjetingiz xuddi Markaziy Bankning rezerviday to'lib-toshsin!

Hurmat bilan: **Saxiy Boyvachcha** 🥂
*(Dardingni biladigan do'sting {s_name} dan)*""",

            "job": f"""💼 **QANI, BIR QARSAK BO'LSIN! {r_name} MANSABGA MINDI!** 💼

Eshitdim, yangi kabinet, yangi kreslo! Endi buyruqlarni qahva ichib beradigan vaqtlar kelibdi-da, a?
Kreslong shunaqangi qulay bo'lsinki, faqat kattaroq daromad keltiradigan qarorlar chiqarasan! 

Oyliging ko'pligidan kassir sanashdan charchasin!
Omad, jigar! 
Hurmat bilan: **Saxiy Boyvachcha**""",

            "general": f"""✨ **SALOM, {r_name}! KAYFIYATLAR QANDAY?** ✨

Sanga hech qanday sababsiz, shunchaki xursandchilik uchun eng zo'r tilaklarni yo'llayapman!
Hayoting xuddi 5 yulduzli lyuks mehmonxonaday dabdabali, rejalaring esa Shveysariya soatiday aniq bo'lsin!

Hurmat bilan: **Boyvachcha Otaxon**"""
        },

        "gai": {
            "birthday": f"""🚨 **DIQQAT! PROTOKOL № 777: TUG'ILGAN KUN SABABLI TO'XTATILDINGIZ!** 🚨

Fuqaro: **{r_name}**!
Siz ushbu kunda 'Cheksiz quvonch va baxt' zonasida tezlikni me'yoridan 200 km/soatga oshirganingiz uchun to'xtatildingiz!

JARIMA O'RNIGA QUYIDAGI MAJBURIY JAZO BELGILANADI:
1. 100 yil davomida har kuni kamida 10 marotaba kulib yurish.
2. Har qanday g'am-tashvishni zudlik bilan 'jarima maydonchasi'ga jo'natish.
3. Cho'ntakda hech qachon 'hujjatsiz' kam pul bilan yurmaslik!

Guvohnoma muddati: CHEKSIZ!
Xizmatni o'tovchi: **Katta Leytenant Qattiqqo'lov**
*(Sizni do'stingiz {s_name} shaxsan 'ushlab berdi')* 🚔""",

            "car": f"""🚨 **DIQQAT, HAYDOVCHI {r_name}! HUJJATLARNI KO'RSATING!** 🚨

Yangi transport vositangiz 'O'ta hashamatli va havas qilsa arzigulik' moddasi bo'yicha to'xtatildi!
Qaror: Balonlaringiz hech qachon mix ko'rmasin, tezlik kameralari siz o'tganingizda chiroyli selfi deb o'ylab suratga olmasin!

Ko'cha harakati qoidalariga amal qiling, lekin omad yo'lida qizil chiroqqa to'xtamang!
Inspektor: **GAI Xodimi**""",

            "general": f"""🚨 **PROFILAKTIK OGOHLANTIRISH: {r_name}!** 🚨

Sizning yuzingizda jiddiylik alomatlari aniqlandi! Zudlik bilan tabassum qiling, aks holda bayramona moddalar bilan javobgarlikka tortilasiz!
Do'stingiz {s_name} sizga tinchlik va sihat-salomatlik tilab yo'lladi!"""
        },

        "savdogar": {
            "birthday": f"""📱 **ASSALOMU ALAYKUM, {r_name} AKAM! BUGUN SIZGA ENG ZO'R 'SKIDKA'!** 📱

Akam, toshkentcha aytganda — bugun sizning modelingiz chiqqan kun ekan! 
Zavoddan yangi chiqqan 'Original 100% batareya' kabi energiyangiz hech qachon 1% ga tushmasin!

Hayotingizda 'brak' kunlar bo'lmasin,
Xarajatlaringiz 'optom' narxda,
Daromadlaringiz esa 'eng qimmat chakana' narxda tushsin!

Sizga eng yaqin akaxon sifatida o'zim kafolat beraman: Baxtingizga 100 yil garantiya!
Hurmat bilan: **Malika & O'rikzor Shovvozlari** 📦
*(Shu zo'r taklifni sizga {s_name} ilindi)*""",

            "car": f"""🚗 **VOY BO'Y, {r_name}! TOYCHOQNI O'ZIMIZDAN OLGANDAY BO'LIPSIZ-KU!** 🚗

Muborak bo'lsin, akam! Birinchi qo'l, probeq halol, kraskasi toza bo'lsin! 
Moshinangiz faqat to'ylarga, dam olishlarga va xursandchilikka xizmat qilsin!

Hurmat bilan: **Shovvoz Savdogar** 🤝""",

            "general": f"""🍏 **AKAM {r_name}, SIZGA ENG SARALANGAN TILAKLAR!** 🍏

Bozorning eng shirin olmasiday totli umr, eng sifatli tovariday mustahkam sog'lik tilayman!
Savdo doim barakali bo'lsin! 
Salom bilan: **Savdogar Akangiz**"""
        },

        "shoir": {
            "birthday": f"""📜 **BAYTI SHARIF: {r_name} SHARAFIGA BITILGAN QASIDA** 📜

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

            "general": f"""📜 **DO'STLIK HAQIDA HIKMAT: {r_name} GA!** 📜

Chin do'st gavhar erur, topilmas oson,
Sizday fidoyiga qoyil har inson.
Baxt va saodatga to'lsin uyingiz,
Baland parvoz etsin doim o'yingiz!

Ehtirom ila: **Donishmand**"""
        },

        "mafioz": {
            "birthday": f"""🕶️ **BU SHAXSIY EMAS, {r_name}... BU SHUNCHAKI HURMAT!** 🕶️

Sitsiliyadan to Toshkentgacha bo'lgan barcha hamkorlar nomidan:
Tug'ilgan kuning muborak, janob {r_name}!

Senga rad etib bo'lmaydigan bitta taklifim bor:
Dushmanlaring oldingda tiz cho'ksin,
Hamkorlaring so'zingni ikki qilmasin,
Va oilang doimo eng yuqori darajadagi himoyada bo'lsin!

Katta oilamiz seni qadrlaydi.
Hurmat ila: **Don Karleone (Shef)** 💼
*(Xabarni yetkazuvchi konseleori: {s_name})*""",

            "general": f"""🕶️ **JANOB {r_name}, SHEF SIZGA SALOM YO'LLADI!** 🕶️

Bizning qoidamiz oddiy: Omad — doimo biz bilan!
Sizga katta ishlarda muvaffaqiyat va yuksak nufuz tilayman.

Hurmat bilan: **Shef**"""
        }
    }
    
    char_dict = templates.get(char_key, templates["boyvachcha"])
    greeting = char_dict.get(reason_key, char_dict.get("birthday", "Tabriklaymiz!"))
    return greeting
