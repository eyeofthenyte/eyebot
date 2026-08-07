const nameParts = {
    nm1: ["Ad", "Ae", "Bal", "Bei", "Car", "Cra", "Dae", "Dor", "El", "Ela", "Er", "Far", "Fen", "Gen", "Glyn", "Hei", "Her", "Ian", "Ili", "Kea", "Kel", "Leo", "Lu", "Mira", "Mor", "Nae", "Nor", "Olo", "Oma", "Pa", "Per", "Pet", "Qi", "Qin", "Ralo", "Ro", "Sar", "Syl", "The", "Tra", "Ume", "Uri", "Va", "Vir", "Waes", "Wran", "Yel", "Yin", "Zin", "Zum"],
    nm2: ["balar", "beros", "can", "ceran", "dan", "dithas", "faren", "fir", "geiros", "golor", "hice", "horn", "jeon", "jor", "kas", "kian", "lamin", "lar", "len", "maer", "maris", "menor", "myar", "nan", "neiros", "nelis", "norin", "peiros", "petor", "qen", "quinal", "ran", "ren", "ric", "ris", "ro", "salor", "sandoral", "toris", "tumal", "valur", "ven", "warin", "wraek", "xalim", "xidor", "yarus", "ydark", "zeiros", "zumin"],
    nm3: ["Ad", "Ara", "Bi", "Bry", "Cai", "Chae", "Da", "Dae", "Eil", "En", "Fa", "Fae", "Gil", "Gre", "Hele", "Hola", "Iar", "Ina", "Jo", "Key", "Kris", "Lia", "Lora", "Mag", "Mia", "Neri", "Ola", "Ori", "Phi", "Pres", "Qi", "Qui", "Rava", "Rey", "Sha", "Syl", "Tor", "Tris", "Ula", "Uri", "Val", "Ven", "Wyn", "Wysa", "Xil", "Xyr", "Yes", "Ylla", "Zin", "Zyl"],
    nm4: ["banise", "bella", "caryn", "cyne", "di", "dove", "fiel", "fina", "gella", "gwyn", "hana", "harice", "jyre", "kalyn", "krana", "lana", "lee", "leth", "lynn", "moira", "mys", "na", "nala", "phine", "phyra", "qirelle", "ra", "ralei", "rel", "rie", "rieth", "rona", "rora", "roris", "satra", "stina", "sys", "thana", "thyra", "tris", "varis", "vyre", "wenys", "wynn", "xina", "xisys", "ynore", "yra", "zana", "zorwyn"],
    nm5: ["A", "Ae", "Ar", "Arga", "Au", "Be", "Ben", "Bene", "Ble", "Blei", "Bra", "Bre", "Bri", "Brio", "Bryo", "Ca", "Can", "Cara", "Cas", "Cen", "Cin", "Cle", "Co", "Con", "Cor", "Da", "De", "Deme", "Fre", "Freo", "Frio", "Ga", "Gau", "Ge", "Ger", "Go", "Gri", "Gry", "Gu", "Gur", "Gwa", "He", "Hed", "Hu", "Hum", "Ia", "Il", "In", "Iu", "Ja", "Jo", "Ke", "Ken", "Ko", "Lo", "Lowe", "Ma", "Mae", "Mas", "Me", "Mel", "Mer", "Mi", "Mo", "Mor", "Mue", "My", "Pa", "Pe", "Per", "Ra", "Re", "Ru", "Rua", "Se", "Sele", "Te", "Tele", "Tew", "Tree", "Tri", "We", "Wel", "Wen", "Wi", "Win", "Wu", "Wur", "Wy", "Ya", "Ye", "Yl"],
    nm6: ["bri", "cant", "cencor", "cohn", "con", "cor", "cryn", "cum", "dan", "der", "dern", "dhek", "dic", "dilic", "dis", "dok", "dret", "drod", "dros", "fagan", "fra", "fure", "gan", "gent", "gethen", "ghal", "girn", "gor", "guallon", "gur", "gustel", "lan", "lic", "loc", "lon", "louen", "marh", "men", "menoc", "min", "mo", "moere", "monoc", "moyre", "muyre", "myn", "nac", "nan", "nci", "neder", "nesek", "noac", "noc", "nok", "radok", "rael", "ran", "redis", "rek", "ren", "rentyn", "ret", "riant", "rient", "rit", "rok", "ron", "ryn", "sek", "sen", "sian", "stel", "tan", "tanet", "thael", "thek", "thien", "thion", "thon", "thrit", "thyen", "tigirn", "tok", "trec", "tyn", "wallon", "wan", "wen", "wyn"],
    nm7: ["A", "Ae", "Anau", "Anni", "As", "Be", "Bea", "Ber", "Bo", "Bria", "Cee", "Cei", "Cein", "Che", "Con", "De", "Deme", "Dero", "E", "Ele", "Elo", "Em", "En", "Ese", "Ewe", "Fua", "Fuan", "Gla", "Gloi", "Gloiu", "Gue", "Guen", "Gwen", "Ia", "Je", "Jene", "Jo", "Ka", "Kel", "Kele", "Ker", "Kere", "La", "Lamo", "Lo", "Lowe", "Ma", "Me", "Mel", "Mo", "Mor", "Morve", "Ne", "Nes", "No", "O", "On", "Ou", "Our", "Pa", "Pas", "Pro", "Ro", "Ru", "Se", "Sena", "So", "Sowe", "Ste", "Ta", "Tal", "Tam", "Tama", "Tan", "Te", "Tre", "Tree", "True", "We", "Wen", "Wue", "Wuen", "Y", "Ys"],
    nm8: ["cen", "cenedl", "der", "dhuil", "doc", "duil", "dylyc", "fer", "gen", "gereth", "guen", "guetel", "guled", "la", "led", "len", "lewen", "lin", "lis", "luen", "lyn", "lynen", "mara", "med", "mon", "morna", "na", "nath", "nedl", "neret", "net", "nik", "nol", "rec", "rel", "reth", "rezen", "rith", "rowen", "sa", "saba", "seld", "sella", "sen", "sin", "stren", "styl", "syn", "teilin", "tel", "ten", "wanet", "wean", "wen", "wena", "wenna", "wetel", "wuen", "wynn", "zen"],
    nm9: ["Acorn", "Aed", "Aeden", "Alaneo", "Albedo", "Ali", "Almond", "Aloha", "Anthurium", "Aodh", "Aphid", "Apogee", "Aqua", "Ash", "Astro", "Aven", "Avo", "Axis", "Badger", "Barley", "Basil", "Bear", "Berry", "Bim", "Birch", "Blathnat", "Blaze", "Bracken", "Bramble", "Briar", "Brock", "Bud", "Bumble", "Calico", "Canyon", "Caraway", "Carpus", "Carrot", "Cedar", "Christopher", "Cinnamon", "Cirro", "Cirrus", "Citron", "Cloud", "Coconut", "Comet", "Cookie", "Cosmo", "Crator", "Cricket", "Daybreak", "Dew", "Dewdrop", "Diaspor", "Dragonfly", "Drake", "Dune", "Dusk", "Earth", "Echo", "Elliot", "Elm", "Finch", "Firo", "Flame", "Flamo", "Flare", "Flax", "Flint", "Flix", "Florian", "Fox", "Foxglove", "Freddie", "Frost", "Frostbite", "Ginko", "Happy", "Harbor", "Harley", "Helio", "Herb", "Indi", "Indigo", "Jamie", "Jarrah", "Jeremy", "Karma", "Koko", "Lake", "Lapis", "Lark", "Laurel", "Lazuli", "Lemony", "Light", "Lightning", "Liri", "Lucky", "Luke", "Magpie", "Mahogany", "Mango", "Marlie", "Meadow", "Mercury", "Midnight", "Miles", "Mitah", "Moon", "Moonbeam", "Moonbean", "Moptop", "Morel", "Mountain", "Mulberry", "Nebula", "Nelly", "Newt", "Nightfall", "Nightshade", "Nimbus", "North", "Nova", "Novus", "Nutmeg", "Nyx", "Oak", "Ocean", "Oleander", "Oliver", "Onyx", "Oregano", "Pandora", "Peanut", "Pecan", "Pepper", "Peridot", "Persimmon", "Petal", "Pine", "Pinecone", "Pistachio", "Plume", "Poppy", "Pyro", "Quicksilver", "Quinn", "Rain", "Raine", "Reef", "Rhubarb", "Ridge", "Robbie", "Robin", "Rock", "Rocky", "Saffron", "Scorpia", "Shade", "Silver", "Sky", "Skylark", "Smokey", "Sneezy", "Snow", "Snowdrop", "Snowflake", "Spark", "Spice", "Spring", "Sprinkle", "Sprinkles", "Stardust", "Starfish", "Stargazer", "Stone", "Storm", "Stormy", "Strombo", "Sunbeam", "Sundew", "Sunrise", "Sunset", "Tadpole", "Tangy", "Tarragon", "Thicket", "Thistle", "Tidal", "Tiger", "Timber", "Timothy", "Tiny", "Tori", "Trevan", "Trumpet", "Turnip", "Twig", "Walnut", "Willow", "Winnie", "Wolf", "Woods", "Zephyr"],
    nm10: ["Pervinca", "Hiedra", "Vinca", "Dandelia", "Dandelion", "Clavelina", "Clavellina", "Vulparia", "Luparia", "Belladonna", "Passiflora", "Pimpinella", "Eupherbia", "Poinsetia", "Rafflesia", "Phyre", "Abeyance", "Abigail", "Abyss", "Acacia", "Adriata", "Alcyone", "Alexa", "Alexandra", "Alexi", "Alexia", "Ali", "Alina", "Allium", "Almond", "Aloha", "Alyssum", "Amaltheia", "Amantha", "Amaryllis", "Amber", "Amethyst", "Amode", "Amy", "Anastasia", "Anemone", "Angel", "Annie", "Apple", "Apricot", "April", "Aqua", "Aria", "Arianna", "Arlette", "Ashley", "Aspen", "Asphodel", "Aurora", "Autumn", "Ayanna", "Azalea", "Azore", "Badger", "Barbara", "Bayberry", "Bedra", "Begonia", "Bellflower", "Berline", "Beryl", "Bethany", "Betsy", "Betty", "Bianca", "Bim", "Birch", "Birdy", "Blodwen", "Blooma", "Blossom", "Bluebell", "Bonnie", "Breeze", "Breezy", "Briar", "Briny", "Bryla", "Bumble", "Buttercup", "Cadmi", "Calico", "Caliphe", "Calla", "Camelia", "Camellia", "Camie", "Camille", "Candala", "Canyon", "Caraway", "Carnelia", "Carrie", "Carrot", "Cassia", "Cassie", "Cayenne", "Cecil", "Cecile", "Celeste", "Celestia", "Chaldera", "Chante", "Charity", "Charlotte", "Chasma", "Cherry", "Chert", "Chestnut", "Chickadee", "Chipmunk", "Chloe", "Chlora", "Christal", "Cinder", "Cinnamon", "Cintrine", "Citron", "Cleo", "Cloud", "Clove", "Clover", "Coconut", "Confiance", "Cookie", "Coral", "Coriander", "Cornflower", "Corona", "Cowrie", "Coyote", "Crabapple", "Cranberry", "Cricket", "Crystal", "Cupcake", "Cypress", "Daffodil", "Dahlia", "Daisy", "Dalila", "Dandelion", "Daphne", "Darla", "Dawn", "Daybreak", "Daylily", "Delia", "Desily", "Dew", "Dewdrop", "Dey", "Diamond", "Didi", "Dill", "Dilys", "Dina", "Dolly", "Dragonfly", "Earth", "Ebbie", "Ebony", "Elaina", "Eli", "Ella", "Elle", "Elliot", "Elm", "Elma", "Elva", "Ember", "Emerald", "Emily", "Emma", "Erissa", "Estrella", "Evangeline", "Eve", "Evening", "Evie", "Ezra", "Faith", "Fantasia", "Fauna", "Faye", "Fee", "Fern", "Feu", "Fiery", "Fifi", "Flame", "Flamo", "Flare", "Flax", "Flora", "Floura", "Forsythia", "Frances", "Frangi", "Freesia", "Frost", "Galaxa", "Galaxy", "Gardenia", "Garnet", "Gem", "Genevieve", "Gerania", "Gerbera", "Ginger", "Ginny", "Gloria", "Gloriosa", "Grace", "Grevillea", "Grove", "Gullie", "Gypsum", "Happy", "Harbor", "Harley", "Harmony", "Hazel", "Heather", "Heaven", "Heidi", "Helen", "Helia", "Helio", "Heliodor", "Herb", "Hibiscus", "Hickoy", "Holly", "Hollyann", "Hollyhock", "Honey", "Hope", "Horizon", "Hurricane", "Hyacinth", "Hydrangea", "Ignea", "Igni", "Indigo", "Infinity", "Ionia", "Iridia", "Iris", "Isabel", "Isabelle", "Island", "Isle", "Ivory", "Ivy", "Jada", "Jade", "Jamie", "Jane", "Jasmine", "Jayla", "Jeanie", "Jenny", "Jessamine", "Jewel", "Jewels", "Jillian", "Joanna", "Johanna", "Joy", "Julianne", "Julie", "June", "Juniper", "Karina", "Karma", "Kate", "Kayleighe", "Kaylor", "Kelly", "Kenzie", "Kesiray", "Kiki", "Kiwi", "Kobi", "Koko", "Kyanne", "Kylee", "Kyra", "Labivia", "Labyrinth", "Lake", "Lala", "Lantana", "Lapis", "Laura", "Laurelai", "Lauren", "Lavender", "Layla", "Lazuli", "Leaf", "Leeta", "Lella", "Lemony", "Lenora", "Levia", "Liatris", "Libby", "Lichen", "Light", "Lila", "Lilac", "Lilah", "Lily", "Liri", "Little", "Liza", "Lizzy", "Lorella", "Lori", "Loue", "Lucia", "Lucky", "Lucy", "Lula", "Lulu", "Lumiona", "Luna", "Lynn", "Lynne", "Maddie", "Maeve", "Maga", "Magenta", "Magna", "Magnola", "Magnolia", "Magpie", "Mahogany", "Maie", "Manga", "Mango", "Maple", "Marcasite", "Marceline", "Margo", "Marigold", "Marin", "Marina", "Marlie", "Mary", "May", "Meadow", "Meer", "Melanie", "Melody", "Meri", "Meridian", "Mia", "Midnight", "Mildread", "Milkweed", "Minerva", "Miranda", "Misha", "Misty", "Mivian", "Molly", "Moon", "Moonbeam", "Moonbean", "Mora", "Mossy", "Mudpie", "Mulberry", "Muriel", "Mythia", "Nastur", "Nature", "Nautila", "Nebula", "Nectarine", "Nelly", "Newt", "Nightfall", "Nightshade", "Nimbus", "Nina", "Nissa", "Nora", "Nutmeg", "Nyphadora", "Nyra", "Oceana", "Octavia", "Olive", "Olivia", "Opal", "Ora", "Orange", "Orchid", "Oreal", "Oregano", "Oriole", "Palmera", "Pandora", "Paprika", "Parsley", "Peach", "Peachy", "Peanut", "Pearl", "Pecan", "Penelope", "Peoni", "Pepper", "Percula", "Peridot", "Petal", "Petunia", "Phira", "Phoebe", "Pine", "Pineapple", "Pinecone", "Pluma", "Plume", "Plumeria", "Poison", "Polly", "Poplar", "Poppy", "Posey", "Posy", "Prairie", "Primrose", "Prinna", "Prise", "Prudence", "Pumpkin", "Purple", "Pyro", "Rachel", "Rain", "Rainbow", "Raine", "Rainy", "Raven", "Rebutia", "Relle", "Rhoda", "Rhodie", "Rhonda", "Rhubarb", "Rill", "River", "Robin", "Rola", "Rore", "Rosa", "Rosalind", "Rose", "Rosemary", "Rosepetal", "Rosie", "Ruby", "Sadie", "Saffron", "Sage", "Sahara", "Saira", "Salle", "Sally", "Sandy", "Sapphire", "Sassafras", "Savannah", "Scarlet", "Scorpia", "Sea", "Seaweed", "Sela", "Selene", "Selenia", "Sequoia", "Serena", "Serendipity", "Shade", "Shanna", "Shayleigh", "Shelly", "Shiny", "Shyla", "Sienna", "Silhouette", "Silver", "Sivelle", "Sky", "Skyler", "Sneezy", "Snow", "Snowdrop", "Snowflake", "Solara", "Soleil", "Sophie", "Sorrell", "Spark", "Sparkla", "Spectra", "Spice", "Spirala", "Spore", "Spring", "Sprinkle", "Sprinkles", "Spruce", "Star", "Stardust", "Starfish", "Stargazer", "Stella", "Stormy", "Strawberri", "Strawberry", "Sue", "Sugar", "Sulcore", "Summer", "Sun", "Sunbeam", "Sundew", "Sunflower", "Sunlight", "Sunny", "Sunrise", "Sunset", "Sunshine", "Swan", "Tamara", "Tangy", "Tansy", "Tara", "Tasi", "Tempest", "Tess", "Tessa", "Thallia", "Thistle", "Tidal", "Tiger", "Tinder", "Tinkerbell", "Tiny", "Topaz", "Topiary", "Tori", "Tourmaline", "Tournant", "Treva", "Trinity", "Trish", "Tulip", "Turnip", "Turquoise", "Twig", "Twilight", "Tyra", "Urchin", "Valorie", "Vanessa", "Velocity", "Venus", "Verey", "Vickie", "Victoria", "Vilotta", "Viola", "Violet", "Vivi", "Wallflower", "Walnut", "Waterfall", "Wave", "West", "Whirl", "Willow", "Wind", "Windy", "Winnie", "Winter", "Wispa", "Woods", "Wrassey", "Wren", "Xenops", "Yasmine", "Yavia", "Yitri", "Yucca"],
};

const nameData = {

};

function random(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function generateNameParts(parts) {
    return parts.map(p => random(nameParts[p])).join("");
}

function nameMas() {
    const rnd = Math.floor(Math.random() * nameParts.nm1.length);
    const rnd2 = Math.floor(Math.random() * nameParts.nm2.length);
    return nameParts.nm1[rnd] + nameParts.nm2[rnd2];
}

function nameFem() {
    const rnd = Math.floor(Math.random() * nameParts.nm3.length);
    const rnd2 = Math.floor(Math.random() * nameParts.nm4.length);
    return nameParts.nm3[rnd] + nameParts.nm4[rnd2];
}

function nameMasT() {
    const rnd = Math.floor(Math.random() * nameParts.nm5.length);
    const rnd2 = Math.floor(Math.random() * nameParts.nm6.length);
    return nameParts.nm5[rnd] + nameParts.nm6[rnd2];
}

function nameFemT() {
    const rnd = Math.floor(Math.random() * nameParts.nm7.length);
    const rnd2 = Math.floor(Math.random() * nameParts.nm8.length);
    return nameParts.nm7[rnd] + nameParts.nm8[rnd2];
}

function generateName(type = "m", subrace = "fairy") {
    const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "male" : "female") : (type === "f" ? "female" : "male");

    const i = Math.floor(Math.random() * 10);
    let first;
    if (g === "f") {
        if (i < 3) {
            first = nameFem(); // Standard feminine
        }
        else if (i < 6) {
            first = nameFemT(); // Thematic feminine
        }
        else {
            first = nameParts.nm10[Math.floor(Math.random() * nameParts.nm10.length)];
        }
    }
    else {
        if (i < 3) {
            first = nameMas(); // Standard masculine
        }
        else if (i < 6) {
            first = nameMasT(); // Thematic masculine
        }
        else {
            first = nameParts.nm9[Math.floor(Math.random() * nameParts.nm9.length)];
        }
    }

    let nMs = ""
    if (g === "male") {
        nMs = (capitalize(first)).trim() + " (m)"
    }
    else {
        nMs = (capitalize(first)).trim() + " (f)"
    }

    return nMs + "###" + subrace;
}



if (typeof require !== "undefined" && require.main === module) {
    let gender = process.argv[2];
    if (!["m", "f", "b"].includes(gender)) gender = "b";
    const quantity = Math.min(Math.max(parseInt(process.argv[3]) || 1, 1), 100);
    for (let i = 0; i < quantity; i++) {
        console.log(generateName(gender));
    }
};
