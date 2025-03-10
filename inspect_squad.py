#!/usr/bin/env python

import sys
import subprocess

# List of tuples containing names and surnames

national_squad = [
#    ("Bron",     "Dibb",      "dmt"),
#    ("Cam",      "Robertson", "dmt"),
#    ("Melissa",  "Romeril",   "dmt"),
#    ("Lach",     "Kirk",      "dmt"),

    ("Dylan",       "Schmidt",             "tra"),
    ("Flynn",       "Gunther",             "tra"),
    ("James",       "Dougal",              "tra"),
    ("Lach",        "Kirk",                "tra"),
    ("Reegan",      "Laidlaw",             "tra"),
    ("Regan",       "Lang",                "tra"),
    ("Seb",         "Smith",               "tra"),

    ("Lauren",      "Sheere",              "tra"),
    ("Mad",         "Davidson",            "tra"),
    ("Rachel",      "Schmidt",             "tra"),
    ("Sienna",      "French",              "tra"),
]


csg_team = [
    ("Alex",        "Withers",             "tra"),
    ("Alira",       "McBride",             "tra"),
    ("Ami",         "Watson",              "tra"),
    ("Anna",        "Clausen",             "tra"),
    ("Archer",      "Draper",              "tra"),
    ("Aria",        "Hewitson",            "tra"),
    ("Ben",         "Plunkett",            "tra"),
    ("Bradon",      "Freeman",             "tra"),
    ("Caitlin",     "McLachlan",           "tra"),
    ("Carmen",      "Leathart-Sutherland", "tra"),
    ("Charlie",     "Graham",              "tra"),
    ("Cleo",        "Pearce",              "tra"),
    ("Cooper",      "Ballinger",           "tra"),
    ("Cooper",      "Buckenham",           "tra"),
    ("Diesel",      "Mackie",              "tra"),
    ("Eamon",       "Lysaght",             "tra"),
    ("Emerson",     "Fenwick",             "tra"),
    ("Emily",       "Gill",                "tra"),
    ("Erika",       "Ward",                "tra"),
    ("Evie",        "Baynes",              "tra"),
    ("Felix",       "Rawhiti",             "tra"),
    ("Fletcher",    "Newlove",             "tra"),
    ("Flynn",       "Morrison",            "tra"),
    ("Flynn",       "Seagar",              "tra"),
    ("Freya",       "Askew",               "tra"),
    ("Gemma",       "Stead",               "tra"),
    ("Grace",       "Byrne",               "tra"),
    ("Harrison",    "Patrick",             "tra"),
    ("Hollie",      "Ward",                "tra"),
    ("Hugo",        "Robertson",           "tra"),
    ("Jaeger",      "Pryce",               "tra"),
    ("Jordan",      "Mkwananzi",           "tra"),
    ("Jye",         "Pryce",               "tra"),
    ("Karia",       "Kundycki",            "tra"),
    ("Kiera",       "Milnthorp",           "tra"),
    ("Kirah",       "Galbraith",           "tra"),
    ("Lilly",       "Bone",                "tra"),
    ("Luca",        "Williams",            "tra"),
    ("Luke",        "Johnston",            "tra"),
    ("Luke",        "Street",              "tra"),
    ("Mackenzie",   "Cameron",             "tra"),
    ("Macsen",      "Greenow",             "tra"),
    ("Maddison",    "Ballinger",           "tra"),
    ("Madison",     "Sillifant",           "tra"),
    ("Mia",         "Caldwell",            "tra"),
    ("Mitchell",    "Prutton",             "tra"),
    ("Naomi",       "King",                "tra"),
    ("Nate",        "Milne",               "tra"),
    ("Naya",        "Milnthorp",           "tra"),
    ("Nicola",      "McLachlan",           "tra"),
    ("Noah",        "Peawini",             "tra"),
    ("Oliver",      "Blank",               "tra"),
    ("Olivia",      "WILKINSON",           "tra"),
    ("Quen",        "Roux",                "tra"),
    ("Summer",      "Milne",               "tra"),
    ("Sydney",      "Gray",                "tra"),
    ("Taylor",      "Ritchie",             "tra"),
    ("Toby",        "Watson",              "tra"),
    ("Tyler",       "Macphail",            "tra"),
    ("Veronica",    "Stan",                "tra"),
    ("Violet",      "Robertson",           "tra"),
]

wc_team = [
    ("Bron",        "Dibb",                "dmt"),
    ("Cam",         "Robertson",           "dmt"),
    ("Melissa",     "Romeril",             "dmt"),

    ("Dylan",       "Schmidt",             "tra"),
    ("James",       "Dougal",              "tra"),
    ("Madaline",    "Davidson",            "tra"),
    ("Rachel",      "Schmidt",             "tra"),
    ("Reegan",      "Laidlaw",             "tra"),
]

wagc_team = [
    ("Anya",        "Crocker",             "tra"),
    ("Emma",        "Tindale",             "tum"),
    ("Ethan",       "Strickland",          "dmt"),
    ("Flynn",       "Gunther",             "tra"),
    ("Jack",        "West",                "dmt"),
    ("Jack",        "West",                "tra"),
    ("Jake",        "Macken",              "dmt"),
    ("Jake",        "Macken",              "tra"),
    ("Lach",        "Kirk",                "dmt"),
    ("Lach",        "Kirk",                "tra"),
    ("Lauren",      "Sheere",              "tra"),
    ("Lily",        "Arnold",              "dmt"),
    ("Lily",        "Arnold",              "tra"),
    ("Lily",        "Arnold",              "tum"),
    ("Luci",        "Unkovich",            "dmt"),
    ("Luci",        "Unkovich",            "tra"),
    ("Mitch",       "Unkovich",            "dmt"),
    ("Nathan",      "Davies",              "dmt"),
    ("Nathan",      "Davies",              "tra"),
    ("Nathan",      "Monkton",             "dmt"),
    ("Nathan",      "Monkton",             "tra"),
    ("Roman",       "McEvedy",             "dmt"),
    ("Roman",       "McEvedy",             "tra"),
    ("Seb",         "Smith",               "dmt"),
    ("Seb",         "Smith",               "tra"),
    ("Sienna",      "French",              "tra"),
    ("Tim",         "Unkovich",            "dmt"),
    ("Tim",         "Unkovich",            "tra"),
]

ice_team = [
    ("Alexandra",   "Watson",              "tra"),
    ("Braida",      "Thomas",              "tra"),
    ("Bron",        "Dibb",                "tra"),
    ("Cam",         "Robertson",           "tra"),
    ("Hannah",      "van Schalkwyk",       "tra"),
    ("Lach",        "Kirk",                "tra"),
    ("Lucy",        "Lucas",               "tra"),
    ("Nic",         "Cox",                 "tra"),

    ("Alexandra",   "Watson",              "dmt"),
    ("Braida",      "Thomas",              "dmt"),
    ("Bron",        "Dibb",                "dmt"),
    ("Cam",         "Robertson",           "dmt"),
    ("Hannah",      "van Schalkwyk",       "dmt"),
    ("Lach",        "Kirk",                "dmt"),
    ("Lucy",        "Lucas",               "dmt"),
    ("Nic",         "Cox",                 "dmt"),
]

worlds = [
    ("Federico",    "CURY",                "dmt"),
    ("Matias",      "PACHECO",             "dmt"),
    ("Matthew",     "FRENCH",              "dmt"),
    ("Troy",        "SITKOWSKI",           "dmt"),
    ("Cameron",     "TIDD",                "dmt"),
    ("Benjamin",    "BROWN",               "dmt"),
    ("Brent",       "DEKLERCK",            "dmt"),
    ("Wannes",      "GEENS",               "dmt"),
    ("Zachary",     "BLAKELY",             "dmt"),
    ("Ryan",        "SHEEHAN",             "dmt"),
    ("Kieran",      "LUPISH",              "dmt"),
    ("Gavin",       "DODD",                "dmt"),
    ("Carlos",      "DEL SER",             "dmt"),
    ("Nicolas",     "TORIBIO",             "dmt"),
    ("David",       "FRANCO",              "dmt"),
    ("Andres",      "MARTINEZ",            "dmt"),
    ("Omo",         "AIKEREMIOKHA",        "dmt"),
    ("Marshall",    "FROST",               "dmt"),
    ("Daniel",      "BERRIDGE",            "dmt"),
    ("Lewis",       "GOSLING",             "dmt"),
    ("Daniel",      "SCHMIDT",             "dmt"),
    ("Hannes",      "KOENIG",              "dmt"),
    ("Simon",       "DOBLER",              "dmt"),
    ("Moritz",      "BRAIG",               "dmt"),
    ("Stefanos",    "KAKOGIANNIS",         "dmt"),
    ("Nektarios",   "PAPADATOS",           "dmt"),
    ("Ioannis",     "PAPADATOS",           "dmt"),
    ("Apostolos",   "PAPADATOS",           "dmt"),
    ("Kaoru",       "KONDO",               "dmt"),
    ("Santiago",    "GONZALEZ",            "dmt"),
    ("Ian",         "ZERMENO",             "dmt"),
    ("Guitho",      "DE WOLFF",            "dmt"),
    ("Campbell",    "ROBERTSON",           "dmt"),
    ("Diogo",       "FERNANDES",           "dmt"),
    ("Tiago",       "SAMPAIO ROMAO",       "dmt"),
    ("Diogo",       "CABRAL",              "dmt"),
    ("Joao",        "FELIX",               "dmt"),
    ("Jean-Claude", "ROUX",                "dmt"),
    ("Matthew",     "BOSCH",               "dmt"),
    ("Jordan",      "BOOYSEN",             "dmt"),
    ("Artur",       "TROYAN",              "dmt"),
    ("Ruben",       "PADILLA",             "dmt"),
    ("Simon",       "SMITH",               "dmt"),
    ("Tomas",       "MINC",                "dmt"),
    ("Dylan",       "KLINE",               "dmt"),
    ("Rosalie",     "THONGPHAY",           "dmt"),
    ("Amber",       "FRENCH",              "dmt"),
    ("Kayla",       "NEL",                 "dmt"),
    ("Braida",      "THOMAS",              "dmt"),
    ("Cheyanna",    "ROBINSON",            "dmt"),
    ("Roos",        "BAL",                 "dmt"),
    ("Lise",        "DOORAKKERS",          "dmt"),
    ("Hannah",      "METHERAL",            "dmt"),
    ("Kalena",      "SOEHN",               "dmt"),
    ("Gabriella",   "FLYNN",               "dmt"),
    ("Celia",       "PROBE",               "dmt"),
    ("Carmen",      "ZARZUELA",            "dmt"),
    ("Marta",       "LOPEZ",               "dmt"),
    ("Alejandra",   "BRANA",               "dmt"),
    ("Melania",     "RODRIGUEZ",           "dmt"),
    ("Molly",       "MCKENNA",             "dmt"),
    ("Bethany",     "WILLIAMSON",          "dmt"),
    ("Kirsty",      "WAY",                 "dmt"),
    ("Ruth",        "SHEVELAN",            "dmt"),
    ("Sara",        "KELLER",              "dmt"),
    ("Anastasia",   "HEINRICH",            "dmt"),
    ("Antonia",     "QUINDEL",             "dmt"),
    ("Imani",       "SAPRAUTZKI",          "dmt"),
    ("Tsampika",    "KALEGKA",             "dmt"),
    ("Ayumi",       "SATO",                "dmt"),
    ("Veronica",    "SOTO",                "dmt"),
    ("Bronwyn",     "DIBB",                "dmt"),
    ("Melissa",     "ROMERIL",             "dmt"),
    ("Alexandra",   "GARCIA",              "dmt"),
    ("Rita",        "ABRANTES",            "dmt"),
    ("Diana",       "GAGO",                "dmt"),
    ("Sara",        "GUIDO",               "dmt"),
    ("Lenita",      "KOTZE",               "dmt"),
    ("Leolin",      "PETERSEN",            "dmt"),
    ("Tuva",        "STJAERNBORG",         "dmt"),
    ("Shelby",      "NOBUHARA",            "dmt"),
    ("Grace",       "HARDER",              "dmt"),
    ("Aliah",       "RAGA",                "dmt"),
    ("Jacqueline",  "KENT",                "dmt"),
]


olympicfinal = [
    ("ALBUQUERQUE", "Gabriel",             "tra"),
    ("Gabriel",     "ALBUQUERQUE",         "tra"),
    ("Allan",       "MORANTE",             "tra"),
    ("Андрей",      "Буйлов",              "tra"),
    ("Benni",       "Wizani",              "tra"),
    ("Benny",       "WIZANI",              "tra"),
    ("Ivan",        "LITVINOVICH",         "tra"),
    ("Иван",        "Литвинович",          "tra"),
    ("Langyu",      "YAN",                 "tra"),
    ("Longyu",      "HE",                  "tra"),
    ("Ryusei",      "NISHIOKA",            "tra"),
    ("隆成",        "西岡",                "tra"),
    ("Zak",         "PERZAMANOS",          "tra"),
    ("Zisai",       "WANG",                "tra"),
    ("Dylan",       "SCHMIDT",             "tra"),
]

aus_itt = [
    ("anika"     , "wood"           , "all") ,
    ("anna"      , "hewitt"         , "all") ,
    ("bella"     , "camp"           , "all") ,
    ("boone"     , "houghton"       , "all") ,
    ("boston"    , "kelly"          , "all") ,
    ("briana"    , "vivian"         , "all") ,
    ("brianna"   , "masterson"      , "all") ,
    ("bronwyn"   , "dibb"           , "all") ,
    ("cam"       , "robertson"      , "all") ,
    ("cleo"      , "pearce"         , "all") ,
    ("daniel"    , "teirney"        , "all") ,
    ("danielle"  , "ogden"          , "all") ,
    ("dylan"     , "schmidt"        , "all") ,
    ("ella"      , "howie"          , "all") ,
    ("emma"      , "robins"         , "all") ,
    ("emma"      , "tindale"        , "all") ,
    ("eras"      , "viljoen"        , "all") ,
    ("ethan"     , "rawson"         , "all") ,
    ("finleigh"  , "glanville"      , "all") ,
    ("finley"    , "smith"          , "all") ,
    ("flynn"     , "gunther"        , "all") ,
    ("francisca" , "marshall"       , "all") ,
    ("grace"     , "foster"         , "all") ,
    ("hannah"    , "schalkwyk"      , "all") ,
    ("he"        , "stefa"          , "all") ,
    ("holly"     , "unkovic"        , "all") ,
    ("isla"      , "wills"          , "all") ,
    ("jaeger"    , "pryce"          , "all") ,
    ("jake"      , "macken"         , "all") ,
    ("jakob"     , "anderson"       , "all") ,
    ("james"     , "dougal"         , "all") ,
    ("jamieson"  , "horst"          , "all") ,
    ("janko"     , "viljoen"        , "all") ,
    ("jess"      , "kalkhoven"      , "all") ,
    ("jon"       , "holman"         , "all") ,
    ("kate"      , "stables"        , "all") ,
    ("kieran"    , "john-francke"   , "all") ,
    ("kyrah"     , "johns"          , "all") ,
    ("lach"      , "kirk"           , "all") ,
    ("lana"      , "pilon"          , "all") ,
    ("lauren"    , "sheere"         , "all") ,
    ("liam"      , "evans"          , "all") ,
    ("liam"      , "quinn"          , "all") ,
    ("lisa"      , "howden"         , "all") ,
    ("luci"      , "unkovi"         , "all") ,
    ("lucy"      , "lucas"          , "all") ,
    ("lucy"      , "reynard"        , "all") ,
    ("mad"       , "davidson"       , "all") ,
    ("maia"      , "drabble"        , "all") ,
    ("marlowe"   , "ansley"         , "all") ,
    ("mason"     , "hall"           , "all") ,
    ("mason"     , "meszaros"       , "all") ,
    ("matthew"   , "teirney"        , "all") ,
    ("melissa"   , "romeril"        , "all") ,
    ("millie"    , "phillips"       , "all") ,
    ("nathan"    , "davies"         , "all") ,
    ("nathan"    , "monkton"        , "all") ,
    ("naya"      , "milnthorp"      , "all") ,
    ("nicola"    , "cox"            , "all") ,
    ("nikita"    , "jones"          , "all") ,
    ("noah"      , "peawini"        , "all") ,
    ("olivia"    , "teixeira"       , "all") ,
    ("rachel"    , "schmidt"        , "all") ,
    ("rada"      , "pazniak"        , "all") ,
    ("regan"     , "langford"       , "all") ,
    ("renee"     , "pilon"          , "all") ,
    ("riley"     , "gavin-crawford" , "all") ,
    ("roman"     , "mcevedy"        , "all") ,
    ("sean"      , "robinson"       , "all") ,
    ("sebastian" , "smith"          , "all") ,
    ("sienna"    , "french"         , "all") ,
    ("stefan"    , "stefanov"       , "all") ,
    ("sylvia"    , "humphreys"      , "all") ,
    ("tamara"    , "marcijasz"      , "all") ,
    ("thomas"    , "king"           , "all") ,
    ("tyron"     , "bradshaw"       , "all") ,
    ("zavier"    , "linstrom"       , "all") ,
]

#squad = national_squad
squad = aus_itt

for given_name, surname, discipline in squad:
    print(f"\n\n{given_name} {surname}")
    sys.stdout.flush()
    if discipline == "all":
        discipline = ["tra", "dmt", "tum"]
    for d in discipline:
        print(f"{d}:")
        sys.stdout.flush()
        command = f"./inspect_trasults.py --no_judge_summary --sort_by_date --{d} --given_name '{given_name}' --surname '{surname}' --since 2024-01-01"
        subprocess.run(command, shell=True)

