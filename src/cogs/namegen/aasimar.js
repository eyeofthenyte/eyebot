const nameParts = {
    nm1: ["", "", "", "", "b", "br", "c", "cr", "h", "l", "m", "n", "p", "r", "t", "v", "w", "z"],
    nm2: ["a", "e", "i", "o", "u", "y", "a", "e", "i", "o", "u", "y", "a", "e", "i", "o", "u", "y", "au", "ai", "ea", "ei"],
    nm3: ["d", "dr", "g", "gg", "gr", "gw", "k", "kr", "kl", "l", "ld", "lg", "lw", "lr", "lt", "n", "nr", "nw", "nl", "r", "rn", "rr", "rw", "rl", "v", "vr", "w"],
    nm4: ["a", "i", "a", "i", "a", "i", "a", "i", "a", "i", "a", "i", "e", "a", "i", "e", "a", "i", "e", "o", "o", "u", "u", "ee", "ia", "ie", "ai", "ei"],
    nm5: ["d", "l", "m", "n", "t", "v"],
    nm6: ["l", "m", "n", "nt", "r"],

    nm7: ["", "", "", "", "", "br", "d", "dr", "h", "l", "m", "n", "ph", "r", "rh", "th", "v", "w", "z"],
    nm8: ["a", "i", "o", "a", "i", "o", "a", "i", "o", "a", "i", "o", "a", "i", "o", "a", "i", "o", "e", "e", "ia", "io", "ea", "eo"],
    nm9: ["d", "j", "l", "ld", "ldr", "lv", "ll", "lt", "m", "mm", "mn", "n", "nr", "nv", "nl", "ndr", "nm", "r", "rd", "rk", "rs", "s", "sr", "sl", "v"],
    nm10: ["a", "e", "i", "o", "a", "e", "i", "o", "a", "e", "i", "o", "a", "e", "i", "o", "a", "e", "i", "o", "ea", "ia", "ie"],
    nm11: ["l", "m", "n", "r", "s", "z"],
    nm12: ["a", "e", "i", "a", "e", "i", "a", "e", "i", "a", "e", "i", "a", "e", "i", "au", "ou", "oe"],
    nm13: ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "h", "l", "m", "n", "r"]
};

const nameData = {
    aasimar: {
        male: [customMale],
        female: [customFemale]
    }
};

function capitalize(name) {
    if (!name || typeof name !== 'string') return '';
    return name.charAt(0).toUpperCase() + name.slice(1);
}

function customMale(i) {
    let nMs = "";
    let rnd, rnd2, rnd3, rnd4, rnd5, rnd6, rnd7;
    rnd = Math.floor(Math.random() * nameParts.nm1.length);
    rnd2 = Math.floor(Math.random() * nameParts.nm2.length);
    rnd3 = Math.floor(Math.random() * nameParts.nm3.length);
    rnd4 = Math.floor(Math.random() * nameParts.nm4.length);
    rnd5 = Math.floor(Math.random() * nameParts.nm6.length);

    if (i < 6) {
        while (nameParts.nm3[rnd3] === nameParts.nm1[rnd] || nameParts.nm3[rnd3] === nameParts.nm6[rnd5]) {
            rnd3 = Math.floor(Math.random() * nameParts.nm3.length);
        }
        nMs = nameParts.nm1[rnd] + nameParts.nm2[rnd2] + nameParts.nm3[rnd3] + nameParts.nm4[rnd4] + nameParts.nm6[rnd5];
    } else {
        rnd6 = Math.floor(Math.random() * nameParts.nm5.length);
        rnd7 = Math.floor(Math.random() * nameParts.nm4.length);
        while (nameParts.nm5[rnd6] === nameParts.nm3[rnd3] || nameParts.nm5[rnd6] === nameParts.nm6[rnd5]) {
            rnd6 = Math.floor(Math.random() * nameParts.nm5.length);
        }
        nMs = nameParts.nm1[rnd] + nameParts.nm2[rnd2] + nameParts.nm3[rnd3] + nameParts.nm4[rnd4] + nameParts.nm5[rnd6] + nameParts.nm4[rnd7] + nameParts.nm6[rnd5];
    }
    return nMs + " (m)";
}

function customFemale(i) {
    let nMs = "";
    let rnd, rnd2, rnd3, rnd4, rnd5, rnd6, rnd7;
    rnd = Math.floor(Math.random() * nameParts.nm7.length);
    rnd2 = Math.floor(Math.random() * nameParts.nm8.length);
    rnd3 = Math.floor(Math.random() * nameParts.nm9.length);
    rnd4 = Math.floor(Math.random() * nameParts.nm10.length);
    rnd5 = Math.floor(Math.random() * nameParts.nm13.length);

    if (i < 6) {
        while (nameParts.nm9[rnd3] === nameParts.nm7[rnd] || nameParts.nm9[rnd3] === nameParts.nm13[rnd5]) {
            rnd3 = Math.floor(Math.random() * nameParts.nm9.length);
        }
        nMs = nameParts.nm7[rnd] + nameParts.nm8[rnd2] + nameParts.nm9[rnd3] + nameParts.nm10[rnd4] + nameParts.nm13[rnd5];
    } else {
        rnd6 = Math.floor(Math.random() * nameParts.nm11.length);
        rnd7 = Math.floor(Math.random() * nameParts.nm12.length);
        while (nameParts.nm11[rnd6] === nameParts.nm9[rnd3] || nameParts.nm11[rnd6] === nameParts.nm13[rnd5]) {
            rnd6 = Math.floor(Math.random() * nameParts.nm11.length);
        }
        nMs = nameParts.nm7[rnd] + nameParts.nm8[rnd2] + nameParts.nm9[rnd3] + nameParts.nm10[rnd4] + nameParts.nm11[rnd6] + nameParts.nm12[rnd7] + nameParts.nm13[rnd5];
    }
    return nMs + " (f)";
}

function generateName(gender = "m", subrace = "aasimar") {
    const i = Math.floor(Math.random() * 10);
    const type = (gender === "f") ? "female" : "male";
    const genFunc = nameData[subrace]?.[type]?.[0];
    if (typeof genFunc === "function") {
        return capitalize(genFunc(i));
    }
    return "";
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
