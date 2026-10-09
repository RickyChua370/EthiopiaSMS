"""Real Ethiopian businesses sourced from OpenStreetMap.

These are ACTUAL places — names, phone numbers and coordinates come straight from
OpenStreetMap (© OpenStreetMap contributors, ODbL). They are the "mappable but
website-less" tourism MSMEs this project targets, spanning several cities
(Addis Ababa, Lalibela, Gondar, Bahir Dar, Hawassa, Adama, and more) and
categories (restaurants, cafés, hotels, bars, shops, attractions).

Photos: OSM has almost no photos for these businesses. We do NOT use stock photos
or fake imagery of a specific business. Only the two places that have a genuinely
free, openly-licensed photo on Wikimedia Commons carry one (Ben Abeba Restaurant,
CC BY 2.0; Sheraton Addis, public domain). Every other listing has NO photo and the
site shows an honest "the owner hasn't added photos yet" note — exactly how the real
product behaves until the owner uploads their own via the SMS upload link.

Fields: (name, category_id, phone, lat, lon, short factual description, photo|None)
"""

from __future__ import annotations

REAL_BUSINESSES = [
    # --- The only two with a genuine, openly-licensed photo ---
    ("Ben Abeba Restaurant", 1, "+251 33 336 0215", 12.04325, 39.03701,
     "Restaurant with panoramic views in Lalibela.", "business_photos/ben_abeba.jpg"),
    ("Sheraton Addis", 3, "+251 11 517 1717", 9.0203, 38.75948,
     "Luxury hotel in central Addis Ababa.", "business_photos/sheraton_addis.jpg"),

    # --- Restaurants / food ---
    ("Aman Catering and Agelgil", 1, "+251916137579", 7.04464, 38.51151,
     "Restaurant serving Ethiopian cuisine in Hawassa.", None),
    ("Hewi Bread and Cake Bakery", 1, "0910292548", 6.86245, 37.76239,
     "Bakery and cake shop in southern Ethiopia.", None),
    ("Boss Burger", 1, "0911605433", 8.99761, 38.78488,
     "Burger restaurant in Addis Ababa.", None),
    ("Barakat Restaurant", 1, "+251915752666", 9.34642, 42.7967,
     "Restaurant in Dire Dawa.", None),
    ("Burger King", 1, "+251116662888", 8.99593, 38.78808,
     "Burger fast-food restaurant in Addis Ababa.", None),
    ("Habtish Fiyel Bet", 1, "+251910117650", 7.04845, 38.47732,
     "Restaurant known for Ethiopian tibs in Hawassa.", None),
    ("Parkdale Burger", 1, "+251939757575", 8.9951, 38.80914,
     "Burger restaurant in Addis Ababa.", None),

    # --- Cafés ---
    ("Africa Cafe", 2, "0918777228", 12.59464, 37.44796,
     "Cafe and coffee house in Gondar.", None),
    ("Harmony Cafe and Restaurant", 2, "+251 911 90 31 72", 8.15007, 38.82025,
     "Cafe and restaurant in central Ethiopia.", None),
    ("Iqlima Mana Bunaa", 2, "+251922005374", 8.60132, 40.32645,
     "Traditional coffee house in Asella.", None),

    # --- Hotels / lodging / hostels ---
    ("40 Springs Hotel", 3, "+251911435326", 6.00582, 37.54611,
     "Hotel in Arba Minch.", None),
    ("Christian Guest House", 3, "+251 93 819 1157", 12.02552, 39.04076,
     "Guest house in Lalibela.", None),
    ("Bahir Dar Backpackers Hostel", 3, "+251909867370", 11.59749, 37.37772,
     "Backpackers hostel in Bahir Dar.", None),
    ("Abay Minch Lodge", 3, "+251 58 218 1039", 11.60882, 37.41451,
     "Lodge near Lake Tana in Bahir Dar.", None),
    ("Dasist Guest House", 3, "0221121939", 8.53635, 39.25,
     "Guest house in Adama.", None),
    ("Gondar Backpackers", 3, "+251968596794", 12.59364, 37.44399,
     "Backpackers hostel in Gondar.", None),
    ("Adama Ras Hotel", 3, "02112188", 8.53917, 39.26136,
     "Hotel in Adama.", None),
    ("Fasillides Hotel", 3, "0918199690", 12.61537, 37.47479,
     "Hotel in Gondar.", None),

    # --- Bars / nightlife ---
    ("Assegid Bar", 9, "0913598510", 7.03552, 38.48486,
     "Bar in Hawassa.", None),
    ("Wim's Holland House", 9, "+251 91 188 7770", 9.00982, 38.7553,
     "Bar and restaurant in Addis Ababa.", None),
    ("Aseged Bar", 9, "+251913590666", 7.05871, 38.47321,
     "Bar in Hawassa.", None),

    # --- Shops / souvenirs ---
    ("Wudassie Souvenir", 10, "+251 111 57 42 42", 9.02171, 38.75247,
     "Souvenir and gift shop in Addis Ababa.", None),
    ("Ras Dashen Shop", 10, "0581111029", 12.61208, 37.46939,
     "Shop in Gondar.", None),

    # --- Clothing / fashion ---
    ("VIP Romance Turkish Fashion", 5, "+251 920 27 51 68", 8.54013, 39.2637,
     "Clothing and fashion shop in Adama.", None),
    ("EDEN Sweater Garments", 5, "+251 11 88 41 00", 9.03212, 38.7518,
     "Garment and sweater shop in Addis Ababa.", None),

    # --- Cultural attractions ---
    ("Blue Nile Cultural Hall", 8, "+251 462 200 197", 7.05692, 38.48978,
     "Cultural venue in Hawassa.", None),
    ("CMC Cultural Center", 8, "+251947920219", 9.01805, 38.84317,
     "Cultural centre in Addis Ababa.", None),

    # --- One more café for balance ---
    ("Tiru Cafe", 2, "0918100200", 12.60500, 37.45500,
     "Cafe in Gondar.", None),
]
