import random

"""
Dinamik ko'p variantli parodiya va hazil generatori.
Har xil kategoriyalar: Tabrik, Hazil/Roast, Qarz eslatish, Motivatsiya.
Har bir soha (IT, Savdo, Taksi, Tibbiyot...) ga mos maxsus professional hazillar!
"""

CHARACTERS = {
    "boyvachcha": {
        "name": "💰 Saxiy Boyvachcha Otaxon",
        "badge": "VIP Boshliq",
        "desc": "Dollar sochadigan, 'muammo yo'q jigar' deydigan saxiy millioner.",
        "icon": "💎"
    },
    "gai": {
        "name": "👮 Katta Leytenant (GAI / Tergovchi)",
        "badge": "Qat'iy Nazorat",
        "desc": "Protokol tuzuvchi, jiddiy va qonuniy hazillar qiluvchi inspektor.",
        "icon": "🚨"
    },
    "savdogar": {
        "name": "🍏 Malika & O'rikzor Shovvozi",
        "badge": "Top Savdogar",
        "desc": "'O'zimni yaqinimga beradigan narxda' deydigan qizg'in savdogar.",
        "icon": "📱"
    },
    "shoir": {
        "name": "📜 Xalq Donishmandi & Shoir Bobo",
        "badge": "Yuqori Adabiyot",
        "desc": "Qofiyali, chuqur falsafiy va kulgili baytlar egasi.",
        "icon": "✍️"
    },
    "mafioz": {
        "name": "🕶️ Xorijdagi 'Shef' (Don Karleone)",
        "badge": "Maxfiy Elita",
        "desc": "Qora ko'zoynakli, nufuzli va so'zi qat'iy mafioz biznesmen.",
        "icon": "💼"
    }
}

CATEGORIES = {
    "greeting": "🎉 Bayram va Qutlov",
    "roast": "🎭 Do'stona Hazil & Roast",
    "debt": "💸 Qarzni Eslatish (Kulgili)",
    "motivation": "💼 Dono Maslahat & Motivatsiya"
}

PROFESSIONS = {
    "it": "💻 Dasturchi / IT mutaxassis",
    "business": "🍏 Savdogar / Biznesmen",
    "driver": "🚕 Haydovchi / Taksist",
    "doctor": "👨‍⚕️ Shifokor / Tibbiyot xodimi",
    "office": "🏢 Ofis / Davlat xodimi",
    "student": "🎓 Talaba / O'quvchi",
    "builder": "🔨 Usta / Quruvchi",
    "general": "✨ Erkin inson (Umumiy)"
}

PROFESSION_WISHES = {
    "it": [
        "Kodingda bitta ham 'bug' chiqmasin, serverlaring hech qachon yiqilmasin, oyliging esa Silikon vodiysidagidek faqat dollarda hisoblansin! 💻🚀",
        "Klaviaturangdan dollar to'kilsin, Wi-Fi tezliging 1000 Gb/s bo'lsin, sun'iy intellekt ham sening oldingda tiz cho'ksin! ⚡",
        "StackOverflow dagi eng qiyin savollarga bir zumda yechim top, hayoting 'Error 404' ko'rmasin! 👨‍💻"
    ],
    "business": [
        "Kassangda pul sig'may ketsin, qarz daftaring butunlay yo'qolsin, tovarlaring 'otash' bo'lib bir kunda sotilib ketsin! 🍏📦",
        "Optom olgan narsang chakana narxda uchsin, bozorning eng qimmatbaho do'koni sening nomingda bo'lsin! 💰",
        "Mijozlaring raxmat aytib navbatda tursin, hisob raqamingdagi nollarni sanashga kalkulyatoringning kuchi yetmasin! 📈"
    ],
    "driver": [
        "Tagdagi mashinang xuddi uchar samolyotdek silliq yursin, radarlar seni ko'rib 'Bu bizning odam' deb suratga olmasin! 🚗💨",
        "Baki doim 98-benzinda to'la bo'lsin, balonlaringga mix yaqinlashmasin, yo'llaring faqat ko'k chiroqda o'tsin! 🛑➡️🟢",
        "Mijozlar faqat saxiy va choychaqa tashlaydigan bo'lsin, motoridan faqat musiqadek mayin ovoz kelsin! 🚕"
    ],
    "doctor": [
        "Qo'llaring doim shifo ulashsin, o'zing esa 100 yil kasal bo'lmasdan mag'rur yurgin! Retseptingga faqat baxt va boylik yozilsin! 👨‍⚕️💊",
        "Bemorlaring bir zumda tuzalsin, stetoskopdan faqat quvonchli yurak urishi eshitilsin! Salomatliging temirdan mustahkam bo'lsin! 🩺",
        "Tibbiyot olamining eng oldi professori bo'lib yurgin, cho'ntaging dorilar bilan emas, yashil dollarlar bilan to'lsin! 💉"
    ],
    "office": [
        "Kreslong charm, kabineting keng bo'lsin! Boshliqlaring senga qahva quyib berib, oyligingni har oy 50% ga oshirsin! 🏢💼",
        "Hisobotlaring bir martada tasdiqlansin, tushlik vaqti 2 soatga cho'zilsin, juma kuni erta ketishga ruxsat berilsin! ☕",
        "Stolingda qog'ozlar kamayib, hisobingda yevrolar ko'paysin! Mansab zinapoyasidan yugurib yuqoriga chiq! 👔"
    ],
    "student": [
        "Sessiyalaring doim 'avtomat' yopilsin, stipendiyang har oy o'sib tursin, domlalaring faqat havas bilan 5 qo'ysin! 🎓📚",
        "Diploming qizil, kelajaging oltin bo'lsin! Darslardan keyin eng zo'r chet el universitetlaridan taklifnoma yog'ilsin! ✈️",
        "Kutubxonada o'tirgan vaqting kelajakda millioner bo'lib qaytsin! Talabalik davring eng baxtli xotiralarga to'lsin! 🌟"
    ],
    "builder": [
        "Qurgan binolaring ming yil qad rostlasin, qo'ling dard ko'rmasin! Zakazlaring ko'pligidan telefoning tinmasin! 🔨🧱",
        "Sementing toshdek, ishonching tog'dek mustahkam bo'lsin! Har bir urgan mixing senga oltin olib kelsin! 🏗️",
        "Usta bo'lsang — senchalik bo'lsin! Mijozlar uyingni eshigida oylap navbat poylasin! 📐"
    ],
    "general": [
        "Har bir bosgan qadaming omad keltirsin, cho'ntaging doimo to'la, peshonang esa charog'on bo'lsin! ✨",
        "Yuzingdan tabassum, qalbingdan xotirjamlik va uyingdan baraka hech qachon arimasin! 🕊️",
        "Dushmanlaring orqangdan havas bilan qarasin, yaqinlaring sening bilan faxrlansin! 🌟"
    ]
}

def generate_custom_message(
    char_key: str,
    recipient_name: str,
    category: str,
    profession_key: str,
    sender_name: str = "Do'stingiz"
) -> str:
    """Foydalanuvchining kasbi, sababi va personajiga moslangan eksklyuziv matn tayyorlaydi."""
    
    r_name = recipient_name.strip().capitalize()
    s_name = sender_name.strip()
    
    prof_list = PROFESSION_WISHES.get(profession_key, PROFESSION_WISHES["general"])
    prof_wish = random.choice(prof_list)

    if category == "roast":
        roast_texts = {
            "boyvachcha": f"""💎 **EY {r_name} JIGARIM, BIR QULOQ SOL!** 💎

Eshitdim, o'zingcha katta ishbilarmon bo'lib ketganmishsan! Lekin choyxonaga borganda hali ham kartang 'ishlamay qolishi' fosh bo'ldi-ku, a? 😄
Qani, tezroq millioner bo'l-chi, navbatdagi oshni sendan kutib qolamiz!

Aytgancha:
{prof_wish}

Hazillashdim, jigar! Omon bo'l, doim yorug' yuz bilan yur!
👑 **Boyvachcha Otaxon** (Seni sevadigan do'sting {s_name} nomidan)""",

            "gai": f"""🚨 **FUQARO {r_name}! DIQQAT, ROAST PROTOKOLI!** 🚨

Siz bugun 'Haddan ziyod jiddiylik va do'stlarni unutish' moddasi bo'yicha to'xtatildingiz!
Jazo choralari:
1. Telefoningizga kelgan qo'ng'iroqlarga 3 soniyada javob berish!
2. Do'stlarga haftasiga kamida bir marta osh berish!

Sohangiz bo'yicha maxsus qaror:
{prof_wish}

Tergovchi: **Katta Leytenant** 🚔 (Do'sting {s_name} topshirig'iga ko'ra)""",

            "savdogar": f"""🍏 **AKAM {r_name}! BOZORCHA GAPLASHAMIZ!** 🍏

O'zingizcha eng qimmat tovardek qadringizni oshirib yubordingiz-ku, ko'rinmaysiz? 
Skidka qiling ozroq, yaqinlarga ham vaqt ajrating!

Kasbingizga esa mana bu tilagim bor:
{prof_wish}

Hurmat ila: **Bozorchi Akangiz** 🤝 ({s_name} sizni sog'indi)""",

            "mafioz": f"""🕶️ **JANOB {r_name}, DON KARLEONE SIZNI KO'Z OSTIGA OLDI!** 🕶️

Xabarlarim yetib boryaptimi? Do'stlaringizni unutib, faqat ishga ko'milib ketibsiz.
Katta oilamiz bunday harakatlarni ma'qullamaydi! Bir oz dam oling, qahva iching!

Shefning shaxsiy buyrug'i:
{prof_wish}

Hurmat bilan: **Don Karleone** 💼 (Sodiq do'stingiz {s_name} buyurtmasi)"""
        }
        return roast_texts.get(char_key, roast_texts["boyvachcha"])

    elif category == "debt":
        debt_texts = {
            "boyvachcha": f"""💸 **SALOM, {r_name} JIGAR! KICHIK BIR ES LATMA!** 💸

Bilasanku, pul — bu qo'lning kiri! Lekin shu 'kir'ni biroz tozalab, vaqtida qaytarsang, do'stlik yanada yaltirab ketadi-da, jigar! 😉
Kassada kamomad bo'lmasin, kartaga bir qarab qo'ygin!

Sohang barakali bo'lsin:
{prof_wish}

Saxovatli salom bilan: **Boyvachcha Otaxon** 💰 ({s_name} nomidan)""",

            "gai": f"""🚨 **DIQQAT FUQARO {r_name}! TO'LOV MUDDATI KELDI!** 🚨

Bizning tizimimizda sizning 'Qarzni vaqtida qaytarish' to'g'risidagi qoidani buzganingiz aniqlandi!
Jarima qo'llanilmasligi uchun zudlik bilan {s_name} ning kartasiga kerakli summani o'tkazishingiz tavsiya etiladi! 💳

Kasbingizga esa oq yo'l:
{prof_wish}

Inspektor: **GAI Xodimi** 🚔""",

            "savdogar": f"""📱 **AKAM {r_name}, SALOM-SALOM!** 📱

Bozor qoidasi: 'Qarz uzilsa — savdo o'sadi, do'stlik mustahkam bo'ladi!'
Bitta qarz daftarchamga qarasam, sizning chiroyli ismingiz turibdi ekan. Xafa bo'lish yo'q, xursandchilikka bitta tashlab qo'ying!

Ishlaringizga baraka:
{prof_wish}

Hurmat bilan: **Savdogar Akangiz** 🍏""",

            "mafioz": f"""🕶️ **JANOB {r_name}, BIZNING BANKIRLARIMIZ BEZOVTA BO'LMOQDA!** 🕶️

Bu shaxsiy masala emas... bu shunchaki moliya intizomi.
Do'stingiz {s_name} ga tegishli kichik omonatni qaytarish vaqti yetib kelganga o'xshaydi.
Keling, bu masalani sokin va do'stona hal qilaylik!

Katta ishlaringizda omad:
{prof_wish}

Hurmat ila: **Don Karleone** 💼"""
        }
        return debt_texts.get(char_key, debt_texts["boyvachcha"])

    elif category == "motivation":
        motivation_texts = {
            "boyvachcha": f"""👑 **{r_name}, MENGA QARA, KELAJAK SENIKI!** 👑

Hech qachon o'zingga shubha qilma! Dunyo katta, imkoniyatlar cheksiz!
Birovlar gapiraveradi, sen esa faqat oldinga qarab, hisobingdagi nolllarni ko'paytirib yuravergin!

Sohang bo'yicha senga ishonchim komil:
{prof_wish}

Boshni baland ko'tar, sen haqiqiy lidersan!
Hurmat bilan: **Saxiy Boyvachcha Otaxon** 💎 ({s_name} doim yoningda!)""",

            "mafioz": f"""🕶️ **JANOB {r_name}, BU DUNYODA FAQAT KUCHLILAR G'ALABA QOZONADI!** 🕶️

Qiyinchiliklar — bu shunchaki tajriba. Har bir mag'lubiyat — kelgusi buyuk g'alabaning poydevoridir!
O'z maqsading sari qat'iy qadam bos, hech kim sening yo'lingni to'sa olmaydi!

Sening salohiyatingga ishonaman:
{prof_wish}

Katta oilamiz senga ishonadi.
Hurmat ila: **Don Karleone** 💼 ({s_name} ehtiromi bilan)""",

            "shoir": f"""📜 **{r_name} GA HIKMAT VA RUH QASIDASI!** 📜

Sabr qilgan toshni yorar deganlar,
Mehnat bilan baxtga yetar insonlar!
Yuragingda mangu yashasin umid,
Seni kutib turar buyuk zamonlar!

Kasbingiz nuri doim porlasin:
{prof_wish}

Ehtirom ila: **Xalq Donishmandi** ✍️"""
        }
        return motivation_texts.get(char_key, motivation_texts["boyvachcha"])

    else:
        # Bayram va Tabriklar (Greeting)
        greeting_texts = {
            "boyvachcha": f"""💎 **ASSALOMU ALAYKUM, {r_name} JIGARIM!** 💎

Bugungi bayraming muborak bo'lsin! 
Senga aytar tilagim bitta: har bir bosgan qadamingdan millionlar unsin, uy to'la baraka bo'lsin!

Sohang bo'yicha maxsus tilagim:
{prof_wish}

Sog'lik — Malibu 2 dan tez,
Baxt — Dubaydagi osmono'par binolarday baland bo'lsin!

Hurmat bilan va cheksiz dollarli salom bilan:
👑 **Saxiy Boyvachcha Otaxoningiz**
*(Senga shu qutlovni qadrdoning {s_name} yo'lladi!)*""",

            "gai": f"""🚨 **DIQQAT! PROTOKOL № 777: {r_name} SHARAFIGA!** 🚨

Siz bugun 'Cheksiz quvonch va baxt' zonasida to'xtatildingiz!
Jarima o'rniga umrbod sog'lom va omadli bo'lishga hukm qilindingiz!

Sohangiz bo'yicha maxsus ruxsatnoma:
{prof_wish}

Guvohnoma muddati: CHEKSIZ!
Xizmatni o'tovchi: **Katta Leytenant** 🚔 (Do'sting {s_name} nomidan)""",

            "savdogar": f"""🍏 **AKAM {r_name}, ENG ZO'R 'ORIGINAL' TABRIKLAR!** 🍏

Toshkentcha aytganda — bugun sizning modelingiz chiqqan kun!
Hayotingizda brak kunlar bo'lmasin, quvvatingiz 100% dan tushmasin!

Kasbingizga esa o'zim kafolat beraman:
{prof_wish}

Hurmat bilan: **Malika & O'rikzor Shovvozlari** 📦 ({s_name} sizni qadrlaydi!)""",

            "shoir": f"""📜 **QASIDA: {r_name} SHARAFIGA BITILGAN BAYT!** 📜

Quyosh ham charqladi bugun o'zgacha,
Quvonch to'lib toshsin tongdan kechgacha!
Umringiz bog'lari so'lmasin aslo,
Dardingiz ketolsin hatto o'zgacha!

Kasbingiz nuriga nur qo'shilsin:
{prof_wish}

Qalam tebratdi: **Shoir Bobo** ✍️ (Do'stingiz {s_name} tuhfasi)""",

            "mafioz": f"""🕶️ **JANOB {r_name}, BU SHAXSIY EMAS... BU HURMAT!** 🕶️

Sitsiliyadan to Toshkentgacha bo'lgan barcha do'stlar nomidan:
Bayramingiz muborak bo'lsin!

Senga rad etib bo'lmaydigan bitta tilagim bor:
{prof_wish}

Dushmaning oldingda bosh egsin, oilang esa doimo eng yuqori himoyada bo'lsin!
Hurmat ila: **Don Karleone (Shef)** 💼 ({s_name} ehtiromi bilan)"""
        }
        return greeting_texts.get(char_key, greeting_texts["boyvachcha"])
