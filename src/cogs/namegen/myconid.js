const nameParts = {
    nm1: ["", "", "", "", "", "b", "d", "f", "g", "h", "l", "n", "p", "ph", "ps", "r", "v", "y"],
    nm2: ["oo", "ee", "aa", "a", "e", "i", "o", "y", "a", "e", "i", "o", "y", "u", "a", "e", "i", "o", "y"],
    nm3: ["b", "bl", "d", "g", "gl", "gr", "l", "lb", "ld", "p", "r", "rb", "s", "sb", "sh", "st"],
    nm4: ["a", "e", "i", "o"],
    nm5: ["b", "c", "d", "l", "m", "n", "p", "r", "b", "c", "d", "l", "m", "n", "p", "r", "b", "c", "d", "l", "m", "n", "p", "r", "bl", "br", "dr", "pb", "pl", "pr", "rb", "rd", "sn", "sp"],
    nm6: ["ia", "oo", "aa", "io", "y", "e", "o", "u", "y", "e", "o", "u", "y", "e", "o", "u", "y", "e", "o", "u", "y", "e", "o", "u"],
    nm7: ["", "b", "d", "l", "p", "r", "s", "b", "d", "l", "p", "r", "s"],
    nm8: ["a", "b", "c", "d", "e"],
    nm9: ["aa", "ee", "ii", "oo", "uu"],
    nm10: ["k", "l", "m", "n", "p"],
    nm11: ["qu", "ra", "si", "to", "vu"],
    nm12: ["we", "xa", "yo", "ze", "tu"],
    nm13: ["li", "mo", "na", "pa", "re"],
    nm14: ["sa", "ta", "ua", "va", "wa"],
    nm15: ["xa", "ya", "za", "ab", "ac"]
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
    const np = nameParts;
	let nMs = "";
    const nTp = Math.floor(Math.random() * 5);
    const rnd = Math.floor(Math.random() * np.nm1.length);
    const rnd2 = Math.floor(Math.random() * np.nm2.length);
    const rnd3 = Math.floor(Math.random() * np.nm7.length);
    let rnd4 = Math.floor(Math.random() * np.nm3.length);
    const rnd5 = Math.floor(Math.random() * np.nm4.length);

    if (nTp < 3) {
        while (np.nm3[rnd4] === np.nm1[rnd] || np.nm3[rnd4] === np.nm7[rnd3]) {
            rnd4 = Math.floor(Math.random() * np.nm3.length);
        }
        nMs = np.nm1[rnd] + np.nm2[rnd2] + np.nm3[rnd4] + np.nm4[rnd5] + np.nm7[rnd3];
    } else {
        const rnd6 = Math.floor(Math.random() * np.nm5.length);
        const rnd7 = Math.floor(Math.random() * np.nm6.length);
        while (np.nm3[rnd4] === np.nm5[rnd6] || np.nm5[rnd6] === np.nm7[rnd3]) {
            rnd4 = Math.floor(Math.random() * np.nm5.length);
        }
        nMs = np.nm1[rnd] + np.nm2[rnd2] + np.nm3[rnd4] + np.nm4[rnd5] + np.nm5[rnd6] + np.nm6[rnd7] + np.nm7[rnd3];
    }

	return capitalize(nMs);
}


function nameFem() {
    const np = nameParts;
    let nMs = "";
    const nTp = Math.floor(Math.random() * 7);
    const rnd = Math.floor(Math.random() * np.nm8.length);
    const rnd2 = Math.floor(Math.random() * np.nm9.length);
    let rnd3 = Math.floor(Math.random() * np.nm10.length);
    const rnd4 = Math.floor(Math.random() * np.nm14.length);
    const rnd7 = Math.floor(Math.random() * np.nm15.length);

    if (nTp < 4) {
        while (np.nm10[rnd3] === np.nm8[rnd] || np.nm10[rnd3] === np.nm15[rnd7]) {
            rnd3 = Math.floor(Math.random() * np.nm10.length);
        }
        nMs = np.nm8[rnd] + np.nm9[rnd2] + np.nm10[rnd3] + np.nm14[rnd4] + np.nm15[rnd7];
    } else {
        const rnd5 = Math.floor(Math.random() * np.nm11.length);
        let rnd6 = Math.floor(Math.random() * np.nm12.length);
        while (np.nm12[rnd6] === np.nm10[rnd3] || np.nm10[rnd3] === np.nm8[rnd]) {
            rnd3 = Math.floor(Math.random() * np.nm10.length);
        }
        if (nTp < 6) {
            nMs = np.nm8[rnd] + np.nm9[rnd2] + np.nm10[rnd3] + np.nm11[rnd5] + np.nm12[rnd6] + np.nm14[rnd4] + np.nm15[rnd7];
        } else {
            const rnd8 = Math.floor(Math.random() * np.nm11.length);
            let rnd9 = Math.floor(Math.random() * np.nm13.length);
            while (np.nm12[rnd6] === np.nm13[rnd9] || np.nm13[rnd9] === np.nm15[rnd7]) {
                rnd9 = Math.floor(Math.random() * np.nm13.length);
            }
            nMs = np.nm8[rnd] + np.nm9[rnd2] + np.nm10[rnd3] + np.nm11[rnd5] + np.nm12[rnd6] + np.nm11[rnd8] + np.nm13[rnd9] + np.nm14[rnd4] + np.nm15[rnd7];
        }
    }

    return capitalize(nMs);
}

function generateName(type = "b", subrace = "") {
    const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "m" : "f") : type;
    const genderTag = g === "m" ? " (m)" : " (f)";

    let nMs = g === "m" ? nameMas() : nameFem();

    return nMs + genderTag + "###" + subrace;
}



if (typeof require !== "undefined" && require.main === module) {
    let gender = process.argv[2];
    if (!["m", "f", "b"].includes(gender)) gender = "b";
    const quantity = Math.min(Math.max(parseInt(process.argv[3]) || 1, 1), 100);
    for (let i = 0; i < quantity; i++) {
        console.log(generateName(gender));
    }
};
