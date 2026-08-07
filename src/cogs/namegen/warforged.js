const nameData = {
    neutral: {
        prefix: ["Iron", "Steel", "Stone", "Bronze", "Ash", "Obsidian", "Cinder", "Chrome", "Rust", "Lead", "Shadow", "Gear", "Silver", "Gold", "Titan", "Adamant", "Quartz", "Smoke", "Onyx", "Flame", "Plasma", "Storm", "Forge", "Echo", "Void", "Wire", "Alloy", "Dust", "Glint", "Frost", "Grime", "Crimson"],
        suffix: ["fist", "core", "shard", "clad", "strike", "spark", "plate", "grip", "knuckle", "gear", "bolt", "drive", "jaw", "spike", "helm", "forge", "arm", "breaker", "chest", "engine", "soul", "eye", "voice", "heart", "guard", "limb", "link", "burn", "clamp", "lash", "grind", "frame"],
        adjective: ["Silent", "Crimson", "Vigilant", "Ironbound", "Echo", "Feral", "Ancient", "Steadfast", "Glowing", "Relentless", "Flickering", "Molten", "Resolute", "Solemn", "Rusted", "Hollow", "Wary", "Unbroken", "Cursed", "Reforged", "Brazen", "Thundering", "Obsessive", "Bound", "Wired", "Heavy", "Etched", "Crumbling", "Mirror", "Static", "Null"],
        noun: ["Sentinel", "Watcher", "Breaker", "Forge", "Strider", "Titan", "Warden", "Revenant", "Golem", "Seeker", "Hammer", "Guard", "Construct", "Beacon", "Shell", "Lancer", "Javelin", "Crusader", "Stalker", "Haunt", "Monolith", "Paladin", "Juggernaut", "Machina", "Harbinger", "Echo", "Specter", "Pilgrim", "Cipher", "Node", "Catalyst"]
    },
    male: {
        prefix: ["Iron", "Steel", "Stone", "Forge", "Ash", "Thunder", "Obsidian", "Brass", "Grim", "Char", "Blast", "Ironhide", "Lead", "Slate", "Furnace", "Dark", "Black", "Smelt", "Grit", "Coal"],
        suffix: ["breaker", "crusher", "shard", "bludgeon", "grip", "spike", "maul", "smash", "bringer", "cleaver", "rend", "ram", "punch", "driver", "sever", "storm", "shatter", "brawler", "guard", "brand"],
        adjective: ["Grim", "Stalwart", "Ironbound", "Unyielding", "Feral", "Relentless", "Savage", "Indomitable", "Resolute", "Steeled", "Burning", "Fearless", "Loyal", "Warlike", "Scarred", "Dreadforged", "Bound", "Cold", "Hardened", "Titanic"],
        noun: ["Juggernaut", "Anvil", "Titan", "Warlord", "Colossus", "Rampart", "Bastion", "Engine", "Wall", "Vanguard", "Giant", "Aegis", "Strike", "Garrison", "Crusher", "Shield", "Blast", "Executioner", "Pillar", "Forgehand"]
    },
    female: {
        prefix: ["Silver", "Crystal", "Light", "Gilded", "Star", "Moon", "Echo", "Petal", "Glass", "Dream", "Mist", "Aurora", "Velvet", "Feather", "Snow", "Pearl", "Glow", "Dawn", "Lace", "Seraph"],
        suffix: ["song", "glide", "whisper", "bloom", "veil", "soul", "wing", "grace", "shine", "flare", "sigh", "shimmer", "dance", "touch", "glow", "beam", "sparkle", "gleam", "flow", "aura"],
        adjective: ["Radiant", "Serene", "Luminous", "Graceful", "Whispering", "Kindred", "Celestial", "Shimmering", "Elegant", "Blessed", "Mystic", "Soothing", "Gentle", "Compassionate", "Heavenly", "Harmonious", "Resonant", "Mirrored", "Flickering", "Vivid"],
        noun: ["Melody", "Hope", "Swan", "Halo", "Dream", "Wisp", "Oracle", "Dawn", "Nova", "Bloom", "Light", "Sigh", "Siren", "Hymn", "Seraph", "Spark", "Feather", "Muse", "Charm", "Spirit"]
    }
};

function random(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function generateNameParts(gender = "b") {
    // Determine source pool
    let chosenCategory;
    if (gender === "f") {
        chosenCategory = Math.random() < 0.25 ? "neutral" : "female";
    } else if (gender === "m") {
        chosenCategory = Math.random() < 0.25 ? "neutral" : "male";
    } else {
        chosenCategory = "neutral";
    }

    const data = nameData[chosenCategory];
    if (!data) {
        throw new Error(`No name parts defined for category: ${chosenCategory}`);
    }

    // Randomly choose between two structure types
    let name;
    if (Math.random() < 0.5) {
        const prefix = random(data.prefix);
        const suffix = random(data.suffix);
        name = /^[A-Z]/.test(suffix) ? `${prefix} ${suffix}` : `${prefix}${suffix}`;
    } else {
        const adjective = random(data.adjective);
        const noun = random(data.noun);
        name = /^[A-Z]/.test(noun) ? `${adjective} ${noun}` : `${adjective}${noun}`;
    }

    return { name, source: chosenCategory };
}

function generateName(gender = "b") {
    const { name, source } = generateNameParts(gender);

    let genderLabel;
    if (source === "female") {
        genderLabel = "(feminine)";
    } else if (source === "male") {
        genderLabel = "(masculine)";
    } else {
        genderLabel = "(neutral)";
    }

    return `${capitalize(name)} ${genderLabel}`;
}

// CLI entry for testing
if (typeof require !== "undefined" && require.main === module) {
    let gender = process.argv[2];
    if (!["m", "f", "b"].includes(gender)) gender = "b";
    const quantity = Math.min(Math.max(parseInt(process.argv[3]) || 1, 1), 100);
    for (let i = 0; i < quantity; i++) {
        console.log(generateName(gender));
    }
}
