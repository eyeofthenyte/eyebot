const nameParts = {
    nm1: ["Ad", "Ae", "Bal", "Bei", "Car", "Cra", "Dae", "Dor", "El", "Ela", "Er", "Far", "Fen", "Gen", "Glyn", "Hei", "Her", "Ian", "Ili", "Kea", "Kel", "Leo", "Lu", "Mira", "Mor", "Nae", "Nor", "Olo", "Oma", "Pa", "Per", "Pet", "Qi", "Qin", "Ralo", "Ro", "Sar", "Syl", "The", "Tra", "Ume", "Uri", "Va", "Vir", "Waes", "Wran", "Yel", "Yin", "Zin", "Zum"],
    nm2: ["balar", "beros", "can", "ceran", "dan", "dithas", "faren", "fir", "geiros", "golor", "hice", "horn", "jeon", "jor", "kas", "kian", "lamin", "lar", "len", "maer", "maris", "menor", "myar", "nan", "neiros", "nelis", "norin", "peiros", "petor", "qen", "quinal", "ran", "ren", "ric", "ris", "ro", "salor", "sandoral", "toris", "tumal", "valur", "ven", "warin", "wraek", "xalim", "xidor", "yarus", "ydark", "zeiros", "zumin"],
    nm3: ["Ad", "Ara", "Bi", "Bry", "Cai", "Chae", "Da", "Dae", "Eil", "En", "Fa", "Fae", "Gil", "Gre", "Hele", "Hola", "Iar", "Ina", "Jo", "Key", "Kris", "Lia", "Lora", "Mag", "Mia", "Neri", "Ola", "Ori", "Phi", "Pres", "Qi", "Qui", "Rava", "Rey", "Sha", "Syl", "Tor", "Tris", "Ula", "Uri", "Val", "Ven", "Wyn", "Wysa", "Xil", "Xyr", "Yes", "Ylla", "Zin", "Zyl"],
    nm4: ["banise", "bella", "caryn", "cyne", "di", "dove", "fiel", "fina", "gella", "gwyn", "hana", "harice", "jyre", "kalyn", "krana", "lana", "lee", "leth", "lynn", "moira", "mys", "na", "nala", "phine", "phyra", "qirelle", "ra", "ralei", "rel", "rie", "rieth", "rona", "rora", "roris", "satra", "stina", "sys", "thana", "thyra", "tris", "varis", "vyre", "wenys", "wynn", "xina", "xisys", "ynore", "yra", "zana", "zorwyn"],

    nm5: ["", "", "", "b", "c", "d", "dr", "f", "fl", "g", "h", "k", "l", "m", "n", "r", "qu", "s", "sh", "t", "th", "v", "w", "x", "y"],
    nm6: ["ae", "ie", "ia", "ei", "ey", "a", "e", "i", "o", "u", "a", "e", "i", "o", "u", "a", "e", "i", "o", "u", "a", "e", "i", "o", "u", "a", "e", "i", "o", "u", "a", "e", "i", "o", "u"],
    nm7: ["dr", "l", "l", "ld", "ldr", "ll", "lph", "lt", "lth", "m", "n", "ndr", "nn", "nt", "ph", "r", "r", "rd", "rn", "s", "sh", "st", "str", "th", "thr", "v"],
    nm8: ["a", "e", "i", "o"],
    nm9: ["dr", "lk", "ndr", "nthr", "sc", "st", "str", "thr", "c", "h", "l", "m", "n", "nn", "ph", "r", "rr", "s", "ss", "v", "x"],
    nm10: ["ii", "ie", "aea", "ia", "ua", "a", "e", "i", "o", "a", "e", "i", "o", "a", "e", "i", "o", "a", "e", "i", "o", "a", "e", "i", "o", "a", "e", "i", "o", "a", "e", "i", "o", "a", "e", "i", "o"],
    nm11: ["", "", "", "", "", "l", "n", "nn", "nt", "r", "s", "sh", "th"],

    nm12: ["alder", "amber", "ash", "aspen", "autumn", "azure", "beech", "birch", "blue", "bold", "bronze", "cedar", "crimson", "dawn", "dew", "diamond", "dusk", "eager", "elder", "elm", "ember", "even", "fall", "far", "feather", "fir", "flower", "fog", "forest", "gem", "gold", "green", "hazel", "light", "lunar", "mist", "moon", "moss", "night", "oak", "oaken", "ocean", "poplar", "rain", "rapid", "raven", "sage", "shadow", "silent", "silver", "spark", "spirit", "spring", "star", "still", "stone", "summer", "sun", "swift", "wild", "willow", "wind", "winter", "wood"],
    nm13: ["beam", "bell", "birth", "blossom", "breath", "breeze", "brook", "cloud", "crown", "dew", "dream", "dreamer", "fall", "fate", "flight", "flow", "flower", "fond", "gaze", "gazer", "gift", "gleam", "grove", "guard", "heart", "heel", "hold", "kind", "light", "mane", "might", "mind", "moon", "path", "petal", "pride", "rest", "river", "seeker", "sense", "shadow", "shard", "shine", "singer", "smile", "song", "spark", "spell", "spirit", "star", "vale", "walker", "watcher", "whisper", "wish"],

    nm14: ["br", "ph", "th", "tr", "c", "d", "f", "g", "j", "k", "l", "m", "n", "p", "r", "s", "t", "v", "w", "z", "", "", "", ""],
    nm15: ["ae", "ay", "oe", "ue", "ai", "ia", "y", "a", "e", "i", "o", "a", "e", "i", "o"],
    nm16: ["k", "l", "ll", "m", "n", "nn", "r"],
    nm17: ["a", "i"],
    nm18: ["ll", "ng", "nn", "th", "rn", "l", "m", "n", "r", "s", "", ""],
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

function generateSurname() {
    const nTp = Math.floor(Math.random() * 8);
    const nm5 = random(nameParts.nm5);
    const nm6 = random(nameParts.nm6);
    const nm7 = random(nameParts.nm7);
    const nm10 = random(nameParts.nm10);
    const nm11 = random(nameParts.nm11);

    if (nTp < 3) {
        return nm5 + nm6 + nm7 + nm10 + nm11;
    } else {
        const nm8 = random(nameParts.nm8);
        const nm9 = random(nameParts.nm9);
        const rnd6 = Math.floor(Math.random() * nameParts.nm8.length);
        const rnd7 = Math.floor(Math.random() * nameParts.nm9.length);
        const nm8_2 = nameParts.nm8[rnd6];
        const nm9_2 = nameParts.nm9[rnd7];
        if (nTp < 6) {
            return nm5 + nm6 + nm7 + nm8 + nm9 + nm10 + nm11;
        } else {
            const rnd8 = Math.floor(Math.random() * nameParts.nm8.length);
            const rnd9 = Math.floor(Math.random() * nameParts.nm9.length);
            const nm8_3 = nameParts.nm8[rnd8];
            const nm9_3 = nameParts.nm9[rnd9];
            if (nTp === 6) {
                return nm5 + nm6 + nm7 + nm8_2 + nm9_2 + nm8_3 + nm9_3 + nm10 + nm11;
            } else {
                return nm5 + nm6 + nm9_2 + nm8_3 + nm7 + nm8_2 + nm9_3 + nm10 + nm11;
            }
        }
    }
}

function generateName(type = "m", subrace = "firbolg") {
    const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "male" : "female") : (type === "f" ? "female" : "male");

    const first = g === "f" ? nameFem() : nameMas();
    const last = generateSurname();

    let nMs = ""
    if (g === "male") {
        nMs = (capitalize(first) + " " + capitalize(last)).trim() + " (m)"
    }
    else {
        nMs = (capitalize(first) + " " + capitalize(last)).trim() + " (f)"
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
