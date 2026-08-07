const nameParts = {
    nm1: ["Ablaze", "Alight", "Ardor", "Ardour", "Arson", "Ash", "Ashe", "Austral", "Bake", "Bayle", "Beacon", "Blaize", "Blaze", "Blight", "Blyze", "Boil", "Bonfire", "Boyle", "Brand", "Broil", "Brun", "Burn", "Calcine", "Candle", "Cauterize", "Cendis", "Char", "Charcoal", "Cinder", "Claire", "Coal", "Coale", "Cole", "Combust", "Conflagration", "Cremate", "Crisp", "Dante", "Dantean", "Ember", "Enkindle", "Explosion", "Fenix", "Fernis", "Ferno", "Fervis", "Fervor", "Fever", "Fiery", "Flair", "Flame", "Flare", "Flarion", "Flaris", "Flash", "Flashfire", "Flicker", "Flux", "Forge", "Frizzle", "Fry", "Fuegis", "Fuego", "Fuel", "Fume", "Fumus", "Furnace", "Fusilis", "Fye", "Glare", "Gleam", "Glint", "Glo", "Glow", "Grill", "Heat", "Hell", "Hellfire", "Hot", "Igneos", "Igneous", "Ignis", "Ignit", "Ignite", "Ignition", "Incedis", "Incendiary", "Incendius", "Incinerate", "Infernal", "Inferno", "Infernus", "Kiln", "Kindle", "Kindra", "Lantern", "Lava", "Lavar", "Lavis", "Light", "Lit", "Magma", "Magmis", "Melt", "Nether", "Nova", "Novis", "Oven", "Parch", "Phoenix", "Piping", "Pyre", "Pyro", "Pyroc", "Ragnis", "Roast", "Scald", "Scaldor", "Scaldris", "Scorch", "Scorchis", "Scoria", "Sear", "Seethe", "Shine", "Sigmis", "Singe", "Sizzle", "Smo", "Smoke", "Smolder", "Smoldris", "Smulder", "Soot", "Soots", "Spark", "Sultry", "Sun", "Swelter", "Tempris", "Thermal", "Thermo", "Tinder", "Toast", "Torch", "Torrid", "Volcanis", "Volcano", "Warmth", "Wildfire", "Wither"],
    nm2: ["Agua", "Aqua", "Aqualis", "Aqualon", "Aquanis", "Aquara", "Aquifis", "Aquira", "Aquiris", "Aquis", "Azure", "Azuris", "Basin", "Bath", "Bathe", "Beck", "Bore", "Boyle", "Branch", "Brine", "Brook", "Caenum", "Clarity", "Cleanse", "Course", "Creek", "Current", "Dabble", "Damp", "Deluge", "Dew", "Dewdrop", "Douse", "Downpour", "Drain", "Drench", "Drift", "Drip", "Drizzle", "Drop", "Droplet", "Drown", "Eagre", "Estuary", "Expanse", "Flo", "Flood", "Flow", "Fluvis", "Flux", "Fog", "Fountain", "Geyser", "Geysis", "Glacia", "Glacis", "Glacius", "Gush", "Hose", "Hydra", "Hydran", "Hydris", "Hydrius", "Hydrogen", "Hydrox", "Influx", "Jet", "Lagoon", "Lake", "Lakelet", "Limu", "Limus", "Liquaxis", "Liquid", "Liquire", "Liquis", "Mere", "Mist", "Monse", "Monsoo", "Monsoon", "Neptis", "Neptulus", "Neptune", "Ocea", "Ocean", "Paddle", "Plash", "Plunge", "Pond", "Pool", "Poole", "Precip", "Precipe", "Precipise", "Puddle", "Puddles", "Puds", "Purity", "Quagmire", "Rain", "Rane", "Rayne", "Retaw", "Rill", "Rinse", "Ripple", "River", "Rivule", "Rivulet", "Run", "Runnel", "Rush", "Saline", "Salis", "Sea", "Seiche", "Shower", "Soak", "Spatter", "Splash", "Spout", "Spring", "Sprinkle", "Squalos", "Storm", "Stream", "Streamlet", "Surf", "Surge", "Swish", "Tear", "Teardrop", "Tempest", "Tempestus", "Tidal", "Tide", "Torrent", "Tributary", "Tsuna", "Tsunami", "Tsunis", "Typhis", "Typhoon", "Typhos", "Vape", "Vapor", "Vapora", "Vapore", "Vapos", "Wash", "Wave", "Well", "Wet"],
    nm3: ["Adamant", "Afa", "Agate", "Alabaster", "Amethyst", "Avalan", "Azurite", "Basalt", "Basselt", "Bedrock", "Block", "Boulder", "Brick", "Bulder", "Callous", "Carbonne", "Citrine", "Clay", "Claye", "Cliff", "Cobble", "Cobbles", "Cobblestone", "Core", "Crag", "Crayg", "Crystal", "Dense", "Diamond", "Dune", "Duster", "Emerald", "Firmis", "Flint", "Fossil", "Fossilstone", "Garnet", "Gem", "Geo", "Geod", "Geode", "Granit", "Granite", "Granius", "Grant", "Graund", "Grav", "Gravel", "Grime", "Grimes", "Grine", "Gritt", "Ground", "Hill", "Hunk", "Ingot", "Jade", "Jewel", "Lapis", "Lazuli", "Limestone", "Lios", "Lodge", "Lump", "Lutu", "Lutum", "Malachite", "Marble", "Marmoreal", "Mason", "Masonry", "Mineral", "Monolith", "Moonstone", "Mountain", "Nugget", "Obsidian", "Onyx", "Opal", "Ore", "Oria", "Oris", "Pebble", "Pellet", "Peridot", "Precious", "Pulvi", "Pulvis", "Quarris", "Quarry", "Quartz", "Quartzite", "Quary", "Roc", "Rock", "Rocky", "Rough", "Rubble", "Ruby", "Rugged", "Sand", "Sandstone", "Sapphire", "Sediment", "Shelf", "Slab", "Slait", "Slate", "Soapstone", "Sod", "Soile", "Solid", "Spinel", "Stone", "Stony", "Stowne", "Sturdy", "Tera", "Terberis", "Terbis", "Terbius", "Terra", "Terrane", "Terros", "Thera", "Theran", "Therris", "Tile", "Topaz", "Travertine", "Turf", "Turve", "Umber", "Valanche", "Wedge", "Zircon"],
    nm4: ["Aeranas", "Aerate", "Aere", "Aeria", "Aerial", "Aeris", "Aeros", "Air", "Aros", "Ascend", "Atmos", "Atmosphere", "Aura", "Avian", "Aviate", "Avis", "Azura", "Azure", "Blast", "Blow", "Breath", "Breeze", "Breyze", "Celes", "Celeste", "Celestial", "Cerulea", "Cerulis", "Cerulle", "Chinook", "Circos", "Clode", "Cloud", "Cruise", "Current", "Cyclone", "Cyclonis", "Cyclonius", "Cyclos", "Draft", "Drift", "Eddy", "Empearal", "Empyrean", "Exalos", "Fan", "Float", "Flow", "Flurris", "Flurry", "Flute", "Flutter", "Fly", "Funnel", "Gale", "Gasp", "Gayle", "Glide", "Gust", "Halitus", "Halo", "Halos", "Heave", "Heaven", "Hiss", "Hover", "Hurican", "Huricus", "Hurricane", "Imperos", "Lift", "Mistral", "Murmur", "Murmus", "Oxygen", "Oxyn", "Ozone", "Pipe", "Pneumatic", "Puff", "Rise", "Sail", "Shriek", "Sigh", "Sky", "Skye", "Soar", "Sonas", "Sonis", "Sono", "Sonus", "Squall", "Storm", "Stratos", "Stratosphere", "Surge", "Tempest", "Tempeste", "Tornado", "Tropos", "Troposphere", "Tumul", "Tumult", "Tumulus", "Turbine", "Turbulence", "Twister", "Vent", "Ventis", "Volance", "Volaris", "Vox", "Voxis", "Waft", "Wheeze", "Whiff", "Whirl", "Whirlwind", "Whisk", "Whistle", "Wind", "Wing", "Xygen", "Zephyr", "Zephys"],
    nm5: ["Avala", "Avalan", "Blizz", "Chillis", "Cryo", "Cryogen", "Crystal", "Drift", "Firn", "Flaik", "Flayke", "Flo", "Flurris", "Frose", "Fross", "Glace", "Glacis", "Glayze", "Gliss", "Hayle", "Iciclis", "Iglis", "Lanche", "Melte", "Neige", "Sleat", "Snift", "Thawe"],
    nm6: ["Flash", "Spark", "Bolt", "Ramman", "Baraq", "Storm", "Elec", "Lec", "Lectric", "Volt", "Tes", "Tesla", "Thun", "Fulg", "Fulgu", "Gurate", "Astra", "Bron", "Bronto", "Cerau", "Ceraun", "Cerauno", "Amp", "Fara", "Farad", "Watt", "Galv", "Galva", "Galvan", "Ohm", "Ohme", "Volta"],
    nm7: ["Aura", "Auris", "Aurora", "Baecos", "Fax", "Glimmes", "Illume", "Illumine", "Lambence", "Luceras", "Lucernas", "Lucis", "Lucus", "Lumen", "Lumina", "Luminus", "Lumis", "Lumus", "Lustris", "Lustrous", "Lux", "Lychnus", "Sol", "Solaris", "Solas", "Soleis"],
    nm8: ["Adum", "Atax", "Bane", "Calamis", "Calas", "Cimmeris", "Clipse", "Corrus", "Diables", "Disaris", "Disas", "Dusk", "Eclipe", "Entros", "Gloom", "Glum", "Hayze", "Heinios", "Iniq", "Malefis", "Malignus", "Malis", "Malos", "Malov", "Miseris", "Narchis", "Nefaris", "Nighe", "Nite", "Obscuras", "Penum", "Pitch", "Scuris", "Shayde", "Shaye", "Smog", "Soros", "Spyte", "Twileigh", "Umbris", "Umbrus", "Veilios", "Vilis"],
    nm9: ["Sanguine", "Sanguinus", "Sange", "Sanguin", "Clot", "Cruor", "Plasma", "Gore", "Serum", "Vein", "Aorta", "Aort", "Plasm", "Arte", "Arter", "Anemis", "Anemia", "Anaemia", "Anae", "Anaemis", "Leuko", "Kocyte", "Leukos", "Hema", "Hemal", "Hemall", "Purpu", "Purpura", "Purpur", "Throm", "Thrombus", "Thromb", "Acidosis", "Acidos"]
};

const nameData = {
    "Fire": {
        "name": ["nm1"],
    },
    "Water": {
        "name": ["nm2"],
    },
    "Earth": {
        "name": ["nm3"],
    },
    "Air": {
        "name": ["nm4"],
    },
    "Ice": {
        "name": ["nm5"],
    },
    "Lightning": {
        "name":["nm6"],
    },
    "Light": {
        "name": ["nm7"],
    },
    "Shadow": {
        "name": ["nm8"],
    },
    "Blood": {
        "name": ["nm9"],
    },
};

function random(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function generateNameParts(subrace = "") {
    const chosenSubrace = subrace || random(Object.keys(nameData));
    const partsObject = nameData[chosenSubrace];

    if (!partsObject || !Array.isArray(partsObject.name) || partsObject.name.length === 0) {
        throw new Error(`No name parts defined for subrace: ${chosenSubrace}`);
    }

    return {
        name: partsObject.name.map(p => random(nameParts[p])).join(""),
        subrace: chosenSubrace
    };
}

function nameMas(subrace = "Fire") {
    return generateNameParts(subrace, "name");
}
function nameFem(subrace = "Fire") {
    return generateNameParts(subrace, "name");
}

function generateName(type = "m", subrace = "") {
    const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "m" : "f") : type;

    const { name, subrace: finalSubrace } = generateNameParts(subrace);
    return capitalize(name).trim() + " " + "("+finalSubrace+")" + "###" + finalSubrace;
}



if (typeof require !== "undefined" && require.main === module) {
    let gender = process.argv[2];
    if (!["m", "f", "b"].includes(gender)) gender = "b";
    const quantity = Math.min(Math.max(parseInt(process.argv[3]) || 1, 1), 100);
    for (let i = 0; i < quantity; i++) {
        console.log(generateName(gender));
    }
};
