const nameParts = {
    nm1: ["b", "br", "chr", "d", "g", "gh", "hr", "kh", "n", "r", "st", "t", "th", "v", "z", "zh"],
    nm2: ["a", "e", "i", "o", "u"],
    nm3: ["d", "dd", "dr", "g", "gh", "gg", "gr", "rr", "rd", "rg", "rn", "t", "tt", "tr", "v", "vr", "z", "zz"],
    nm4: ["a", "i", "o", "u"],
    nm5: ["k", "lk", "mkk", "n", "nn", "nk", "r", "rk", "rr", "th"],
};

const nameData = {
    "bugbear": {
        male: [["nm1", "nm2", "nm3"]],
        female: [["nm1", "nm2", "nm3"]]
    }
};

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function generateNameParts(pattern) {
    return pattern.map(part => {
        const arr = nameParts[part];
        return arr[Math.floor(Math.random() * arr.length)];
    }).join("");
}


function generateName(type = "m", subrace = null) {
    const subraces = Object.keys(nameData);
    subrace = subrace || subraces[Math.floor(Math.random() * subraces.length)];
    let sr = nameData[subrace] || nameData[subrace.toLowerCase()] || nameData["bugbear"];
    if (!sr) return "";

    const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "male" : "female") : (type === "f" ? "female" : "male");

    const nTp = Math.floor(Math.random() * 3);
    const rnd = Math.floor(Math.random() * nameParts.nm1.length);
    const rnd2 = Math.floor(Math.random() * nameParts.nm4.length);
    const rnd3 = Math.floor(Math.random() * nameParts.nm5.length);

    let nMs = "";

    if (nTp === 0) {
        nMs = nameParts.nm1[rnd] + nameParts.nm4[rnd2] + nameParts.nm5[rnd3] + " (m)";
    } else {
        const rnd4 = Math.floor(Math.random() * nameParts.nm2.length);
        const rnd5 = Math.floor(Math.random() * nameParts.nm3.length);
        nMs = nameParts.nm1[rnd] + nameParts.nm2[rnd4] + nameParts.nm3[rnd5] + nameParts.nm4[rnd2] + nameParts.nm5[rnd3] + " (f)";
    }

    return capitalize(nMs) + "###" + subrace;
}

// CLI usage
if (typeof require !== "undefined" && require.main === module) {
    let gender = process.argv[2];
    if (!["m", "f", "b"].includes(gender)) gender = "b";
    const quantity = Math.min(Math.max(parseInt(process.argv[3]) || 1, 1), 100);
    for (let i = 0; i < quantity; i++) {
        console.log(generateName(gender));
    }
};
