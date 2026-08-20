# datos.py

# --- BASE DE DATOS DE EDIFICIOS ---
edificios_db = {
    "Edificio Kavanagh": {"dir": "Florida 1065, Retiro", "alt": "120 m", "acc": "Principal / Cocheras", "coords": "-34.5922, -58.3753"},
    "Palacio Barolo": {"dir": "Av. de Mayo 1370, Monserrat", "alt": "100 m", "acc": "Principal / Carga", "coords": "-34.6095, -58.3860"},
    "Teatro Colón": {"dir": "Cerrito 628, San Nicolás", "alt": "30 m", "acc": "Libertad / Tucumán", "coords": "-34.6011, -58.3816"},
    "Congreso de la Nación": {"dir": "Av. Entre Ríos 50, Balvanera", "alt": "80 m", "acc": "Principal / Protocolar", "coords": "-34.6099, -58.3916"},
    "Casa Rosada": {"dir": "Balcarce 50, Monserrat", "alt": "24 m", "acc": "Balcarce 24 / Explanada", "coords": "-34.6081, -58.3702"},
    "Torre YPF": {"dir": "Macacha Güemes 515, Pto Madero", "alt": "160 m", "acc": "Dique 4", "coords": "-34.6031, -58.3639"},
    "Facultad de Derecho UBA": {"dir": "Av. Figueroa Alcorta 2263", "alt": "35 m", "acc": "Escalinata", "coords": "-34.5833, -58.3897"},
    "CCK": {"dir": "Sarmiento 151", "alt": "40 m", "acc": "Sarmiento / Alem", "coords": "-34.6044, -58.3694"},
    "Estación Retiro Mitre": {"dir": "Av. Dr. Ramos Mejía 1302", "alt": "30 m", "acc": "Hall Central", "coords": "-34.5903, -58.3742"},
    "Estación Constitución": {"dir": "Av. Brasil 1152", "alt": "30 m", "acc": "Hall Principal", "coords": "-34.6281, -58.3814"},
}

# --- BASE DE DATOS DE PUNTOS SEGUROS (HOSPITALES + COMISARÍAS + PFA) ---
puntos_seguros = {
    # Hospitales
    "Hosp. Alvarez": (-34.6190, -58.4610),
    "Hosp. Argerich": (-34.6366, -58.3639),
    "Hosp. Durand": (-34.6111, -58.4347),
    "Hosp. Fernández": (-34.5833, -58.4069),
    "Hosp. Grierson": (-34.6852, -58.4612),
    "Hosp. Penna": (-34.6432, -58.3912),
    "Hosp. Piñero": (-34.6432, -58.4412),
    "Hosp. Pirovano": (-34.5583, -58.4839),
    "Hosp. Ramos Mejía": (-34.6152, -58.4079),
    "Hosp. Rivadavia": (-34.5852, -58.3976),
    "Hosp. Santojanni": (-34.6531, -58.5134),
    "Hosp. Tornú": (-34.5856, -58.4812),
    "Hosp. Vélez Sarsfield": (-34.6291, -58.5089),
    "Hosp. Zubizarreta": (-34.5954, -58.5176),
    # Comisarías Comunales
    "Comisaría Comunal 1": (-34.5842, -58.3695),
    "Comisaría Comunal 2": (-34.5911, -58.3923),
    "Comisaría Comunal 3": (-34.6149, -58.3936),
    "Comisaría Comunal 4": (-34.6419, -58.4028),
    "Comisaría Comunal 5": (-34.6044, -58.4156),
    "Comisaría Comunal 6": (-34.6203, -58.4532),
    "Comisaría Comunal 7": (-34.6310, -58.4583),
    "Comisaría Comunal 8": (-34.6712, -58.4551),
    "Comisaría Comunal 9": (-34.6451, -58.5252),
    "Comisaría Comunal 10": (-34.6391, -58.4940),
    "Comisaría Comunal 11": (-34.6110, -58.4729),
    "Comisaría Comunal 12": (-34.5509, -58.4910),
    "Comisaría Comunal 13": (-34.5552, -58.4591),
    "Comisaría Comunal 14": (-34.5812, -58.4136),
    "Comisaría Comunal 15": (-34.5905, -58.4510),
    # PFA
    "PFA Depto. Central": (-34.6146, -58.3848),
    "PFA Inv. Federales": (-34.6135, -58.3912),
    "PFA Delitos Tecnológicos": (-34.5778, -58.4065),
    "PFA Bomberos Central": (-34.6045, -58.3810),
}
