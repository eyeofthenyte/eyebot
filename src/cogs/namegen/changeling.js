const nameParts = {
    nm1: ["", "", "", "b", "d", "f", "h", "j", "l", "m", "n", "p", "r", "s", "t", "v", "w", "y"],
    nm2: ["a", "i", "o", "u", "a", "i", "o", "u", "a", "i", "o", "u", "a", "i", "o", "u", "ee", "ie", "ea", "ae", "ai", "oo", "ou"],
    nm3: ["c", "g", "gs", "k", "ks", "kt", "m", "n", "rx", "rt", "rs", "s", "sk", "t", "ts", "x", "z"]
};

const nameData = {
    "changeling": {
        male: {
            nameParts: [["nm1"], ["nm2"], ["nm3"]],
            custom: customMale
        },
        female: {
            nameParts: [["nm1"], ["nm2"], ["nm3"]],
            custom: customMale // or define a separate customFemale if needed
        },
        // No surname defined
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

function customMale(parts) {
    const nm1 = parts["nm1"];
    const nm2 = parts["nm2"];
    const nm3 = parts["nm3"];

    let rnd = Math.floor(Math.random() * nm1.length);
    let rnd2 = Math.floor(Math.random() * nm2.length);
    let rnd3 = Math.floor(Math.random() * nm3.length);

    while (nm1[rnd] === nm3[rnd3]) {
        rnd3 = Math.floor(Math.random() * nm3.length);
    }

    let nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3]
    return nMs;
}

function generateName(type = "m", subrace = null) {
    const subraces = Object.keys(nameData);
    subrace = subrace || subraces[Math.floor(Math.random() * subraces.length)];
    let sr = nameData[subrace] || nameData[subrace.toLowerCase()] || nameData["changeling"];
    if (!sr) return "";

    const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "male" : "female") : (type === "f" ? "female" : "male");

    const patternInfo = sr[g];

    let name;
    if (patternInfo.custom) {
        name = patternInfo.custom(nameParts);
    } else {
        const pattern = Array.isArray(patternInfo.nameParts[0])
            ? patternInfo.nameParts[Math.floor(Math.random() * patternInfo.nameParts.length)]
            : patternInfo.nameParts;
        name = generateNameParts(pattern);
    }

    return capitalize(name) + " (neutral)" + "###" + subrace;
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
