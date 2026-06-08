import asyncio

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import hash_password
from app.models import (
    Cliente,
    Deposito,
    Empleado,
    Pais,
    Persona,
    Seguro,
    Subastador,
)


PAISES = [
    {"numero": 1, "nombre": "Argentina", "nombre_corto": "ARG", "capital": "Buenos Aires", "nacionalidad": "argentino/a", "idiomas": "Español"},
    {"numero": 2, "nombre": "Afganistán", "nombre_corto": "AFG", "capital": "Kabul", "nacionalidad": "afgano/a", "idiomas": "Pastún, Darí"},
    {"numero": 3, "nombre": "Albania", "nombre_corto": "ALB", "capital": "Tirana", "nacionalidad": "albanés/a", "idiomas": "Albanés"},
    {"numero": 4, "nombre": "Alemania", "nombre_corto": "DEU", "capital": "Berlín", "nacionalidad": "alemán/a", "idiomas": "Alemán"},
    {"numero": 5, "nombre": "Andorra", "nombre_corto": "AND", "capital": "Andorra la Vieja", "nacionalidad": "andorrano/a", "idiomas": "Catalán"},
    {"numero": 6, "nombre": "Angola", "nombre_corto": "AGO", "capital": "Luanda", "nacionalidad": "angoleño/a", "idiomas": "Portugués"},
    {"numero": 7, "nombre": "Antigua y Barbuda", "nombre_corto": "ATG", "capital": "Saint John", "nacionalidad": "antiguano/a", "idiomas": "Inglés"},
    {"numero": 8, "nombre": "Arabia Saudita", "nombre_corto": "SAU", "capital": "Riad", "nacionalidad": "saudí", "idiomas": "Árabe"},
    {"numero": 9, "nombre": "Argelia", "nombre_corto": "DZA", "capital": "Argel", "nacionalidad": "argelino/a", "idiomas": "Árabe, Bereber"},
    {"numero": 10, "nombre": "Australia", "nombre_corto": "AUS", "capital": "Camberra", "nacionalidad": "australiano/a", "idiomas": "Inglés"},
    {"numero": 11, "nombre": "Austria", "nombre_corto": "AUT", "capital": "Viena", "nacionalidad": "austriaco/a", "idiomas": "Alemán"},
    {"numero": 12, "nombre": "Azerbaiyán", "nombre_corto": "AZE", "capital": "Bakú", "nacionalidad": "azerbaiyano/a", "idiomas": "Azerí"},
    {"numero": 13, "nombre": "Bahamas", "nombre_corto": "BHS", "capital": "Nasáu", "nacionalidad": "bahameño/a", "idiomas": "Inglés"},
    {"numero": 14, "nombre": "Bangladés", "nombre_corto": "BGD", "capital": "Daca", "nacionalidad": "bangladesí", "idiomas": "Bengalí"},
    {"numero": 15, "nombre": "Barbados", "nombre_corto": "BRB", "capital": "Bridgetown", "nacionalidad": "barbadense", "idiomas": "Inglés"},
    {"numero": 16, "nombre": "Baréin", "nombre_corto": "BHR", "capital": "Manama", "nacionalidad": "bareiní", "idiomas": "Árabe"},
    {"numero": 17, "nombre": "Bélgica", "nombre_corto": "BEL", "capital": "Bruselas", "nacionalidad": "belga", "idiomas": "Neerlandés, Francés, Alemán"},
    {"numero": 18, "nombre": "Belice", "nombre_corto": "BLZ", "capital": "Belmopán", "nacionalidad": "beliceño/a", "idiomas": "Inglés"},
    {"numero": 19, "nombre": "Benín", "nombre_corto": "BEN", "capital": "Porto Novo", "nacionalidad": "beninés/a", "idiomas": "Francés"},
    {"numero": 20, "nombre": "Bielorrusia", "nombre_corto": "BLR", "capital": "Minsk", "nacionalidad": "bielorruso/a", "idiomas": "Bielorruso, Ruso"},
    {"numero": 21, "nombre": "Bolivia", "nombre_corto": "BOL", "capital": "Sucre", "nacionalidad": "boliviano/a", "idiomas": "Español, Quechua, Aimara"},
    {"numero": 22, "nombre": "Bosnia y Herzegovina", "nombre_corto": "BIH", "capital": "Sarajevo", "nacionalidad": "bosnio/a", "idiomas": "Bosnio, Croata, Serbio"},
    {"numero": 23, "nombre": "Botsuana", "nombre_corto": "BWA", "capital": "Gaborone", "nacionalidad": "botsuano/a", "idiomas": "Inglés, Setsuana"},
    {"numero": 24, "nombre": "Brasil", "nombre_corto": "BRA", "capital": "Brasilia", "nacionalidad": "brasileño/a", "idiomas": "Portugués"},
    {"numero": 25, "nombre": "Brunéi", "nombre_corto": "BRN", "capital": "Bandar Seri Begawan", "nacionalidad": "bruneano/a", "idiomas": "Malayo"},
    {"numero": 26, "nombre": "Bulgaria", "nombre_corto": "BGR", "capital": "Sofía", "nacionalidad": "búlgaro/a", "idiomas": "Búlgaro"},
    {"numero": 27, "nombre": "Burkina Faso", "nombre_corto": "BFA", "capital": "Uagadugú", "nacionalidad": "burkinés/a", "idiomas": "Francés"},
    {"numero": 28, "nombre": "Burundi", "nombre_corto": "BDI", "capital": "Gitega", "nacionalidad": "burundés/a", "idiomas": "Kirundi, Francés"},
    {"numero": 29, "nombre": "Bután", "nombre_corto": "BTN", "capital": "Timbu", "nacionalidad": "butanés/a", "idiomas": "Dzongkha"},
    {"numero": 30, "nombre": "Cabo Verde", "nombre_corto": "CPV", "capital": "Praia", "nacionalidad": "caboverdiano/a", "idiomas": "Portugués"},
    {"numero": 31, "nombre": "Camboya", "nombre_corto": "KHM", "capital": "Nom Pen", "nacionalidad": "camboyano/a", "idiomas": "Jemer"},
    {"numero": 32, "nombre": "Camerún", "nombre_corto": "CMR", "capital": "Yaundé", "nacionalidad": "camerunés/a", "idiomas": "Francés, Inglés"},
    {"numero": 33, "nombre": "Canadá", "nombre_corto": "CAN", "capital": "Ottawa", "nacionalidad": "canadiense", "idiomas": "Inglés, Francés"},
    {"numero": 34, "nombre": "Catar", "nombre_corto": "QAT", "capital": "Doha", "nacionalidad": "catarí", "idiomas": "Árabe"},
    {"numero": 35, "nombre": "Chad", "nombre_corto": "TCD", "capital": "Yamena", "nacionalidad": "chadiano/a", "idiomas": "Francés, Árabe"},
    {"numero": 36, "nombre": "Chile", "nombre_corto": "CHL", "capital": "Santiago", "nacionalidad": "chileno/a", "idiomas": "Español"},
    {"numero": 37, "nombre": "China", "nombre_corto": "CHN", "capital": "Pekín", "nacionalidad": "chino/a", "idiomas": "Chino Mandarín"},
    {"numero": 38, "nombre": "Chipre", "nombre_corto": "CYP", "capital": "Nicosia", "nacionalidad": "chipriota", "idiomas": "Griego, Turco"},
    {"numero": 39, "nombre": "Colombia", "nombre_corto": "COL", "capital": "Bogotá", "nacionalidad": "colombiano/a", "idiomas": "Español"},
    {"numero": 40, "nombre": "Comoras", "nombre_corto": "COM", "capital": "Moroni", "nacionalidad": "comorense", "idiomas": "Comorense, Árabe, Francés"},
    {"numero": 41, "nombre": "Corea del Norte", "nombre_corto": "PRK", "capital": "Pionyang", "nacionalidad": "norcoreano/a", "idiomas": "Coreano"},
    {"numero": 42, "nombre": "Corea del Sur", "nombre_corto": "KOR", "capital": "Seúl", "nacionalidad": "surcoreano/a", "idiomas": "Coreano"},
    {"numero": 43, "nombre": "Costa de Marfil", "nombre_corto": "CIV", "capital": "Yamusukro", "nacionalidad": "marfileño/a", "idiomas": "Francés"},
    {"numero": 44, "nombre": "Costa Rica", "nombre_corto": "CRI", "capital": "San José", "nacionalidad": "costarricense", "idiomas": "Español"},
    {"numero": 45, "nombre": "Croacia", "nombre_corto": "HRV", "capital": "Zagreb", "nacionalidad": "croata", "idiomas": "Croata"},
    {"numero": 46, "nombre": "Cuba", "nombre_corto": "CUB", "capital": "La Habana", "nacionalidad": "cubano/a", "idiomas": "Español"},
    {"numero": 47, "nombre": "Dinamarca", "nombre_corto": "DNK", "capital": "Copenhague", "nacionalidad": "danés/a", "idiomas": "Danés"},
    {"numero": 48, "nombre": "Dominica", "nombre_corto": "DMA", "capital": "Roseau", "nacionalidad": "dominiqués/a", "idiomas": "Inglés"},
    {"numero": 49, "nombre": "Ecuador", "nombre_corto": "ECU", "capital": "Quito", "nacionalidad": "ecuatoriano/a", "idiomas": "Español"},
    {"numero": 50, "nombre": "Egipto", "nombre_corto": "EGY", "capital": "El Cairo", "nacionalidad": "egipcio/a", "idiomas": "Árabe"},
    {"numero": 51, "nombre": "El Salvador", "nombre_corto": "SLV", "capital": "San Salvador", "nacionalidad": "salvadoreño/a", "idiomas": "Español"},
    {"numero": 52, "nombre": "Emiratos Árabes Unidos", "nombre_corto": "ARE", "capital": "Abu Dabi", "nacionalidad": "emiratí", "idiomas": "Árabe"},
    {"numero": 53, "nombre": "Eritrea", "nombre_corto": "ERI", "capital": "Asmara", "nacionalidad": "eritreo/a", "idiomas": "Tigriña, Árabe, Inglés"},
    {"numero": 54, "nombre": "Eslovaquia", "nombre_corto": "SVK", "capital": "Bratislava", "nacionalidad": "eslovaco/a", "idiomas": "Eslovaco"},
    {"numero": 55, "nombre": "Eslovenia", "nombre_corto": "SVN", "capital": "Liubliana", "nacionalidad": "esloveno/a", "idiomas": "Esloveno"},
    {"numero": 56, "nombre": "España", "nombre_corto": "ESP", "capital": "Madrid", "nacionalidad": "español/a", "idiomas": "Español"},
    {"numero": 57, "nombre": "Estados Unidos", "nombre_corto": "USA", "capital": "Washington D.C.", "nacionalidad": "estadounidense", "idiomas": "Inglés"},
    {"numero": 58, "nombre": "Estonia", "nombre_corto": "EST", "capital": "Tallin", "nacionalidad": "estonio/a", "idiomas": "Estonio"},
    {"numero": 59, "nombre": "Esuatini", "nombre_corto": "SWZ", "capital": "Mbabane", "nacionalidad": "suazi", "idiomas": "Suazi, Inglés"},
    {"numero": 60, "nombre": "Etiopía", "nombre_corto": "ETH", "capital": "Adís Abeba", "nacionalidad": "etíope", "idiomas": "Amárico"},
    {"numero": 61, "nombre": "Filipinas", "nombre_corto": "PHL", "capital": "Manila", "nacionalidad": "filipino/a", "idiomas": "Filipino, Inglés"},
    {"numero": 62, "nombre": "Finlandia", "nombre_corto": "FIN", "capital": "Helsinki", "nacionalidad": "finlandés/a", "idiomas": "Finés, Sueco"},
    {"numero": 63, "nombre": "Fiyi", "nombre_corto": "FJI", "capital": "Suva", "nacionalidad": "fiyiano/a", "idiomas": "Inglés, Fiyiano, Hindi"},
    {"numero": 64, "nombre": "Francia", "nombre_corto": "FRA", "capital": "París", "nacionalidad": "francés/a", "idiomas": "Francés"},
    {"numero": 65, "nombre": "Gabón", "nombre_corto": "GAB", "capital": "Libreville", "nacionalidad": "gabonés/a", "idiomas": "Francés"},
    {"numero": 66, "nombre": "Gambia", "nombre_corto": "GMB", "capital": "Banjul", "nacionalidad": "gambiano/a", "idiomas": "Inglés"},
    {"numero": 67, "nombre": "Georgia", "nombre_corto": "GEO", "capital": "Tiflis", "nacionalidad": "georgiano/a", "idiomas": "Georgiano"},
    {"numero": 68, "nombre": "Ghana", "nombre_corto": "GHA", "capital": "Acra", "nacionalidad": "ghanés/a", "idiomas": "Inglés"},
    {"numero": 69, "nombre": "Granada", "nombre_corto": "GRD", "capital": "Saint George", "nacionalidad": "granadino/a", "idiomas": "Inglés"},
    {"numero": 70, "nombre": "Grecia", "nombre_corto": "GRC", "capital": "Atenas", "nacionalidad": "griego/a", "idiomas": "Griego"},
    {"numero": 71, "nombre": "Guatemala", "nombre_corto": "GTM", "capital": "Ciudad de Guatemala", "nacionalidad": "guatemalteco/a", "idiomas": "Español"},
    {"numero": 72, "nombre": "Guyana", "nombre_corto": "GUY", "capital": "Georgetown", "nacionalidad": "guyanés/a", "idiomas": "Inglés"},
    {"numero": 73, "nombre": "Guinea", "nombre_corto": "GIN", "capital": "Conakri", "nacionalidad": "guineano/a", "idiomas": "Francés"},
    {"numero": 74, "nombre": "Guinea-Bisáu", "nombre_corto": "GNB", "capital": "Bisáu", "nacionalidad": "guineano/a", "idiomas": "Portugués"},
    {"numero": 75, "nombre": "Guinea Ecuatorial", "nombre_corto": "GNQ", "capital": "Malabo", "nacionalidad": "ecuatoguineano/a", "idiomas": "Español, Francés, Portugués"},
    {"numero": 76, "nombre": "Haití", "nombre_corto": "HTI", "capital": "Puerto Príncipe", "nacionalidad": "haitiano/a", "idiomas": "Francés, Criollo haitiano"},
    {"numero": 77, "nombre": "Honduras", "nombre_corto": "HND", "capital": "Tegucigalpa", "nacionalidad": "hondureño/a", "idiomas": "Español"},
    {"numero": 78, "nombre": "Hungría", "nombre_corto": "HUN", "capital": "Budapest", "nacionalidad": "húngaro/a", "idiomas": "Húngaro"},
    {"numero": 79, "nombre": "India", "nombre_corto": "IND", "capital": "Nueva Delhi", "nacionalidad": "indio/a", "idiomas": "Hindi, Inglés"},
    {"numero": 80, "nombre": "Indonesia", "nombre_corto": "IDN", "capital": "Yakarta", "nacionalidad": "indonesio/a", "idiomas": "Indonesio"},
    {"numero": 81, "nombre": "Irak", "nombre_corto": "IRQ", "capital": "Bagdad", "nacionalidad": "iraquí", "idiomas": "Árabe, Kurdo"},
    {"numero": 82, "nombre": "Irán", "nombre_corto": "IRN", "capital": "Teherán", "nacionalidad": "iraní", "idiomas": "Persa"},
    {"numero": 83, "nombre": "Irlanda", "nombre_corto": "IRL", "capital": "Dublín", "nacionalidad": "irlandés/a", "idiomas": "Irlandés, Inglés"},
    {"numero": 84, "nombre": "Islandia", "nombre_corto": "ISL", "capital": "Reikiavik", "nacionalidad": "islandés/a", "idiomas": "Islandés"},
    {"numero": 85, "nombre": "Israel", "nombre_corto": "ISR", "capital": "Jerusalén", "nacionalidad": "israelí", "idiomas": "Hebreo, Árabe"},
    {"numero": 86, "nombre": "Italia", "nombre_corto": "ITA", "capital": "Roma", "nacionalidad": "italiano/a", "idiomas": "Italiano"},
    {"numero": 87, "nombre": "Jamaica", "nombre_corto": "JAM", "capital": "Kingston", "nacionalidad": "jamaiquino/a", "idiomas": "Inglés"},
    {"numero": 88, "nombre": "Japón", "nombre_corto": "JPN", "capital": "Tokio", "nacionalidad": "japonés/a", "idiomas": "Japonés"},
    {"numero": 89, "nombre": "Jordania", "nombre_corto": "JOR", "capital": "Amán", "nacionalidad": "jordano/a", "idiomas": "Árabe"},
    {"numero": 90, "nombre": "Kazajistán", "nombre_corto": "KAZ", "capital": "Astaná", "nacionalidad": "kazajo/a", "idiomas": "Kazajo, Ruso"},
    {"numero": 91, "nombre": "Kenia", "nombre_corto": "KEN", "capital": "Nairobi", "nacionalidad": "keniano/a", "idiomas": "Suajili, Inglés"},
    {"numero": 92, "nombre": "Kirguistán", "nombre_corto": "KGZ", "capital": "Biskek", "nacionalidad": "kirguís", "idiomas": "Kirguís, Ruso"},
    {"numero": 93, "nombre": "Kiribati", "nombre_corto": "KIR", "capital": "Tarawa Sur", "nacionalidad": "kiribatiano/a", "idiomas": "Inglés, Gilbertés"},
    {"numero": 94, "nombre": "Kuwait", "nombre_corto": "KWT", "capital": "Kuwait", "nacionalidad": "kuwaití", "idiomas": "Árabe"},
    {"numero": 95, "nombre": "Laos", "nombre_corto": "LAO", "capital": "Vientián", "nacionalidad": "laosiano/a", "idiomas": "Lao"},
    {"numero": 96, "nombre": "Lesoto", "nombre_corto": "LSO", "capital": "Maseru", "nacionalidad": "lesotense", "idiomas": "Sesoto, Inglés"},
    {"numero": 97, "nombre": "Letonia", "nombre_corto": "LVA", "capital": "Riga", "nacionalidad": "letón/a", "idiomas": "Letón"},
    {"numero": 98, "nombre": "Líbano", "nombre_corto": "LBN", "capital": "Beirut", "nacionalidad": "libanés/a", "idiomas": "Árabe"},
    {"numero": 99, "nombre": "Liberia", "nombre_corto": "LBR", "capital": "Monrovia", "nacionalidad": "liberiano/a", "idiomas": "Inglés"},
    {"numero": 100, "nombre": "Libia", "nombre_corto": "LBY", "capital": "Trípoli", "nacionalidad": "libio/a", "idiomas": "Árabe"},
    {"numero": 101, "nombre": "Liechtenstein", "nombre_corto": "LIE", "capital": "Vaduz", "nacionalidad": "liechtensteiniano/a", "idiomas": "Alemán"},
    {"numero": 102, "nombre": "Lituania", "nombre_corto": "LTU", "capital": "Vilna", "nacionalidad": "lituano/a", "idiomas": "Lituano"},
    {"numero": 103, "nombre": "Luxemburgo", "nombre_corto": "LUX", "capital": "Luxemburgo", "nacionalidad": "luxemburgués/a", "idiomas": "Luxemburgués, Francés, Alemán"},
    {"numero": 104, "nombre": "Madagascar", "nombre_corto": "MDG", "capital": "Antananarivo", "nacionalidad": "malgache", "idiomas": "Malgache, Francés"},
    {"numero": 105, "nombre": "Malasia", "nombre_corto": "MYS", "capital": "Kuala Lumpur", "nacionalidad": "malasio/a", "idiomas": "Malayo"},
    {"numero": 106, "nombre": "Malaui", "nombre_corto": "MWI", "capital": "Lilongwe", "nacionalidad": "malauí", "idiomas": "Inglés, Chichewa"},
    {"numero": 107, "nombre": "Maldivas", "nombre_corto": "MDV", "capital": "Malé", "nacionalidad": "maldivo/a", "idiomas": "Divehi"},
    {"numero": 108, "nombre": "Malí", "nombre_corto": "MLI", "capital": "Bamako", "nacionalidad": "maliense", "idiomas": "Francés"},
    {"numero": 109, "nombre": "Malta", "nombre_corto": "MLT", "capital": "La Valeta", "nacionalidad": "maltés/a", "idiomas": "Maltés, Inglés"},
    {"numero": 110, "nombre": "Marruecos", "nombre_corto": "MAR", "capital": "Rabat", "nacionalidad": "marroquí", "idiomas": "Árabe, Bereber"},
    {"numero": 111, "nombre": "Mauricio", "nombre_corto": "MUS", "capital": "Port Louis", "nacionalidad": "mauriciano/a", "idiomas": "Inglés, Francés"},
    {"numero": 112, "nombre": "Mauritania", "nombre_corto": "MRT", "capital": "Nuakchot", "nacionalidad": "mauritano/a", "idiomas": "Árabe"},
    {"numero": 113, "nombre": "México", "nombre_corto": "MEX", "capital": "Ciudad de México", "nacionalidad": "mexicano/a", "idiomas": "Español"},
    {"numero": 114, "nombre": "Micronesia", "nombre_corto": "FSM", "capital": "Palikir", "nacionalidad": "micronesio/a", "idiomas": "Inglés"},
    {"numero": 115, "nombre": "Moldavia", "nombre_corto": "MDA", "capital": "Chisinau", "nacionalidad": "moldavo/a", "idiomas": "Rumano"},
    {"numero": 116, "nombre": "Mónaco", "nombre_corto": "MCO", "capital": "Mónaco", "nacionalidad": "monegasco/a", "idiomas": "Francés"},
    {"numero": 117, "nombre": "Mongolia", "nombre_corto": "MNG", "capital": "Ulán Bator", "nacionalidad": "mongol/a", "idiomas": "Mongol"},
    {"numero": 118, "nombre": "Montenegro", "nombre_corto": "MNE", "capital": "Podgorica", "nacionalidad": "montenegrino/a", "idiomas": "Montenegrino"},
    {"numero": 119, "nombre": "Mozambique", "nombre_corto": "MOZ", "capital": "Maputo", "nacionalidad": "mozambiqueño/a", "idiomas": "Portugués"},
    {"numero": 120, "nombre": "Myanmar", "nombre_corto": "MMR", "capital": "Naipyidó", "nacionalidad": "birmano/a", "idiomas": "Birmano"},
    {"numero": 121, "nombre": "Namibia", "nombre_corto": "NAM", "capital": "Windhoek", "nacionalidad": "namibio/a", "idiomas": "Inglés"},
    {"numero": 122, "nombre": "Nauru", "nombre_corto": "NRU", "capital": "Yaren", "nacionalidad": "nauruano/a", "idiomas": "Nauruano, Inglés"},
    {"numero": 123, "nombre": "Nepal", "nombre_corto": "NPL", "capital": "Katmandú", "nacionalidad": "nepalés/a", "idiomas": "Nepalí"},
    {"numero": 124, "nombre": "Nicaragua", "nombre_corto": "NIC", "capital": "Managua", "nacionalidad": "nicaragüense", "idiomas": "Español"},
    {"numero": 125, "nombre": "Níger", "nombre_corto": "NER", "capital": "Niamey", "nacionalidad": "nigerino/a", "idiomas": "Francés"},
    {"numero": 126, "nombre": "Nigeria", "nombre_corto": "NGA", "capital": "Abuya", "nacionalidad": "nigeriano/a", "idiomas": "Inglés"},
    {"numero": 127, "nombre": "Noruega", "nombre_corto": "NOR", "capital": "Oslo", "nacionalidad": "noruego/a", "idiomas": "Noruego"},
    {"numero": 128, "nombre": "Nueva Zelanda", "nombre_corto": "NZL", "capital": "Wellington", "nacionalidad": "neozelandés/a", "idiomas": "Inglés, Maorí"},
    {"numero": 129, "nombre": "Omán", "nombre_corto": "OMN", "capital": "Mascate", "nacionalidad": "omaní", "idiomas": "Árabe"},
    {"numero": 130, "nombre": "Países Bajos", "nombre_corto": "NLD", "capital": "Ámsterdam", "nacionalidad": "neerlandés/a", "idiomas": "Neerlandés"},
    {"numero": 131, "nombre": "Pakistán", "nombre_corto": "PAK", "capital": "Islamabad", "nacionalidad": "pakistaní", "idiomas": "Urdu, Inglés"},
    {"numero": 132, "nombre": "Palaos", "nombre_corto": "PLW", "capital": "Ngerulmud", "nacionalidad": "palauano/a", "idiomas": "Palauano, Inglés"},
    {"numero": 133, "nombre": "Panamá", "nombre_corto": "PAN", "capital": "Ciudad de Panamá", "nacionalidad": "panameño/a", "idiomas": "Español"},
    {"numero": 134, "nombre": "Papúa Nueva Guinea", "nombre_corto": "PNG", "capital": "Port Moresby", "nacionalidad": "papú", "idiomas": "Inglés, Tok Pisin, Hiri Motu"},
    {"numero": 135, "nombre": "Paraguay", "nombre_corto": "PRY", "capital": "Asunción", "nacionalidad": "paraguayo/a", "idiomas": "Español, Guaraní"},
    {"numero": 136, "nombre": "Perú", "nombre_corto": "PER", "capital": "Lima", "nacionalidad": "peruano/a", "idiomas": "Español, Quechua, Aimara"},
    {"numero": 137, "nombre": "Polonia", "nombre_corto": "POL", "capital": "Varsovia", "nacionalidad": "polaco/a", "idiomas": "Polaco"},
    {"numero": 138, "nombre": "Portugal", "nombre_corto": "PRT", "capital": "Lisboa", "nacionalidad": "portugués/a", "idiomas": "Portugués"},
    {"numero": 139, "nombre": "Reino Unido", "nombre_corto": "GBR", "capital": "Londres", "nacionalidad": "británico/a", "idiomas": "Inglés"},
    {"numero": 140, "nombre": "República Centroafricana", "nombre_corto": "CAF", "capital": "Bangui", "nacionalidad": "centroafricano/a", "idiomas": "Francés, Sango"},
    {"numero": 141, "nombre": "República Checa", "nombre_corto": "CZE", "capital": "Praga", "nacionalidad": "checo/a", "idiomas": "Checo"},
    {"numero": 142, "nombre": "República del Congo", "nombre_corto": "COG", "capital": "Brazzaville", "nacionalidad": "congoleño/a", "idiomas": "Francés"},
    {"numero": 143, "nombre": "República Democrática del Congo", "nombre_corto": "COD", "capital": "Kinshasa", "nacionalidad": "congoleño/a", "idiomas": "Francés"},
    {"numero": 144, "nombre": "República Dominicana", "nombre_corto": "DOM", "capital": "Santo Domingo", "nacionalidad": "dominicano/a", "idiomas": "Español"},
    {"numero": 145, "nombre": "Ruanda", "nombre_corto": "RWA", "capital": "Kigali", "nacionalidad": "ruandés/a", "idiomas": "Kinyarwanda, Francés, Inglés"},
    {"numero": 146, "nombre": "Rumania", "nombre_corto": "ROU", "capital": "Bucarest", "nacionalidad": "rumano/a", "idiomas": "Rumano"},
    {"numero": 147, "nombre": "Rusia", "nombre_corto": "RUS", "capital": "Moscú", "nacionalidad": "ruso/a", "idiomas": "Ruso"},
    {"numero": 148, "nombre": "Samoa", "nombre_corto": "WSM", "capital": "Apia", "nacionalidad": "samoano/a", "idiomas": "Samoano, Inglés"},
    {"numero": 149, "nombre": "San Cristóbal y Nieves", "nombre_corto": "KNA", "capital": "Basseterre", "nacionalidad": "sancristobaleño/a", "idiomas": "Inglés"},
    {"numero": 150, "nombre": "San Marino", "nombre_corto": "SMR", "capital": "San Marino", "nacionalidad": "sanmarinense", "idiomas": "Italiano"},
    {"numero": 151, "nombre": "San Vicente y las Granadinas", "nombre_corto": "VCT", "capital": "Kingstown", "nacionalidad": "sanvicentino/a", "idiomas": "Inglés"},
    {"numero": 152, "nombre": "Santa Lucía", "nombre_corto": "LCA", "capital": "Castries", "nacionalidad": "santalucense", "idiomas": "Inglés"},
    {"numero": 153, "nombre": "Santo Tomé y Príncipe", "nombre_corto": "STP", "capital": "Santo Tomé", "nacionalidad": "santotomense", "idiomas": "Portugués"},
    {"numero": 154, "nombre": "Senegal", "nombre_corto": "SEN", "capital": "Dakar", "nacionalidad": "senegalés/a", "idiomas": "Francés"},
    {"numero": 155, "nombre": "Serbia", "nombre_corto": "SRB", "capital": "Belgrado", "nacionalidad": "serbio/a", "idiomas": "Serbio"},
    {"numero": 156, "nombre": "Seychelles", "nombre_corto": "SYC", "capital": "Victoria", "nacionalidad": "seychellense", "idiomas": "Inglés, Francés, Criollo seychellense"},
    {"numero": 157, "nombre": "Sierra Leona", "nombre_corto": "SLE", "capital": "Freetown", "nacionalidad": "sierraleonés/a", "idiomas": "Inglés"},
    {"numero": 158, "nombre": "Singapur", "nombre_corto": "SGP", "capital": "Singapur", "nacionalidad": "singapurense", "idiomas": "Inglés, Malayo, Chino, Tamil"},
    {"numero": 159, "nombre": "Siria", "nombre_corto": "SYR", "capital": "Damasco", "nacionalidad": "sirio/a", "idiomas": "Árabe"},
    {"numero": 160, "nombre": "Somalia", "nombre_corto": "SOM", "capital": "Mogadiscio", "nacionalidad": "somalí", "idiomas": "Somalí, Árabe"},
    {"numero": 161, "nombre": "Sri Lanka", "nombre_corto": "LKA", "capital": "Sri Jayawardenepura Kotte", "nacionalidad": "esrilankés/a", "idiomas": "Cingalés, Tamil"},
    {"numero": 162, "nombre": "Sudáfrica", "nombre_corto": "ZAF", "capital": "Pretoria", "nacionalidad": "sudafricano/a", "idiomas": "Inglés, Afrikáans, Zulú"},
    {"numero": 163, "nombre": "Sudán", "nombre_corto": "SDN", "capital": "Jartum", "nacionalidad": "sudanés/a", "idiomas": "Árabe, Inglés"},
    {"numero": 164, "nombre": "Sudán del Sur", "nombre_corto": "SSD", "capital": "Yuba", "nacionalidad": "sursudanés/a", "idiomas": "Inglés, Árabe"},
    {"numero": 165, "nombre": "Suecia", "nombre_corto": "SWE", "capital": "Estocolmo", "nacionalidad": "sueco/a", "idiomas": "Sueco"},
    {"numero": 166, "nombre": "Suiza", "nombre_corto": "CHE", "capital": "Berna", "nacionalidad": "suizo/a", "idiomas": "Alemán, Francés, Italiano, Romanche"},
    {"numero": 167, "nombre": "Surinam", "nombre_corto": "SUR", "capital": "Paramaribo", "nacionalidad": "surinamés/a", "idiomas": "Neerlandés"},
    {"numero": 168, "nombre": "Tailandia", "nombre_corto": "THA", "capital": "Bangkok", "nacionalidad": "tailandés/a", "idiomas": "Tailandés"},
    {"numero": 169, "nombre": "Tanzania", "nombre_corto": "TZA", "capital": "Dodoma", "nacionalidad": "tanzano/a", "idiomas": "Suajili, Inglés"},
    {"numero": 170, "nombre": "Tayikistán", "nombre_corto": "TJK", "capital": "Dusambé", "nacionalidad": "tayiko/a", "idiomas": "Tayiko"},
    {"numero": 171, "nombre": "Timor Oriental", "nombre_corto": "TLS", "capital": "Dili", "nacionalidad": "timorense", "idiomas": "Tetun, Portugués"},
    {"numero": 172, "nombre": "Togo", "nombre_corto": "TGO", "capital": "Lomé", "nacionalidad": "togolés/a", "idiomas": "Francés"},
    {"numero": 173, "nombre": "Tonga", "nombre_corto": "TON", "capital": "Nukualofa", "nacionalidad": "tongano/a", "idiomas": "Tongano, Inglés"},
    {"numero": 174, "nombre": "Trinidad y Tobago", "nombre_corto": "TTO", "capital": "Puerto España", "nacionalidad": "trinitense", "idiomas": "Inglés"},
    {"numero": 175, "nombre": "Túnez", "nombre_corto": "TUN", "capital": "Túnez", "nacionalidad": "tunecino/a", "idiomas": "Árabe"},
    {"numero": 176, "nombre": "Turkmenistán", "nombre_corto": "TKM", "capital": "Asjabad", "nacionalidad": "turcomano/a", "idiomas": "Turcomano"},
    {"numero": 177, "nombre": "Turquía", "nombre_corto": "TUR", "capital": "Ankara", "nacionalidad": "turco/a", "idiomas": "Turco"},
    {"numero": 178, "nombre": "Tuvalu", "nombre_corto": "TUV", "capital": "Funafuti", "nacionalidad": "tuvaluano/a", "idiomas": "Tuvaluano, Inglés"},
    {"numero": 179, "nombre": "Ucrania", "nombre_corto": "UKR", "capital": "Kiev", "nacionalidad": "ucraniano/a", "idiomas": "Ucraniano"},
    {"numero": 180, "nombre": "Uganda", "nombre_corto": "UGA", "capital": "Kampala", "nacionalidad": "ugandés/a", "idiomas": "Inglés, Suajili"},
    {"numero": 181, "nombre": "Uruguay", "nombre_corto": "URY", "capital": "Montevideo", "nacionalidad": "uruguayo/a", "idiomas": "Español"},
    {"numero": 182, "nombre": "Uzbekistán", "nombre_corto": "UZB", "capital": "Taskent", "nacionalidad": "uzbeko/a", "idiomas": "Uzbeko"},
    {"numero": 183, "nombre": "Vanuatu", "nombre_corto": "VUT", "capital": "Port Vila", "nacionalidad": "vanuatense", "idiomas": "Bislama, Inglés, Francés"},
    {"numero": 184, "nombre": "Venezuela", "nombre_corto": "VEN", "capital": "Caracas", "nacionalidad": "venezolano/a", "idiomas": "Español"},
    {"numero": 185, "nombre": "Vietnam", "nombre_corto": "VNM", "capital": "Hanói", "nacionalidad": "vietnamita", "idiomas": "Vietnamita"},
    {"numero": 186, "nombre": "Yemen", "nombre_corto": "YEM", "capital": "Saná", "nacionalidad": "yemení", "idiomas": "Árabe"},
    {"numero": 187, "nombre": "Yibuti", "nombre_corto": "DJI", "capital": "Yibuti", "nacionalidad": "yibutiano/a", "idiomas": "Árabe, Francés"},
    {"numero": 188, "nombre": "Zambia", "nombre_corto": "ZMB", "capital": "Lusaka", "nacionalidad": "zambiano/a", "idiomas": "Inglés"},
    {"numero": 189, "nombre": "Zimbabue", "nombre_corto": "ZWE", "capital": "Harare", "nacionalidad": "zimbabuense", "idiomas": "Inglés, Shona, Ndebele"},
]


async def seed():
    async with async_session() as db:  # type: AsyncSession
        # Países
        for p in PAISES:
            existe = await db.get(Pais, p["numero"])
            if existe is None:
                db.add(Pais(**p))
        await db.flush()

        # Usuario Midnight Lace (ID 1) — empresa
        existe_ml = await db.get(Persona, 1)
        if existe_ml is None:
            db.add(
                Persona(
                    identificador=1,
                    documento="00000000",
                    nombre="Midnight",
                    apellido="Lace",
                    email="contacto@midnightlace.com",
                    nombre_usuario="midnight_lace",
                    direccion="Alsina",
                    altura="451",
                    localidad="CABA",
                    ciudad="CABA",
                    url_foto_doc_frente="n/a",
                    url_foto_doc_dorso="n/a",
                    estado="activo",
                    hash_contrasenia="n/a",
                )
            )
            await db.flush()

        existe_emp = await db.get(Empleado, 1)
        if existe_emp is None:
            db.add(Empleado(identificador=1, cargo="Midnight Lace"))
            await db.flush()

        existe_cli = await db.get(Cliente, 1)
        if existe_cli is None:
            db.add(Cliente(identificador=1, admitido="si", categoria="platino", verificador=1))
            await db.flush()

        # Resetear secuencia de personas después de insertar ID 1 manualmente
        await db.execute(text("SELECT setval('personas_identificador_seq', GREATEST(1, (SELECT COALESCE(MAX(identificador), 0) FROM personas)))"))

        await db.flush()

        # Subastador de prueba (para que verificacion-producto tenga a quien asignar)
        existe_sub = await db.scalar(select(Persona).where(Persona.email == "subastador@midnightlace.com"))
        if existe_sub is None:
            db.add(Persona(
                documento="11111111",
                nombre="Martillero",
                apellido="Público",
                email="subastador@midnightlace.com",
                nombre_usuario="subastador_ml",
                direccion="Corrientes",
                altura="800",
                localidad="CABA",
                ciudad="CABA",
                url_foto_doc_frente="n/a",
                url_foto_doc_dorso="n/a",
                estado="activo",
                hash_contrasenia=hash_password("Subastador123!"),
            ))
            await db.flush()
            sub_persona = await db.scalar(select(Persona).where(Persona.email == "subastador@midnightlace.com"))
            db.add(Subastador(identificador=sub_persona.identificador, matricula="ML-001", region="CABA"))
            await db.flush()

        # Depósitos
        depos = await db.scalar(text("SELECT COUNT(*) FROM depositos"))
        if depos == 0:
            db.add_all([
                Deposito(nombre="Depósito Central", direccion="Av. Rivadavia 1500, CABA"),
                Deposito(nombre="Depósito Norte", direccion="Panamericana Km 35, Pilar"),
                Deposito(nombre="Depósito Sur", direccion="Av. Calchaquí 4500, Quilmes"),
                Deposito(nombre="Depósito Oeste", direccion="Ruta 7 Km 22, Luján"),
                Deposito(nombre="Depósito Puerto", direccion="Av. España 1200, Puerto Madero"),
            ])
            await db.flush()

        # Seguros (pólizas disponibles)
        segs = await db.scalar(text("SELECT COUNT(*) FROM seguros"))
        if segs == 0:
            db.add_all([
                Seguro(nro_poliza="POL-2026-001", compania="La Segunda Seguros", poliza_combinada="si", importe=500000),
                Seguro(nro_poliza="POL-2026-002", compania="Sancor Seguros", poliza_combinada="no", importe=750000),
                Seguro(nro_poliza="POL-2026-003", compania="Federación Patronal", poliza_combinada="si", importe=300000),
                Seguro(nro_poliza="POL-2026-004", compania="Zurich Seguros", poliza_combinada="no", importe=1000000),
                Seguro(nro_poliza="POL-2026-005", compania="Mapfre Seguros", poliza_combinada="si", importe=450000),
                Seguro(nro_poliza="POL-2026-006", compania="Allianz Seguros", poliza_combinada="no", importe=600000),
                Seguro(nro_poliza="POL-2026-007", compania="Galeno Seguros", poliza_combinada="si", importe=850000),
                Seguro(nro_poliza="POL-2026-008", compania="Prudential Seguros", poliza_combinada="no", importe=400000),
            ])
            await db.flush()

        await db.commit()
        print("Seed completado: 189 países (ONU) + Midnight Lace + subastador + 5 depósitos + 8 seguros.")


if __name__ == "__main__":
    asyncio.run(seed())
