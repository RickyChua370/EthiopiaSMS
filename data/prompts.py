"""Multilingual prompt strings for the SMS onboarding flow.

Each prompt key maps to a dict of language -> text (amh / orm / eng).
Prompts are intentionally short to fit comfortably inside SMS segments.

Location guidance uses the phone's built-in **Compass** app (which reports
latitude/longitude) rather than Google Maps, since basic phones may not have
Google Maps installed.
"""

from __future__ import annotations

PROMPTS: dict[str, dict[str, str]] = {
    "welcome": {
        "eng": "Welcome! Let's put your business online for tourists. It's free. "
               "Reply in your language anytime.",
        "amh": "እንኳን ደህና መጡ! ንግድዎን ለቱሪስቶች በመስመር ላይ እናስተዋውቅ። ነጻ ነው። "
               "በፈለጉት ጊዜ በቋንቋዎ ይመልሱ።",
        "orm": "Baga nagaan dhuftan! Daldala keessan turistootaaf online haa gochuu. "
               "Bilisa. Yeroo barbaaddanitti afaan keessaniin deebisaa.",
    },
    "ask_category": {
        "eng": "What type of business is it? Reply with the number:",
        "amh": "ንግድዎ ምን ዓይነት ነው? በቁጥር ይመልሱ፦",
        "orm": "Daldalli keessan gosa kami? Lakkoofsaan deebisaa:",
    },
    "ask_name": {
        "eng": "What is the name of your business?",
        "amh": "የንግድዎ ስም ማን ይባላል?",
        "orm": "Maqaan daldala keessanii eenyu?",
    },
    "ask_price": {
        "eng": "What is your typical price? (e.g. 150 ETB). Reply 'skip' if none.",
        "amh": "የተለመደ ዋጋዎ ስንት ነው? (ለምሳሌ 150 ብር)። ከሌለ 'skip' ይበሉ።",
        "orm": "Gatiin keessan meeqa? (fakkeenyaaf 150 ETB). Yoo hin jirre 'skip' jedhaa.",
    },
    # --- Location via the COMPASS app (not Google Maps) ---
    "ask_location_intro": {
        "eng": "Now your location. Most phones have a 'Compass' app that shows your "
               "coordinates. Let's use it.",
        "amh": "አሁን አካባቢዎ። አብዛኞቹ ስልኮች መጋጠሚያዎን የሚያሳይ 'ኮምፓስ' መተግበሪያ አላቸው። "
               "እሱን እንጠቀም።",
        "orm": "Amma iddoo keessan. Bilbilli hedduun aappilikeeshinii 'Compass' kan "
               "iddoo agarsiisu qaba. Isa haa fayyadamnu.",
    },
    "ask_location_steps": {
        "eng": "1) Stand at your business.\n2) Open the Compass app.\n3) It shows two "
               "numbers (latitude & longitude), e.g. 9.0105, 38.7612.\n4) Reply with those "
               "two numbers.",
        "amh": "1) ንግድዎ ጋር ይቁሙ።\n2) የኮምፓስ መተግበሪያውን ይክፈቱ።\n3) ሁለት ቁጥሮችን ያሳያል "
               "(latitude እና longitude)፣ ለምሳሌ 9.0105, 38.7612።\n4) እነዚያን ሁለት ቁጥሮች ይላኩ።",
        "orm": "1) Daldala keessan bira dhaabadhaa.\n2) Aappii Compass banaa.\n3) Lakkoofsa "
               "lama agarsiisa (latitude fi longitude), fkn 9.0105, 38.7612.\n4) Lakkoofsa "
               "lamaan sana ergaa.",
    },
    "location_invalid": {
        "eng": "Sorry, I couldn't read coordinates in Ethiopia's range. Please reply with "
               "two numbers like: 9.0105, 38.7612. Or reply 'area' to give a place name "
               "instead.",
        "amh": "ይቅርታ፣ በኢትዮጵያ ክልል ውስጥ መጋጠሚያ ማንበብ አልቻልኩም። እባክዎ እንደ 9.0105, 38.7612 "
               "ያሉ ሁለት ቁጥሮች ይላኩ። ወይም በምትኩ የቦታ ስም ለመስጠት 'area' ይበሉ።",
        "orm": "Dhiifama, qindoomina Itoophiyaa keessaa dubbisuu hin dandeenye. Maaloo "
               "lakkoofsa lama akka 9.0105, 38.7612 ergaa. Yookaan maqaa iddoo kennuuf "
               "'area' jedhaa.",
    },
    "ask_area_fallback": {
        "eng": "No problem. What area or neighbourhood is your business in? (e.g. Bole, Addis Ababa)",
        "amh": "ችግር የለም። ንግድዎ በየትኛው አካባቢ ነው? (ለምሳሌ ቦሌ፣ አዲስ አበባ)",
        "orm": "Rakkoo hin jiru. Daldalli keessan naannoo kami jira? (fkn Boolee, Finfinnee)",
    },
    "ask_description": {
        "eng": "In one or two sentences, describe your business for tourists.",
        "amh": "በአንድ ወይም ሁለት ዓረፍተ ነገር ንግድዎን ለቱሪስቶች ይግለጹ።",
        "orm": "Himoota tokko ykn lama keessatti daldala keessan turistootaaf ibsaa.",
    },
    # --- Deferred, connection-aware image upload ---
    "images_link": {
        "eng": "Your listing is now LIVE (text only). To add photos later when you have "
               "internet, open this link: {upload_url}",
        "amh": "ዝርዝርዎ አሁን በመስመር ላይ ነው (ጽሑፍ ብቻ)። ኢንተርኔት ሲኖርዎ ፎቶ ለመጨመር ይህን "
               "ሊንክ ይክፈቱ፦ {upload_url}",
        "orm": "Tarreen keessan amma online jira (barruu qofa). Yeroo intarneetii "
               "qabdan suuraa dabaluuf liinkii kana banaa: {upload_url}",
    },
    "confirm_published": {
        "eng": "Done! '{name}' is live for tourists to find. We will send bookings to "
               "this number. Reply 'edit' anytime to update.",
        "amh": "ተጠናቀቀ! '{name}' ቱሪስቶች እንዲያገኙት በመስመር ላይ ነው። ቦታ ማስያዣዎችን ወደዚህ "
               "ቁጥር እንልካለን። ለማዘመን በፈለጉ ጊዜ 'edit' ይበሉ።",
        "orm": "Xumurame! '{name}' turistootaan argamuuf online jira. Buukingii gara "
               "lakkoofsa kanaa ni ergina. Haaromsuuf yeroo kamiyyuu 'edit' jedhaa.",
    },
    "review_pending": {
        "eng": "Thank you! We are reviewing the translation to make sure it's accurate "
               "before publishing. It will be live shortly.",
        "amh": "አመሰግናለሁ! ትክክለኛ መሆኑን ለማረጋገጥ ትርጉሙን በመገምገም ላይ ነን። በቅርቡ "
               "በመስመር ላይ ይሆናል።",
        "orm": "Galatoomaa! Hiikni sirrii ta'uu isaa mirkaneeffachuuf gamaggamaa jirra. "
               "Dhiheenyatti online ta'a.",
    },
    "unknown": {
        "eng": "Sorry, I didn't understand. Reply 'help' for options.",
        "amh": "ይቅርታ፣ አልገባኝም። አማራጮችን ለማየት 'help' ይበሉ።",
        "orm": "Dhiifama, hin hubanne. Filannoodhaaf 'help' jedhaa.",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    """Fetch a prompt by key in the given language, falling back to English."""
    entry = PROMPTS.get(key, {})
    text = entry.get(lang) or entry.get("eng") or ""
    return text.format(**kwargs) if kwargs else text
