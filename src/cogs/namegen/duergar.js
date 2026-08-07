const nameParts = {
    nm1: ["Ad","Am","Arm","Baer","Daer","Bal","Ban","Bar","Bel","Ben","Ber","Bhal","Bhar","Bhel","Bram","Bran","Brom","Brum","Bun","Dal","Dar","Dol","Dul","Eb","Em","Erm","Far","Gal","Gar","Ger","Gim","Gral","Gram","Gran","Grem","Gren","Gril","Gry","Gul","Har","Hjal","Hjol","Hjul","Hor","Hul","Hur","Kar","Khar","Kram","Krom","Krum","Mag","Mal","Mel","Mor","Muir","Mur","Rag","Ran","Reg","Rot","Thal","Thar","Thel","Ther","Tho","Thor","Thul","Thur","Thy","Tor","Ty","Um","Urm","Von"],
    nm2: ["adin","bek","brek","dahr","dain","dal","dan","dar","dek","dir","dohr","dor","drak","dram","dren","drom","drum","drus","duhr","dur","dus","garn","gram","gran","grim","grom","gron","grum","grun","gurn","gus","iggs","kahm","kam","kohm","kom","kuhm","kum","kyl","man","mand","mar","mek","miir","min","mir","mond","mor","mun","mund","mur","mus","myl","myr","nam","nar","nik","nir","nom","num","nur","nus","nyl","rak","ram","ren","rig","rigg","rik","rim","rom","ron","rum","rus","ryl","tharm","tharn","thran","thrum","thrun"],
    nm3: ["An","Ar","Baer","Bar","Bel","Belle","Bon","Bonn","Braen","Bral","Bralle","Bran","Bren","Bret","Bril","Brille","Brol","Bron","Brul","Bryl","Brylle","Bryn","Bryt","Byl","Bylle","Daer","Dear","Dim","Ed","Ein","El","Gem","Ger","Gwan","Gwen","Gwin","Gwyn","Gym","Ing","Jen","Jenn","Jin","Jyn","Kait","Kar","Kat","Kath","Ket","Las","Lass","Les","Less","Lyes","Lys","Lyss","Maer","Maev","Mar","Mis","Mist","Myr","Mys","Myst","Naer","Nal","Nas","Nass","Nes","Nis","Nys","Raen","Ran","Red","Reyn","Run","Ryn","Sar","Sol","Tas","Taz","Tis","Tish","Tiz","Tor","Tys","Tysh"],
    nm4: ["belle","bera","delle","deth","dielle","dille","dish","dora","dryn","dyl","giel","glia","glian","gwyn","la","leen","leil","len","lin","linn","lyl","lyn","lynn","ma","mera","mora","mura","myl","myla","nan","nar","nas","nera","nia","nip","nis","niss","nora","nura","nyl","nys","nyss","ra","ras","res","ri","ria","rielle","rin","ris","ros","ryl","ryn","sael","selle","sora","syl","thel","thiel","tin","tyn","va","van","via","vian","waen","win","wyn","wynn"],
    nm5: ["b","br","c","d","dr","f","g","gl","gr","h","l","m","r","str","t","thr"],
    nm6: ["ae","a","e","o","u","a","e","o","u","a","e","o","u","a","e","o","u"],
    nm7: ["br","d","fd","h","k","lbr","ld","ll","mn","ng","nh","nk","r","rd","rth","tg","thg","zz"],
    nm8: ["a","e","i","o","u"],
    nm9: ["g","h","k","n","r","v"],
    nm10: ["a","a","e","e","i","o","u"],
    nm11: ["ck","g","hk","hr","k","ln","m","n","nn","r","rk","rr","rt"],
    nm12: ["ash","barren","battle","black","blast","blind","blood","bold","bone","bright","broad","broken","bronze","burn","craven","dark","doom","earth","fire","flame","flint","fore","forge","giant","goblin","gore","grave","grim","hell","hollow","iron","keen","knife","mad","mind","molten","neck","onyx","ore","proud","rage","red","rock","rune","rust","shadow","silent","skull","stark","steel","stone","storm","stout","thunder","troll","under","venge","vice","war","wicked","wild","wrath"],
    nm13: ["axe","basher","battle","beard","belch","belcher","belt","blade","bleeder","boot","boots","braid","brand","breaker","breath","bringer","brow","buster","chain","chains","champion","chewer","cleaver","crag","crusher","drum","dust","earth","eater","edge","eye","fall","favor","feast","fight","fist","flayer","flow","force","forge","fury","gift","gore","grace","guard","hammer","hand","handle","head","heart","helm","hold","honor","horn","hunt","hunter","lord","mantle","march","mask","master","might","minder","pass","past","pride","reach","rest","ripper","rock","runner","slayer","slice","snapper","sorrow","spite","stand","stone","storm","strike","striker","tale","tamer","ward"],
};

const nameData = {
    duergar: {
        male: [["nm1", "nm2"]],
        female: [["nm3", "nm4"]],
        surname: [["nm12", "nm13"]],
    }
};

function capitalize(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function random(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
}

function generateNameParts(pattern) {
    return pattern.map(key => {
        const part = nameParts[key];
        return part ? part[Math.floor(Math.random() * part.length)] : "";
    }).join("");
}

function generateName(type = "m", subrace = null) {
    const subraces = Object.keys(nameData);
    subrace = subrace || subraces[Math.floor(Math.random() * subraces.length)];
    let sr = nameData[subrace] || nameData[subrace.toLowerCase()] || nameData["duergar"];
    if (!sr) return "";

    const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "male" : "female") : (type === "f" ? "female" : "male");

    const patternList = sr[g];
    const pattern = Array.isArray(patternList[0]) ? patternList[Math.floor(Math.random() * patternList.length)] : patternList;

    const first = generateNameParts(pattern);
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

function nameMas() {
    const nm1 = random(nameParts.nm1);
    const nm2 = random(nameParts.nm2);
    return nm1 + nm2;
}

function nameFem() {
    const nm3 = random(nameParts.nm3);
    const nm4 = random(nameParts.nm4);
    return nm3 + nm4;
}

function generateSurname() {
    const useAlt = Math.random() < 0.4;
    if (useAlt) {
        let rnd = Math.floor(Math.random() * nameParts.nm12.length);
        let rnd2 = Math.floor(Math.random() * nameParts.nm13.length);
        while (nameParts.nm12[rnd] === nameParts.nm13[rnd2]) {
            rnd2 = Math.floor(Math.random() * nameParts.nm13.length);
        }
        return nameParts.nm12[rnd] + nameParts.nm13[rnd2];
    } else {
        const ntp = Math.floor(Math.random() * 2);
        const nm5 = random(nameParts.nm5);
        const nm6 = random(nameParts.nm6);
        const nm7 = random(nameParts.nm7);
        const nm10 = random(nameParts.nm10);
        const nm11 = random(nameParts.nm11);

        if (ntp === 0) {
            return nm5 + nm6 + nm7 + nm10 + nm11;
        } else {
            const nm8 = random(nameParts.nm8);
            const nm9 = random(nameParts.nm9);
            return nm5 + nm6 + nm7 + nm8 + nm9 + nm10 + nm11;
        }
    }
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
