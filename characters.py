# -*- coding: utf-8 -*-
import random

"""
Dinamik ko'p variantli parodiya va hazil generatori.
8 xil noyob xarakter, 4 xil toifa, 9 xil kasb-kor bo'yicha boyitilgan hazillar!
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
    },
    "taksist": {
        "name": "🚕 Toshkent Taksisti (Bratva)",
        "badge": "Shahar Yo'lbarsi",
        "desc": "Yo'l-yo'lakay siyosatdan tortib hayot falsafasigacha gapirib beruvchi shovvoz.",
        "icon": "🚗"
    },
    "talaba": {
        "name": "🎓 Charchagan Talaba (Sessiya)",
        "badge": "Stipendiya Qahramoni",
        "desc": "Sessiyadan qo'rqmaydigan, doim och va choyxona poylaydigan sho'x talaba.",
        "icon": "📚"
    },
    "qaynona": {
        "name": "👑 Hazilkash Qaynona & Kelin",
        "badge": "Oila Boshlig'i",
        "desc": "Ham mehrli, ham shirin qistovli, kulgili oilaviy maslahatchi.",
        "icon": "🫖"
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
    "teacher": "📚 Ustoz / O'qituvchi",
    "office": "🏢 Ofis / Davlat xodimi",
    "student": "🎓 Talaba / O'quvchi",
    "builder": "🔨 Usta / Quruvchi",
    "general": "✨ Erkin inson (Umumiy)"
}

PROFESSION_WISHES = {
    "it": [
        "Kodingda bitta ham 'bug' chiqmasin, serverlaring hech qachon yiqilmasin, oyliging Silikon vodiysidagidek faqat dollarda hisoblansin! 💻🚀",
        "Klaviaturangdan dollar to'kilsin, Wi-Fi tezliging 1000 Gb/s bo'lsin, sun'iy intellekt ham sening oldingda tiz cho'ksin! ⚡",
        "StackOverflow dagi eng qiyin savollarga bir zumda yechim top, hayoting 'Error 404' ko'rmasin! 👨‍💻",
        "Kodlaring birinchi urinishdayoq 'Success' bo'lsin, monitoring panellaring doim yam-yashil yonsin! 🟢"
    ],
    "business": [
        "Kassangda pul sig'may ketsin, qarz daftaring butunlay yo'qolsin, tovarlaring 'otash' bo'lib bir kunda sotilib ketsin! 🍏📦",
        "Optom olgan narsang chakana narxda uchsin, bozorning eng qimmatbaho do'koni sening nomingda bo'lsin! 💰",
        "Mijozlaring raxmat aytib navbatda tursin, hisob raqamingdagi nollarni sanashga kalkulyatoringning kuchi yetmasin! 📈",
        "Daromading kun sayin ko'payib, biznesing xalqaro birjalarga chiqsin! 🌐💎"
    ],
    "driver": [
        "Tagdagi mashinang xuddi uchar samolyotdek silliq yursin, radarlar seni ko'rib 'Bu bizning odam' deb suratga olmasin! 🚗💨",
        "Baki doim 98-benzinda to'la bo'lsin, balonlaringga mix yaqinlashmasin, yo'llaring faqat ko'k chiroqda o'tsin! 🛑➡️🟢",
        "Mijozlar faqat saxiy va choychaqa tashlaydigan bo'lsin, motoridan faqat musiqadek mayin ovoz kelsin! 🚕",
        "GAI xodimlari seni ko'rib faqat 'Oq yo'l akam!' deb qol ko'tarsin! 🛣️"
    ],
    "doctor": [
        "Qo'llaring doim shifo ulashsin, o'zing esa 100 yil kasal bo'lmasdan mag'rur yurgin! Retseptingga faqat baxt va boylik yozilsin! 👨‍⚕️💊",
        "Bemorlaring bir zumda tuzalsin, stetoskopdan faqat quvonchli yurak urishi eshitilsin! Salomatliging temirdan mustahkam bo'lsin! 🩺",
        "Tibbiyot olamining eng oldi professori bo'lib yurgin, cho'ntaging dorilar bilan emas, yashil dollarlar bilan to'lsin! 💉",
        "Har bir operatsiyang yutuqli bo'lsin, obro'ying osmondek yuksalsin! 🌟"
    ],
    "teacher": [
        "O'quvchilaring jahon olimpiadalarida 1-o'rinni olsin, mehnating doim e'zoz va ehtiromda bo'lsin! 📚🏆",
        "Darslaringda shovqin bo'lmasin, oyliging har oy 100% ga oshib tursin! 🎓",
        "Qalamingizdan faqat hikmat va baxt nurlari yog'ilsin, ustozlik maqomingiz abadiy porlasin! ✍️",
        "Shogirdlaringiz kelajakda vazir, millioner bo'lib sizga minnatdorchilik bilan qimmatbaho mashinalar sovg'a qilsin! 🎁"
    ],
    "office": [
        "Kreslong charm, kabineting keng bo'lsin! Boshliqlaring senga qahva quyib berib, oyligingni har oy 50% ga oshirsin! 🏢💼",
        "Hisobotlaring bir martada tasdiqlansin, tushlik vaqti 2 soatga cho'zilsin, juma kuni erta ketishga ruxsat berilsin! ☕",
        "Stolingda qog'ozlar kamayib, hisobingda yevrolar ko'paysin! Mansab zinapoyasidan yugurib yuqoriga chiq! 👔",
        "Printering hech qachon qog'oz chaynmasin, kofe mashinang eng zo'r espresso quyib bersin! ☕✨"
    ],
    "student": [
        "Sessiyalaring doim 'avtomat' yopilsin, stipendiyang har oy o'sib tursin, domlalaring faqat havas bilan 5 qo'ysin! 🎓📚",
        "Diploming qizil, kelajaging oltin bo'lsin! Darslardan keyin eng zo'r chet el universitetlaridan taklifnoma yog'ilsin! ✈️",
        "Kutubxonada o'tirgan vaqting kelajakda millioner bo'lib qaytsin! Talabalik davring eng baxtli xotiralarga to'lsin! 🌟",
        "Kurs ishingni birinchi martadayoq domlang o'qimay imzolab bersin! 📝🎉"
    ],
    "builder": [
        "Qurgan binolaring ming yil qad rostlasin, qo'ling dard ko'rmasin! Zakazlaring ko'pligidan telefoning tinmasin! 🔨🧱",
        "Sementing toshdek, ishonching tog'dek mustahkam bo'lsin! Har bir urgan mixing senga oltin olib kelsin! 🏗️",
        "Usta bo'lsang — senchalik bo'lsin! Mijozlar uyingni eshigida oylap navbat poylasin! 📐",
        "Loyiha chizmalaring doim bir urinishda tasdiqlansin, smetang faqat plyusda bo'lsin! 💰"
    ],
    "general": [
        "Har bir bosgan qadaming omad keltirsin, cho'ntaging doimo to'la, peshonang esa charog'on bo'lsin! ✨",
        "Yuzingdan tabassum, qalbingdan xotirjamlik va uyingdan baraka hech qachon arimasin! 🕊️",
        "Dushmanlaring orqangdan havas bilan qarasin, yaqinlaring sening bilan faxrlansin! 🌟",
        "Salomatliging po'latdek mustahkam, kayfiyating esa 24/7 eng yuqori notada bo'lsin! 🚀"
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
    
    r_name = recipient_name.strip().capitalize() if recipient_name else "Do'stim"
    s_name = sender_name.strip() if sender_name else "Do'stingiz"
    
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

Hurmat bilan: **Don Karleone** 💼 (Sodiq do'stingiz {s_name} buyurtmasi)""",

            "taksist": f"""🚕 **EE {r_name} BRATVA, TO'XTA BIR DAQIQA!** 🚕

Yo'l-yo'lakay eshitib qoldim: 'U do'stlarini unutib yubordi' deyishayapti!
Ko'p rulni noto'g'ri burma, jigar! Gazni bosib, choyxonaga yetib kel!

Tagdagi 'motor'ingga tilagim:
{prof_wish}

Salyut bilan: **Toshkent Taksisti** 🚗 (Qadrdoning {s_name} bilan birga)""",

            "talaba": f"""🎓 **{r_name}, MENGA QARA, SESSISYADAN QOCHGAN TALABA!** 🎓

O'zingcha katta profi bo'lib ketdingmi? Bitta choyxona qilishga kelganda 'Vaqtim yo'q' deb bahona qilishingni hamma biladi! 😄
Keling, do'stona bitta yig'ilaylik!

Kasbing bo'yicha tilak:
{prof_wish}

Hurmat bilan: **Sessiya Qurboni Talaba** 📚 ({s_name} nomidan)""",

            "qaynona": f"""🫖 **VOY {r_name} JONIM, SIZGA BIR GAPIM BOR EDI!** 🫖

Ko'rinmay ketdingiz-ku? Qachon bitta issiq choyga chaqirasiz?
Ish-ish deb o'zingizni unutmang, yaqinlarga vaqt ajrating!

Duomiz:
{prof_wish}

Mehribon: **Hazilkash Qaynona/Kelin** 👑 ({s_name} sizni o'ylaydi)""",

            "shoir": f"""📜 **BAYT: {r_name} NING G'OYIB BO'LGANIGA ATALDI!** 📜

Do'stlaringni unutib qaylargadir ketding sen,
O'zingcha osmondagi oylarga ham yetding sen!
Kelgin endi bir zumga, choyxonada osh tayyor,
Qadrdonlar diydorin unutib ne etding sen?!

Kasbingiz hamisha yuksalsin:
{prof_wish}

Qalamkash: **Shoir Bobo** ✍️ ({s_name} sog'inchi)"""
        }
        return roast_texts.get(char_key, roast_texts["boyvachcha"])

    elif category == "debt":
        debt_texts = {
            "boyvachcha": f"""💸 **SALOM, {r_name} JIGAR! KICHIK BIR ESLATMA!** 💸

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

Hurmat ila: **Don Karleone** 💼""",

            "taksist": f"""🚕 **AKAM {r_name}, SCHYOTCHIK ISHLAB TURIBDI!** 🚕

Bilasizku, benzin narxi ham oshyapti, hayot ham ketyapti!
Do'stingiz {s_name} ga berilishi kerak bo'lgan kichik hisob-kitobni yopib yuborsak, yo'limiz ancha ravon bo'lardi! 😉

Ishingiz doim yurishsin:
{prof_wish}

Oq yo'l bilan: **Taksist Akangiz** 🚖""",

            "talaba": f"""🎓 **EY {r_name}, STIPENDIYA KELMADI, UMID SENDAN!** 🎓

Bilasanku, talabaning holini: qorni och, cho'ntagi bo'sh!
O'sha berilgan kichik qarzni qaytarib tursang, bitta issiq lavash yeb, senga duo qilib yurardik! 🌯

Kasbingga omad:
{prof_wish}

Qorin g'amida: **Talaba Do'stingiz** 📚 ({s_name} iltimosi bilan)""",

            "qaynona": f"""🫖 **BOLAM {r_name}, HISOB-KITOB TOZA BO'LSA — KO'NGL TOZA BO'LADI!** 🫖

Do'stingiz {s_name} ga bitta qarab qo'ying, qarz degan narsani ortga surmagan yaxshi, baraka ketadi!
Bugunoq kartasiga tashlab bering-da, yorug' yuz bilan yuring!

Duomiz:
{prof_wish}

Ehtirom ila: **Hazilkash Qaynona** 👑""",

            "shoir": f"""📜 **QARZ HAQIDA HIKMATLI BAYT: {r_name} GA!** 📜

Qarz bergan do'st doimo intizor bo'lib kutar,
Qaytarilgan har omonat do'stlik rishtasin tutar!
Vaqtida uzilgan hisob ko'ngillarni shod etar,
Baraka yog'ilib uyga, g'am-alamlar chekilar!

Kasbingiz doim gullasin:
{prof_wish}

Nasihat ila: **Shoir Bobo** ✍️"""
        }
        return debt_texts.get(char_key, debt_texts["boyvachcha"])

    elif category == "motivation":
        motivation_texts = {
            "boyvachcha": f"""👑 **{r_name}, MENGA QARA, KELAJAK SENIKI!** 👑

Hech qachon o'zingga shubha qilma! Dunyo katta, imkoniyatlar cheksiz!
Birovlar gapiraveradi, sen esa faqat oldinga qarab, hisobingdagi nollarni ko'paytirib yuravergin!

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

Ehtirom ila: **Xalq Donishmandi** ✍️""",

            "taksist": f"""🚕 **{r_name} JIGAR, TEZLIKNI TUSHURMA, MAQSAD SARI BOS!** 🚕

Yo'lda probka bo'ladi, svetofor qizil yonadi, lekin harakatdan to'xtamasang — manzilga baribir birinchi yetib borasan!
Hayot ham shunaqa: gazni bos, o'zingga ishon!

Ishlaring doim silliq ketsin:
{prof_wish}

Omad tilovchi: **Taksist Akangiz** 🚖 ({s_name} dildosh)""",

            "talaba": f"""🎓 **{r_name}, BIZ HALI DUNYONI ZABT ETAMIZ!** 🎓

Hozir qiyin bo'lishi mumkin, lekin bu mehnatlarning mevasi ertaga shirin bo'ladi!
O'zingga ishon, ilm va harakat hech qachon zoye ketmaydi!

Kelajaging buyuk bo'lsin:
{prof_wish}

Do'stona ruhda: **Talaba Jo'rang** 📚 ({s_name} doim qo'llab-quvvatlaydi)""",

            "qaynona": f"""🫖 **BO'TAM {r_name}, HAR ISHDA BIR HIKMAT BOR!** 🫖

Hech qachon ko'nglingizni cho'ktirmang! Sabrli bo'lgan insonning baxti butun, barakasi ortiq bo'ladi.
Boshlagan har bir ezgu ishingizda Alloh o'zi madadkor bo'lsin!

Duomiz siz bilan:
{prof_wish}

Oq fotiha bilan: **Hazilkash Qaynona** 👑"""
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
Hurmat ila: **Don Karleone (Shef)** 💼 ({s_name} ehtiromi bilan)""",

            "taksist": f"""🚕 **EE {r_name} AKAM! BUGUN SHAHARDA ENG KATTA BAYRAM!** 🚕

Ko'chalar yam-yashil, radarlar ham sizni tabriklab turibdi!
Tug'ilgan kuningiz / bayramingiz qutlug' bo'lsin!
Mashinangizning baki benzinga, cho'ntagingiz esa dollarga to'lib yursin!

Sohangiz bo'yicha eng zo'r reys tilayman:
{prof_wish}

Signal chalib tabrikladi: **Toshkent Taksisti** 🚖 (Do'stingiz {s_name} taksida o'tirib yo'lladi)""",

            "talaba": f"""🎓 **SALOM {r_name}! BUGUN BAYRAM, DARS QILISH BEKOR!** 🎓

Bayraming bilan chin yurakdan tabriklayman!
Stipendiyang hech qachon kechikmasin, hayotingdagi har bir imtihondan 5 baho olib o'tgin!

Sohang bo'yicha maxsus tilagim:
{prof_wish}

Omon bo'l, doim yuzingdan kulgu arimasin!
Zo'r kayfiyat bilan: **Talaba Jo'rang** 📚 ({s_name} bilan birga)""",

            "qaynona": f"""👑 **AZIZIM {r_name}! UYIMIZNING GULI, BAYRAMINGIZ MUBORAK!** 👑

Doimo sog'-salomat bo'ling, yuzingizdan nur, qalbingizdan samimiyat arimasin!
Katta oilamiz siz bilan faxrlanadi! Baxtingiz osmondek baland bo'lsin!

Duoyi salomlarimiz:
{prof_wish}

Shirin mehr bilan: **Hazilkash Qaynona & Oila** 🫖 (Qadrdoningiz {s_name} tuhfasi)"""
        }
        return greeting_texts.get(char_key, greeting_texts["boyvachcha"])
