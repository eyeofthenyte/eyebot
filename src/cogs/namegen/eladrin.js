const nameParts = {
    nm1: ["Ara", "Aran", "Ber", "Bran", "Cor", "Cru", "Da", "Daye", "Elro", "Ere", "Far", "Fyla", "Gal", "Galin", "Ha", "Hor", "Im", "Ira", "Ja", "Jor", "Kru", "Kuo", "Lan", "Lic", "Mar", "Min", "Nal", "Nark", "Ola", "Otir", "Pae", "Pan", "Qua", "Quo", "Rel", "Riar", "Sarn", "Sove", "Tav", "Trin", "Uri", "Veth", "Vic", "Wal", "Wrug", "Xan", "Yan", "Yor", "Zen", "Zor"],
    nm2: ["aris", "aster", "baver", "bin", "card", "corin", "dan", "darai", "dartis", "don", "emin", "erta", "fis", "fros", "geon", "grephor", "heros", "horn", "ikul", "iver", "kris", "kul", "lias", "liss", "mendi", "meral", "mil", "morn", "neiros", "nis", "okas", "oros", "peiros", "prath", "ratra", "reth", "rian", "rion", "sirak", "ster", "thas", "tihr", "torin", "urian", "uvir", "van", "vis", "wirn", "worn", "xeral", "xis", "ykos", "yth", "zeiros", "zion"],
    nm3: ["Al", "An", "Anas", "Be", "Bri", "Cae", "Cyl", "Dris", "Dur", "Eil", "Ena", "Fae", "Fan", "Gru", "Gyl", "Hen", "Hyl", "Illa", "Ire", "Jar", "Jelen", "Kai", "Kora", "Les", "Lyv", "Mag", "Me", "Nai", "Neri", "Ol", "Ori", "Pi", "Prys", "Qi", "Que", "Ri", "Rol", "Sa", "Sha", "Thei", "Tri", "Ul", "Ura", "Va", "Vela", "Wes", "Wre", "Xyr", "Ylla", "Zen"],
    nm4: ["bis", "bynn", "cahne", "caryn", "celle", "cena", "diel", "dys", "faera", "fyra", "glyn", "grys", "hanna", "hyssa", "kiries", "kyrath", "lenae", "lenna", "lyn", "lynna", "meiv", "miris", "mynis", "nairra", "neth", "parys", "prana", "qirith", "qis", "raste", "rastra", "riele", "rynna", "sanna", "shana", "sys", "thaea", "tora", "trianna", "vara", "viryn", "vyre", "wena", "wyse", "xana", "xis", "yana", "yeira", "zane", "zora"],
};

const nameData = {
    eladrin: {
        male: [["nm1", "nm2"]],
        female: [["nm3", "nm4"]],
        surname: [["nm1", "nm2"]],
    }
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


function generateName(type = "m", subrace = "eladrin") {
    const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "male" : "female") : (type === "f" ? "female" : "male");

    const subraceData = nameData[subrace];
    if (!subraceData || !subraceData[g]) {
        throw new Error(`No name data defined for subrace: ${subrace} and gender: ${g}`);
    }

    const firstParts = subraceData[g][0]; // Always one pattern
    const lastParts = subraceData.surname[0]; // Always one pattern

    const first = generateNameParts(firstParts);
    const last = generateNameParts(lastParts);

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
