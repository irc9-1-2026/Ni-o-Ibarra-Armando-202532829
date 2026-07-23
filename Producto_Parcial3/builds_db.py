import requests

import requests

# Diccionario de traducción de nombres en español a sus Slugs en la API (inglés)
WEAPON_SLUGS = {
    # Espadas 1H
    "clorofilo fulgurante": "light-of-foliar-incision",
    "cortador de jafe": "primordial-jade-cutter",
    "cortador de jade": "primordial-jade-cutter",
    "espina de hierro": "iron-sting",
    "espada negra": "the-black-sword",
    "reflejo de las tinieblas": "mistsplitter-reforged",
    "hoja afilada celestial": "skyward-blade",
    "espada de madera": "sapwood-blade",
    "espada de favonius": "favonius-sword",
    "espada del sacrificio": "sacrificial-sword",
    "amenoma kageuchi": "amenoma-kageuchi",
    
    # Lanzas
    "baculo de homa": "staff-of-homa",
    "luz del segador": "engulfing-lightning",
    "la captura": "the-catch",
    "lanza de favonius": "favonius-lance",
    "halcon de jade": "primordial-jade-winged-spear",
    
    # Arcos
    "alas celestiales": "skyward-harp",
    "elegia del fin": "elegy-for-the-end",
    "arco de favonius": "favonius-warbow",
    "masacradora de demonios": "hamayumi",
    
    # Mandobles
    "lapida del lobo": "wolfs-gravestone",
    "emblema del mar de juncos": "beacon-of-the-reed-sea",
    "sombra de la marea": "tidal-shadow",
    
    # Catalizadores
    "suenos milenarios": "a-thousand-floating-dreams",
    "axioma de la kagura": "kaguras-verity",
    "sinfonia de los cazadores": "the-widsith",
    "prototipo ambar": "prototype-amber",
}

def get_weapon_img_url(weapon_name):
    clean_key = weapon_name.strip().lower()
    
    # Si tenemos la traducción exacta a la API
    if clean_key in WEAPON_SLUGS:
        slug = WEAPON_SLUGS[clean_key]
        return f"https://genshin.jmp.blue/weapons/{slug}/icon"
    
    # Intento genérico formateado
    slug = (
        clean_key.replace(" ", "-")
        .replace("'", "")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )
    return f"https://genshin.jmp.blue/weapons/{slug}/icon"

def parse_armas(texto_armas):
    lista_armas = []
    if not texto_armas:
        return lista_armas
        
    for nombre in texto_armas.split("/"):
        nombre_clean = nombre.strip()
        if nombre_clean:
            lista_armas.append({
                "nombre": nombre_clean,
                "img": get_weapon_img_url(nombre_clean)
            })
    return lista_armas

# Base de datos global y exacta para personajes
PERSONAJES_EXACTOS = {
    # --- PYRO ---
    "amber": {
        "arma_5": "Alas Celestiales / Elegia del Fin", "arma_4": "Masacradora de Demonios / Arco de Favonius",
        "artefacto": "4x Rito Antiguo de la Nobleza / 4x Bruja Carmesí",
        "reloj": "ATQ%", "caliz": "Bono Daño Pyro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Maestría Elemental",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2 / C4"
    },
    "bennett": {
        "arma_5": "Hoja Afilada Celestial / Reflejo de las Tinieblas", "arma_4": "Espada de Madera / Espada de Favonius",
        "artefacto": "4x Rito Antiguo de la Nobleza",
        "reloj": "Recarga de Energía / Vida%", "caliz": "Vida%", "corona": "Bono Curación / Vida%",
        "substats": "Recarga de Energía (>200%) > Vida% > Vida Plana",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C1 / C5"
    },
    "xiangling": {
        "arma_5": "Luz del Segador / Baculo de Homa", "arma_4": "La Captura / Lanza de Favonius",
        "artefacto": "4x Emblema del Destino",
        "reloj": "Recarga de Energía / Maestría Elemental", "caliz": "Bono Daño Pyro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Recarga de Energía (>180%) > Prob. CRIT > Daño CRIT > Maestría",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C3 / C4"
    },
    "diluc": {
        "arma_5": "Lapida del Lobo / Emblema del Mar de Juncos", "arma_4": "Sombra de la Marea / Prototipo Arcaico",
        "artefacto": "4x Bruja Carmesí de las Llamas",
        "reloj": "ATQ% / Maestría Elemental", "caliz": "Bono Daño Pyro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Maestría",
        "talentos": "Básicos > Elemental (E) > Definitiva (Q)", "constelaciones": "C2 / C4"
    },
    "klee": {
        "arma_5": "Axioma de la Kagura / Oracion a los Vientos Perdidos", "arma_4": "Sinfonia de los Cazadores / Cuento de Dodoco",
        "artefacto": "4x Bruja Carmesí / 4x Reminiscencia",
        "reloj": "ATQ%", "caliz": "Bono Daño Pyro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Básicos > Elemental (E) > Definitiva (Q)", "constelaciones": "C2"
    },
    "hu-tao": {
        "arma_5": "Baculo de Homa", "arma_4": "Perdicion del Dragon / Balada de los Fiordos",
        "artefacto": "4x Bruja Carmesí / 4x Reminiscencia",
        "reloj": "Vida% / Maestría Elemental", "caliz": "Bono Daño Pyro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > Maestría > Vida%",
        "talentos": "Básicos (Cargados) > Elemental (E) > Definitiva (Q)", "constelaciones": "C1 / C2"
    },
    "yoimiya": {
        "arma_5": "Agitador del Trueno", "arma_4": "Masacradora de Demonios / Herrumbre",
        "artefacto": "4x Reminiscencia de la Purificación",
        "reloj": "ATQ% / Maestría", "caliz": "Bono Daño Pyro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Maestría",
        "talentos": "Básicos > Elemental (E) > Definitiva (Q)", "constelaciones": "C1 / C2"
    },
    "thoma": {
        "arma_5": "Luz del Segador", "arma_4": "Lanza de Favonius / Cruz de Kitain",
        "artefacto": "4x Flor Olvidada del Paraíso (Burgeon) / 4x Emblema",
        "reloj": "Recarga de Energía / Maestría", "caliz": "Vida% / Maestría", "corona": "Vida% / Maestría",
        "substats": "Recarga de Energía > Maestría > Vida%",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2 / C4 / C6"
    },
    "yanfei": {
        "arma_5": "Oracion a los Vientos Perdidos", "arma_4": "Sinfonia de los Cazadores / Ojo de la Percepcion",
        "artefacto": "4x Orquesta del Vagabundo / 4x Bruja Carmesí",
        "reloj": "ATQ% / Maestría", "caliz": "Bono Daño Pyro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Recarga",
        "talentos": "Básicos > Definitiva (Q) > Elemental (E)", "constelaciones": "C1 / C4"
    },
    "xinyan": {
        "arma_5": "Lapida del Lobo", "arma_4": "Gran Espada de Favonius / Sombra de la Marea",
        "artefacto": "4x Ritual del Gladiador / 4x Tenacidad",
        "reloj": "DEF% / ATQ%", "caliz": "Bono Daño Físico / DEF%", "corona": "Daño CRIT / DEF%",
        "substats": "DEF% > Daño CRIT > ATQ%",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2 / C4"
    },
    "dehya": {
        "arma_5": "Emblema del Mar de Juncos / Baculo de Homa", "arma_4": "Espada de Favonius / Fierro de Flor Marina",
        "artefacto": "4x Vourukasha's Glow / 4x Emblema",
        "reloj": "Vida% / ATQ% / Recarga", "caliz": "Bono Daño Pyro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > Vida% > Recarga",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C2"
    },
    "lyney": {
        "arma_5": "Gran Magia / Alas Celestiales", "arma_4": "Arco del Penasco Oscuro / Masacradora",
        "artefacto": "4x Cazador de Sombras",
        "reloj": "ATQ%", "caliz": "Bono Daño Pyro", "corona": "Daño CRIT / Prob. CRIT",
        "substats": "Daño CRIT > Prob. CRIT > ATQ%",
        "talentos": "Básicos > Elemental (E) > Definitiva (Q)", "constelaciones": "C1 / C2"
    },
    "gaming": {
        "arma_5": "Emblema del Mar de Juncos / Lapida del Lobo", "arma_4": "Superespada de Hierro / Gran Espada del Sacrificio",
        "artefacto": "4x Cazador de Sombras / 4x Bruja Carmesí",
        "reloj": "ATQ% / Maestría", "caliz": "Bono Daño Pyro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > Maestría > Recarga",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C6"
    },
    "arlecchino": {
        "arma_5": "Semblante de la Luna Roja / Baculo de Homa", "arma_4": "Balada de los Fiordos / Borla Blanca",
        "artefacto": "4x Fragmento de Armonía Fantasiosa / 4x Gladiador",
        "reloj": "ATQ%", "caliz": "Bono Daño Pyro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Maestría",
        "talentos": "Básicos > Elemental (E) > Definitiva (Q)", "constelaciones": "C1 / C2"
    },

    # --- HYDRO ---
    "barbara": {
        "arma_5": "Suenos Milenarios", "arma_4": "Cuento de Cazadores de Dragones / Prototipo Ambar",
        "artefacto": "4x Perla Oceánica / 4x Doncella Amada",
        "reloj": "Vida%", "caliz": "Vida%", "corona": "Bono Curación / Vida%",
        "substats": "Vida% > Recarga de Energía > Vida Plana",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2 / C6"
    },
    "xingqiu": {
        "arma_5": "Cortador de Jafe / Reflejo de las Tinieblas", "arma_4": "Espada del Sacrificio / Espada de Favonius",
        "artefacto": "4x Emblema del Destino",
        "reloj": "ATQ% / Recarga", "caliz": "Bono Daño Hydro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Recarga (>180%) > Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2 / C6"
    },
    "mona": {
        "arma_5": "Axioma de la Kagura", "arma_4": "Codice de Favonius / Sinfonia de los Cazadores",
        "artefacto": "4x Emblema del Destino / 4x Rito Antiguo",
        "reloj": "Recarga de Energía", "caliz": "Bono Daño Hydro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Recarga > Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C1 / C4"
    },
    "childe": {
        "arma_5": "Estrella Polar / Alas Celestiales", "arma_4": "Cazador del Callejon / Masacradora",
        "artefacto": "4x Sueño de la Nymph / 4x Corazón de las Profundidades",
        "reloj": "ATQ%", "caliz": "Bono Daño Hydro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Maestría",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C3"
    },
    "kokomi": {
        "arma_5": "Luz del Enredo / Luna Inalterable", "arma_4": "Prototipo Ambar / Cazadores de Dragones",
        "artefacto": "4x Perla Oceánica / 4x Tenacidad",
        "reloj": "Vida%", "caliz": "Bono Daño Hydro / Vida%", "corona": "Bono Curación",
        "substats": "Vida% > Recarga de Energía > Vida Plana",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1"
    },
    "ayato": {
        "arma_5": "Luz de la Cortadura / Haran Geppaku Futsu", "arma_4": "Espada Negra / Amenoma Kageuchi",
        "artefacto": "4x Eco del Ofrenda / 4x Corazón de las Profundidades",
        "reloj": "ATQ%", "caliz": "Bono Daño Hydro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Recarga",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2 / C3"
    },
    "yelan": {
        "arma_5": "Simulacro de Agua / Elegia del Fin", "arma_4": "Arco de Favonius / Arco del Sacrificio",
        "artefacto": "4x Emblema del Destino",
        "reloj": "Recarga / Vida%", "caliz": "Bono Daño Hydro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Recarga (>180%) > Prob. CRIT > Daño CRIT > Vida%",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C1 / C2"
    },
    "nilou": {
        "arma_5": "Llave de la Coronacion", "arma_4": "Espada de Madera / Espada del Sacrificio",
        "artefacto": "2x Vourukasha + 2x Tenacidad (Vida +20% / +20%)",
        "reloj": "Vida%", "caliz": "Vida%", "corona": "Vida%",
        "substats": "Vida% > Vida Plana > Maestría > Recarga",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2"
    },
    "candace": {
        "arma_5": "Lanza de Favonius", "arma_4": "Lanza de Favonius / Borla Negra",
        "artefacto": "4x Rito Antiguo / 2x Vida 2x Recarga",
        "reloj": "Recarga / Vida%", "caliz": "Vida%", "corona": "Vida%",
        "substats": "Vida% > Recarga > Prob. CRIT",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2 / C6"
    },
    "neuvillette": {
        "arma_5": "Rito del Flujo Eterno", "arma_4": "Prototipo Ambar / Sacrificio Jade",
        "artefacto": "4x Cazador de Sombras",
        "reloj": "Vida%", "caliz": "Bono Daño Hydro / Vida%", "corona": "Daño CRIT / Prob. CRIT",
        "substats": "Daño CRIT > Prob. CRIT > Vida% > Recarga",
        "talentos": "Básicos (Cargado) > Definitiva (Q) > Elemental (E)", "constelaciones": "C1 / C2"
    },
    "furina": {
        "arma_5": "Fulgor de las Aguas Calmas", "arma_4": "Vado del Rio Ceniciento / Favonius",
        "artefacto": "4x Compañía Dorada",
        "reloj": "Vida% / Recarga", "caliz": "Bono Hydro / Vida%", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Recarga > Vida% > Prob. CRIT > Daño CRIT",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C2"
    },
    "sigewinne": {
        "arma_5": "Balsamo del Silencio", "arma_4": "Arco de Favonius / Recurvo",
        "artefacto": "4x Cantos de Días Pasados / 2x Vida +20% +20%",
        "reloj": "Vida%", "caliz": "Vida%", "corona": "Vida% / Bono Curación",
        "substats": "Vida% > Recarga > Vida Plana",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C2"
    },

    # --- ELECTRO ---
    "lisa": {
        "arma_5": "Axioma de la Kagura", "arma_4": "Sinfonia de los Cazadores / Favonius",
        "artefacto": "4x Furia del Trueno / 4x Emblema",
        "reloj": "ATQ% / Maestría", "caliz": "Bono Electro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > Maestría > Recarga",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C4 / C6"
    },
    "razor": {
        "arma_5": "Lapida del Lobo", "arma_4": "Prototipo Arcaico / Sombra de la Marea",
        "artefacto": "4x Llamas Pálidas",
        "reloj": "ATQ%", "caliz": "Bono Daño Físico", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Básicos > Elemental (E) > Definitiva (Q)", "constelaciones": "C4"
    },
    "fischl": {
        "arma_5": "Estrella Polar / Alas Celestiales", "arma_4": "Cazador del Callejon / Ultimo Acorde",
        "artefacto": "4x Compañía Dorada",
        "reloj": "ATQ% / Maestría", "caliz": "Bono Electro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Maestría",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C6"
    },
    "beidou": {
        "arma_5": "Lapida del Lobo", "arma_4": "Rey de los Mares / Favonius",
        "artefacto": "4x Emblema del Destino",
        "reloj": "Recarga / ATQ%", "caliz": "Bono Electro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Recarga (>180%) > Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2"
    },
    "keqing": {
        "arma_5": "Reflejo de las Tinieblas / Cortador de Jafe", "arma_4": "Espada Negra / Lions Roar",
        "artefacto": "4x Furia del Trueno",
        "reloj": "ATQ% / Maestría", "caliz": "Bono Electro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Maestría",
        "talentos": "Básicos > Elemental (E) > Definitiva (Q)", "constelaciones": "C4 / C6"
    },
    "raiden": {
        "arma_5": "Luz del Segador", "arma_4": "La Captura / Lanza de Favonius",
        "artefacto": "4x Emblema del Destino",
        "reloj": "Recarga / ATQ%", "caliz": "Bono Electro / ATQ%", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Recarga (>250%) > Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2 / C3"
    },
    "sara": {
        "arma_5": "Alas Celestiales / Elegia del Fin", "arma_4": "Arco del Sacrificio / Favonius",
        "artefacto": "4x Emblema del Destino",
        "reloj": "Recarga / ATQ%", "caliz": "Bono Electro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Recarga > Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2 / C6"
    },
    "shinobu": {
        "arma_5": "Juramento de la Libertad", "arma_4": "Espinegra / Espada de Hierro Oscuro",
        "artefacto": "4x Flor Olvidada del Paraíso / 4x Sueños Áureos",
        "reloj": "Maestría Elemental", "caliz": "Maestría Elemental", "corona": "Maestría Elemental",
        "substats": "Maestría > Vida% > Recarga",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2"
    },
    "yae-miko": {
        "arma_5": "Axioma de la Kagura", "arma_4": "Sinfonia de los Cazadores / Solar Pearl",
        "artefacto": "4x Compañía Dorada / 4x Sueños Áureos",
        "reloj": "ATQ% / Maestría", "caliz": "Bono Electro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Maestría",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2"
    },
    "cyno": {
        "arma_5": "Baculo de las Arenas Escarlatas", "arma_4": "Balada de los Fiordos / Borla Blanca",
        "artefacto": "4x Sueños Áureos / 4x Furia del Trueno",
        "reloj": "Maestría / ATQ%", "caliz": "Bono Electro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > Maestría > ATQ%",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2"
    },
    "dori": {
        "arma_5": "Orgullo Celestial", "arma_4": "Gran Espada del Sacrificio / Favonius",
        "artefacto": "4x Rito Antiguo / 4x Perla Oceánica",
        "reloj": "Recarga / Vida%", "caliz": "Vida%", "corona": "Bono Curación / Vida%",
        "substats": "Recarga > Vida% > Vida Plana",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2 / C4"
    },
    "clorinde": {
        "arma_5": "Expiacion / Reflejo de las Tinieblas", "arma_4": "Final de las Profundidades / Espada Negra",
        "artefacto": "4x Fragmento de Armonía Fantasiosa / 4x Furia del Trueno",
        "reloj": "ATQ%", "caliz": "Bono Electro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Recarga",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C2"
    },
    "sethos": {
        "arma_5": "Cazador del Callejon", "arma_4": "Flor de Ibis / Scion of the Sun",
        "artefacto": "4x Orquesta del Vagabundo / 4x Sueños Áureos",
        "reloj": "Maestría Elemental", "caliz": "Bono Electro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Maestría > Prob. CRIT > Daño CRIT > Recarga",
        "talentos": "Básicos > Definitiva (Q) > Elemental (E)", "constelaciones": "C2 / C6"
    },

    # --- CRYO ---
    "kaeya": {
        "arma_5": "Reflejo de las Tinieblas", "arma_4": "Amenoma Kageuchi / Favonius",
        "artefacto": "4x Nómada del Invierno / 4x Emblema",
        "reloj": "ATQ% / Recarga", "caliz": "Bono Cryo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Recarga",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2 / C6"
    },
    "chongyun": {
        "arma_5": "Lapida del Lobo", "arma_4": "Gran Espada del Sacrificio / Akuoumaru",
        "artefacto": "4x Rito Antiguo / 4x Bruja (Melt)",
        "reloj": "ATQ% / Maestría", "caliz": "Bono Cryo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Maestría",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2 / C6"
    },
    "diona": {
        "arma_5": "Elegia del Fin", "arma_4": "Arco del Sacrificio / Favonius",
        "artefacto": "4x Rito Antiguo / 4x Tenacidad",
        "reloj": "Recarga / Vida%", "caliz": "Vida%", "corona": "Vida% / Bono Curación",
        "substats": "Recarga > Vida% > Vida Plana",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2 / C6"
    },
    "ganyu": {
        "arma_5": "Arco de Amos / Alas Celestiales", "arma_4": "Masacradora de Demonios / Protagonista",
        "artefacto": "4x Orquesta del Vagabundo / 4x Nómada del Invierno",
        "reloj": "ATQ% / Maestría", "caliz": "Bono Cryo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Maestría",
        "talentos": "Básicos > Definitiva (Q) > Elemental (E)", "constelaciones": "C1 / C6"
    },
    "qiqi": {
        "arma_5": "Afilada Celestial", "arma_4": "Espada del Sacrificio / Favonius",
        "artefacto": "4x Perla Oceánica",
        "reloj": "ATQ% / Recarga", "caliz": "ATQ%", "corona": "Bono Curación / ATQ%",
        "substats": "Recarga > ATQ% > Vida Plana",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C6"
    },
    "rosaria": {
        "arma_5": "Halcon de Jade", "arma_4": "Lanza de Favonius / La Captura",
        "artefacto": "4x Emblema / 4x Rito Antiguo",
        "reloj": "ATQ% / Recarga", "caliz": "Bono Cryo", "corona": "Prob. CRIT",
        "substats": "Prob. CRIT (>70%) > Daño CRIT > ATQ% > Recarga",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2 / C6"
    },
    "eula": {
        "arma_5": "Oda de los Pinos / Lapida del Lobo", "arma_4": "Sombra de la Marea / Rey de los Mares",
        "artefacto": "4x Llamas Pálidas",
        "reloj": "ATQ%", "caliz": "Bono Daño Físico", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Recarga",
        "talentos": "Básicos > Definitiva (Q) > Elemental (E)", "constelaciones": "C1 / C6"
    },
    "ayaka": {
        "arma_5": "Reflejo de las Tinieblas", "arma_4": "Amenoma Kageuchi / Espada Fluvial",
        "artefacto": "4x Nómada del Invierno",
        "reloj": "ATQ%", "caliz": "Bono Cryo", "corona": "Daño CRIT",
        "substats": "Daño CRIT > ATQ% > Prob. CRIT (15-30%) > Recarga",
        "talentos": "Definitiva (Q) > Básicos > Elemental (E)", "constelaciones": "C2 / C4"
    },
    "shenhe": {
        "arma_5": "Luz del Segador / Baculo de Homa", "arma_4": "Lanza de Favonius / Lanza de Caza",
        "artefacto": "2x ATQ +18% + 2x ATQ +18% / 4x Rito Antiguo",
        "reloj": "ATQ% / Recarga", "caliz": "ATQ%", "corona": "ATQ%",
        "substats": "ATQ% > Recarga > Prob. CRIT",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C2"
    },
    "layla": {
        "arma_5": "Llave de la Coronacion", "arma_4": "Espada de Favonius / Sacrificio",
        "artefacto": "4x Tenacidad de la Geoarmada",
        "reloj": "Vida%", "caliz": "Vida%", "corona": "Vida%",
        "substats": "Vida% > Recarga > Prob. CRIT",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2 / C4"
    },
    "mika": {
        "arma_5": "Lanza de Favonius", "arma_4": "Lanza de Favonius / Borla Negra",
        "artefacto": "4x Rito Antiguo / 4x Perla Oceánica",
        "reloj": "Recarga / Vida%", "caliz": "Vida%", "corona": "Bono Curación / Vida%",
        "substats": "Recarga > Vida% > Prob. CRIT",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2 / C6"
    },
    "freminet": {
        "arma_5": "Oda de los Pinos", "arma_4": "Sombra de la Marea / Prototipo",
        "artefacto": "4x Llamas Pálidas",
        "reloj": "ATQ%", "caliz": "Bono Físico / Bono Cryo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Elemental (E) > Básicos > Definitiva (Q)", "constelaciones": "C4 / C6"
    },
    "wriothesley": {
        "arma_5": "Supervision de Flujo / Kagura", "arma_4": "Sinfonia de los Cazadores / Sacrificio Jade",
        "artefacto": "4x Cazador de Sombras",
        "reloj": "ATQ% / Maestría", "caliz": "Bono Cryo", "corona": "Daño CRIT / Prob. CRIT",
        "substats": "Daño CRIT > Prob. CRIT > ATQ% > Maestría",
        "talentos": "Básicos > Elemental (E) > Definitiva (Q)", "constelaciones": "C1 / C2"
    },
    "charlotte": {
        "arma_5": "Axioma de la Kagura", "arma_4": "Codice de Favonius / Ojo del Juramento",
        "artefacto": "4x Rito Antiguo / 4x Perla Oceánica",
        "reloj": "Recarga / ATQ%", "caliz": "ATQ%", "corona": "Bono Curación / ATQ%",
        "substats": "Recarga > ATQ% > Prob. CRIT",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C1 / C4"
    },

    # --- ANEMO ---
    "venti": {
        "arma_5": "Elegia del Fin", "arma_4": "Ultimo Acorde / Arco de Favonius",
        "artefacto": "4x Sombra del Verde Esmeralda",
        "reloj": "Maestría / ATQ%", "caliz": "Maestría / Bono Anemo", "corona": "Maestría / Prob. CRIT",
        "substats": "Maestría > Recarga > Prob. CRIT > Daño CRIT",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2 / C6"
    },
    "sucrose": {
        "arma_5": "Suenos Milenarios", "arma_4": "Memorias de Sacrificio / Favonius",
        "artefacto": "4x Sombra del Verde Esmeralda",
        "reloj": "Maestría", "caliz": "Maestría", "corona": "Maestría",
        "substats": "Maestría > Recarga de Energía",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C6"
    },
    "xiao": {
        "arma_5": "Halcon de Jade / Baculo de Homa", "arma_4": "Lanza del Duelo / Penasco Oscuro",
        "artefacto": "4x Deceso del Cinabrio / 4x Cazador de Sombras",
        "reloj": "ATQ%", "caliz": "Bono Anemo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Recarga",
        "talentos": "Básicos > Definitiva (Q) > Elemental (E)", "constelaciones": "C1 / C6"
    },
    "kazuha": {
        "arma_5": "Juramento de la Libertad", "arma_4": "Espada de Favonius / Espada de Hierro Oscuro",
        "artefacto": "4x Sombra del Verde Esmeralda",
        "reloj": "Maestría", "caliz": "Maestría", "corona": "Maestría",
        "substats": "Maestría > Recarga (>160%) > Prob. CRIT",
        "talentos": "Elemental (E) = Definitiva (Q) > Básicos", "constelaciones": "C1 / C2"
    },
    "sayu": {
        "arma_5": "Lapida del Lobo", "arma_4": "Gran Espada de Favonius / Sacrificio",
        "artefacto": "4x Sombra del Verde Esmeralda",
        "reloj": "Recarga / Maestría", "caliz": "Maestría / ATQ%", "corona": "Maestría / Bono Curación",
        "substats": "Maestría > Recarga > ATQ%",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C1 / C6"
    },
    "heizou": {
        "arma_5": "Axioma de la Kagura", "arma_4": "Sinfonia de los Cazadores / Sacrificio",
        "artefacto": "4x Sombra del Verde Esmeralda / 4x Gladiador",
        "reloj": "ATQ%", "caliz": "Bono Anemo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Maestría",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C6"
    },
    "faruzan": {
        "arma_5": "Elegia del Fin", "arma_4": "Arco de Favonius / Sacrificio",
        "artefacto": "4x Tenacidad / 4x Emblema",
        "reloj": "Recarga de Energía", "caliz": "Bono Anemo", "corona": "Prob. CRIT",
        "substats": "Recarga (>250% sin C6) > Prob. CRIT > ATQ%",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C6"
    },
    "wanderer": {
        "arma_5": "Reminiscencia de Tulaytullah", "arma_4": "Sinfonia de los Cazadores / Perla Solar",
        "artefacto": "4x Épica del Pabellón del Desierto",
        "reloj": "ATQ%", "caliz": "Bono Anemo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Básicos > Elemental (E) > Definitiva (Q)", "constelaciones": "C2 / C6"
    },
    "lynette": {
        "arma_5": "Cortador de Jafe", "arma_4": "Espada de Favonius / Sacrificio",
        "artefacto": "4x Sombra del Verde Esmeralda",
        "reloj": "Recarga / ATQ%", "caliz": "Bono Anemo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Recarga > Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C1 / C6"
    },
    "xianyun": {
        "arma_5": "Llamada del Grullal", "arma_4": "Ojo del Juramento / Codice de Favonius",
        "artefacto": "4x Sombra del Verde Esmeralda / 4x Cantos de Días Pasados",
        "reloj": "ATQ% / Recarga", "caliz": "ATQ%", "corona": "ATQ% / Bono Curación",
        "substats": "ATQ% > Recarga > Prob. CRIT",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C1 / C2"
    },

    # --- GEO ---
    "noelle": {
        "arma_5": "Cornamusa de la Marea / Redención", "arma_4": "Sombra Blanca / Favonius",
        "artefacto": "4x Cáscara de Sueños Opulentos / 4x Cazador de Sombras",
        "reloj": "DEF%", "caliz": "Bono Geo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > DEF% > Recarga",
        "talentos": "Básicos > Definitiva (Q) > Elemental (E)", "constelaciones": "C6"
    },
    "ningguang": {
        "arma_5": "Oracion a los Vientos Perdidos", "arma_4": "Sinfonia de los Cazadores / Perla Solar",
        "artefacto": "2x Geo + 2x ATQ%",
        "reloj": "ATQ%", "caliz": "Bono Geo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Básicos > Definitiva (Q) > Elemental (E)", "constelaciones": "C2 / C6"
    },
    "albedo": {
        "arma_5": "Cortador de Jafe", "arma_4": "Huso de Cinabrio / Espada del Deseo",
        "artefacto": "4x Cáscara de Sueños Opulentos / 4x Compañía Dorada",
        "reloj": "DEF%", "caliz": "Bono Geo", "corona": "DEF% / Prob. CRIT",
        "substats": "DEF% > Prob. CRIT > Daño CRIT > Recarga",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2"
    },
    "zhongli": {
        "arma_5": "Halcon de Jade / Homa", "arma_4": "Borla Negra / Lanza de Favonius",
        "artefacto": "4x Tenacidad de la Geoarmada",
        "reloj": "Vida%", "caliz": "Vida% / Bono Geo", "corona": "Vida% / Prob. CRIT",
        "substats": "Vida% > Vida Plana > Prob. CRIT > Recarga",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C2"
    },
    "gorou": {
        "arma_5": "Elegia del Fin", "arma_4": "Arco de Favonius / Sacrificio",
        "artefacto": "4x Exiliado / 4x Cáscara",
        "reloj": "DEF% / Recarga", "caliz": "DEF%", "corona": "Prob. CRIT / DEF%",
        "substats": "Recarga > DEF% > Prob. CRIT",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C4 / C6"
    },
    "itto": {
        "arma_5": "Cornamusa de la Marea", "arma_4": "Sombra Blanca / Penasco Oscuro",
        "artefacto": "4x Cáscara de Sueños Opulentos",
        "reloj": "DEF%", "caliz": "Bono Geo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "DEF% > Prob. CRIT > Daño CRIT > Recarga",
        "talentos": "Básicos > Definitiva (Q) > Elemental (E)", "constelaciones": "C1 / C2 / C6"
    },
    "yunjin": {
        "arma_5": "Luz del Segador", "arma_4": "Lanza de Favonius",
        "artefacto": "4x Cáscara de Sueños Opulentos / 2x DEF 2x Recarga",
        "reloj": "DEF% / Recarga", "caliz": "DEF%", "corona": "DEF% / Prob. CRIT",
        "substats": "DEF% > Recarga > Prob. CRIT",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2 / C6"
    },
    "navia": {
        "arma_5": "Sentencia de las Sombras / Lapida del Lobo", "arma_4": "Gran Espada del Sacrificio / Favonius",
        "artefacto": "4x Murmullo del Bosque Sonoro / 4x Compañía Dorada",
        "reloj": "ATQ%", "caliz": "Bono Geo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > ATQ% > Recarga",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C2"
    },
    "chiori": {
        "arma_5": "Uraku Misugiri / Cortador de Jafe", "arma_4": "Huso de Cinabrio / Espada Fluvial",
        "artefacto": "4x Compañía Dorada / 4x Cáscara",
        "reloj": "DEF% / ATQ%", "caliz": "Bono Geo", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > DEF% > ATQ%",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C2"
    },

    # --- DENDRO ---
    "collei": {
        "arma_5": "Elegia del Fin", "arma_4": "Arco de Favonius / Sacrificio",
        "artefacto": "4x Recuerdos del Bosque",
        "reloj": "Recarga / ATQ%", "caliz": "Bono Dendro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Recarga > Prob. CRIT > Daño CRIT > Maestría",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C2 / C6"
    },
    "tighnari": {
        "arma_5": "Senda de la Cazadora / Alas Celestiales", "arma_4": "Protagonista / Ultimo Acorde",
        "artefacto": "4x Sueños Áureos / 4x Orquesta del Vagabundo",
        "reloj": "Maestría Elemental", "caliz": "Bono Dendro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Prob. CRIT > Daño CRIT > Maestría > ATQ%",
        "talentos": "Básicos > Definitiva (Q) > Elemental (E)", "constelaciones": "C1 / C2"
    },
    "nahida": {
        "arma_5": "Suenos Milenarios", "arma_4": "Memorias de Sacrificio / Estrella Errabunda",
        "artefacto": "4x Recuerdos del Bosque / 4x Sueños Áureos",
        "reloj": "Maestría Elemental", "caliz": "Maestría / Bono Dendro", "corona": "Maestría / Prob. CRIT",
        "substats": "Maestría (>800) > Prob. CRIT > Daño CRIT > Recarga",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2"
    },
    "alhaitham": {
        "arma_5": "Clorofilo Fulgurante / Cortador de Jafe", "arma_4": "Espina de Hierro / Espada Negra",
        "artefacto": "4x Sueños Áureos / 4x Recuerdos del Bosque",
        "reloj": "Maestría Elemental", "caliz": "Bono Dendro", "corona": "Prob. CRIT / Daño CRIT",
        "substats": "Maestría > Prob. CRIT > Daño CRIT > ATQ%",
        "talentos": "Elemental (E) > Básicos > Definitiva (Q)", "constelaciones": "C1 / C2"
    },
    "baizhu": {
        "arma_5": "Esplendor de las Profundidades", "arma_4": "Prototipo Ambar / Favonius",
        "artefacto": "4x Recuerdos del Bosque / 4x Perla Oceánica",
        "reloj": "Vida% / Recarga", "caliz": "Vida%", "corona": "Vida% / Bono Curación",
        "substats": "Vida% (>50k) > Recarga (>180%) > Vida Plana",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C2"
    },
    "kaveh": {
        "arma_5": "Orgullo Celestial", "arma_4": "Fierro de Flor Marina / Favonius",
        "artefacto": "4x Flor Olvidada del Paraíso / 4x Recuerdos del Bosque",
        "reloj": "Recarga / Maestría", "caliz": "Maestría", "corona": "Maestría",
        "substats": "Recarga > Maestría > Vida%",
        "talentos": "Definitiva (Q) > Elemental (E) > Básicos", "constelaciones": "C4 / C6"
    },
    "kirara": {
        "arma_5": "Llave de la Coronacion", "arma_4": "Espada de Madera / Favonius",
        "artefacto": "4x Recuerdos del Bosque / 2x Vida 2x Vida",
        "reloj": "Vida%", "caliz": "Vida%", "corona": "Vida%",
        "substats": "Vida% > Recarga > Vida Plana",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C2 / C6"
    },
    "yaoyao": {
        "arma_5": "Lanza de Favonius", "arma_4": "Lanza de Favonius / Cruz de Kitain",
        "artefacto": "4x Recuerdos del Bosque / 4x Tenacidad",
        "reloj": "Vida% / Recarga", "caliz": "Vida%", "corona": "Bono Curación / Vida%",
        "substats": "Vida% > Recarga > Maestría",
        "talentos": "Elemental (E) > Definitiva (Q) > Básicos", "constelaciones": "C1 / C2"
    }
}
def obtener_build(nombre_personaje):
    """
    Busca un personaje en el diccionario. 
    Limpia el texto para evitar problemas con mayúsculas, espacios o tildes.
    """
    if not nombre_personaje:
        return None
        
    # Limpiamos la búsqueda (ejemplo: "Hu Tao " -> "hu-tao")
    clean_name = (
        nombre_personaje.strip()
        .lower()
        .replace(" ", "-")
        .replace("'", "")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )
    
    # Obtenemos la data del personaje
    data = PERSONAJES_EXACTOS.get(clean_name)
    
    if data:
        # Hacemos una copia para no alterar el diccionario original
        build = data.copy()
        # Convertimos los strings de armas a listas estructuradas con sus imágenes
        build["arma_5_list"] = parse_armas(build.get("arma_5", ""))
        build["arma_4_list"] = parse_armas(build.get("arma_4", ""))
        return build
        
    return None