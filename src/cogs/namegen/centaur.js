const nameParts = {
	nm1: ["","","","b","d","dw","g","gh","gw","j","k","kh","m","n","rh","t","th","v","vr","z"],
	nm2: ["ae","ai","a","e","i","o","a","e","o","a","e","i","o","a","e","o"],
	nm3: ["f'r","l'n","l'd","m'v","m'z","n'z","n'v","n'r","sh'r","s'r","s'z","s'l","z'r","z'h","d","dr","g","gl","gr","k","kr","kl","l","ll","ld","ldr","ln","lr","lv","lz","lzr","m","mr","n","nn","nd","nv","r","rl","th","z","zl","zr"],
	nm4: ["a","e","i","u","e","i","u"],
	nm5: ["d","g","k","l","m","n","r","th","v"],
	nm6: ["a","e","i","o"],
	nm7: ["","","","d","g","h","l","ld","lk","n","nd","r","rd","s","t","th"],
	nm8: ["b","d","f","h","l","m","n","ph","r","s","sh","v","z"],
	nm9: ["a","e","i","a","e","i","o","y"],
	nm10: ["d","dh","dr","fr","fl","fn","g","gl","gr","ld","ldr","lg","ln","lr","lth","lv","lz","n","nr","nv","r","rl","rn","rg","rs","rz","rsh","z","zh","zr","zl"],
	nm11: ["a","e","i","i","o","y","y"],
	nm12: ["l","n","r","v","z"],
	nm13: ["ea","ia","ae","a","e","a","e","i","a","e","a","e","i","a","e","a","e","i","o","a","e","a","e","i","a","e","a","e","i","a","e","a","e","i","o"],
	nm14: ["g","h","l","n","r","s","sh","t","th"],
	nm15: ["Aspen","Autumn","Birch","Bloom","Boulder","Brook","Brown","Bright","Brush","Burrow","Cedar","Crater","Creek","Drift","Dust","Earthen","Elm","Fall","Flood","Fog","Forest","Grass","Green","Grove","Hail","Hazel","Hill","Hollow","Ice","Iron","Laurel","Maple","Moon","Moss","Mountain","Oaken","Peak","Pine","Plain","Rain","Ridge","River","Rock","Snow","Spring","Star","Stone","Storm","Summer","Sun","Thorn","Timber","Valley","Vine","Willow","Winter","Wood","Yew"],
	nm16: ["bark","basker","bearer","binder","blade","blesser","blossom","blossoms","booster","borne","braid","braider","braids","breaker","bringer","bruiser","caller","carver","catcher","chanter","charger","chaser","cleanser","conqueror","crest","dancer","darter","defender","divider","dreamer","drinker","eyes","fader","fighter","force","forcer","former","gatherer","glow","groom","groomer","guard","heart","herald","hold","hoof","laugh","leaf","leaper","leaves","limp","love","mane","mangle","march","mask","mind","muse","pass","pelt","petals","prowl","prowler","push","reign","rest","reveler","ride","rise","roamer","roar","run","runner","rush","rusher","scorn","screamer","seeker","shadow","shield","shifter","shine","sign","sleep","slumber","smile","smirk","spark","spell","stare","strength","tail","temper","thread","trampler","tree","twister","voice","volley","wander","wanderer","watch","watcher","whisper","whisperer","wish"]
};

const nameData = {
  "centaur": {
    male: [["nm1", "nm2", "nm3"]],
    female: [["nm1", "nm2", "nm3"]],
    surname:[["nm15", "nm16"]]
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
  let sr = nameData[subrace] || nameData[subrace.toLowerCase()] || nameData["centaur"];
  if (!sr) return "";

  const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "male" : "female") : (type === "f" ? "female" : "male");

  let first = "";

  if (g === "male") {
    const nTp = Math.floor(Math.random() * 5);
    let rnd = Math.floor(Math.random() * nameParts.nm1.length);
    let rnd2 = Math.floor(Math.random() * nameParts.nm2.length);
    let rnd5 = Math.floor(Math.random() * nameParts.nm7.length);

    if (nTp === 0) {
      while (nameParts.nm1[rnd] === "") {
        rnd = Math.floor(Math.random() * nameParts.nm1.length);
      }
      while (nameParts.nm7[rnd5] === "") {
        rnd5 = Math.floor(Math.random() * nameParts.nm7.length);
      }
      first = nameParts.nm1[rnd] + nameParts.nm2[rnd2] + nameParts.nm7[rnd5];
    } else {
      let rnd3 = Math.floor(Math.random() * nameParts.nm3.length);
      let rnd4 = Math.floor(Math.random() * nameParts.nm4.length);
      while (nameParts.nm3[rnd3] === nameParts.nm1[rnd] || nameParts.nm3[rnd3] === nameParts.nm7[rnd5]) {
        rnd3 = Math.floor(Math.random() * nameParts.nm3.length);
      }
      if (rnd2 === 0) {
        while (rnd4 === 0) {
          rnd4 = Math.floor(Math.random() * nameParts.nm4.length);
        }
      }
      if (nTp < 4) {
        first = nameParts.nm1[rnd] + nameParts.nm2[rnd2] + nameParts.nm3[rnd3] + nameParts.nm4[rnd4] + nameParts.nm7[rnd5];
      } else {
        let rnd6 = Math.floor(Math.random() * nameParts.nm5.length);
        let rnd7 = Math.floor(Math.random() * nameParts.nm6.length);
        while (nameParts.nm3[rnd3] === nameParts.nm5[rnd6] || nameParts.nm5[rnd6] === nameParts.nm7[rnd5]) {
          rnd6 = Math.floor(Math.random() * nameParts.nm5.length);
        }
        first = nameParts.nm1[rnd] + nameParts.nm2[rnd2] + nameParts.nm3[rnd3] + nameParts.nm4[rnd4] + nameParts.nm5[rnd6] + nameParts.nm6[rnd7] + nameParts.nm7[rnd5];
      }
    }
  } else {
    const nTp = Math.floor(Math.random() * 3);
    let rnd = Math.floor(Math.random() * nameParts.nm8.length);
    let rnd2 = Math.floor(Math.random() * nameParts.nm9.length);
    let rnd3 = Math.floor(Math.random() * nameParts.nm10.length);
    let rnd4 = Math.floor(Math.random() * nameParts.nm13.length);
    let rnd5 = Math.floor(Math.random() * nameParts.nm14.length);

    if (nTp < 2) {
      while (nameParts.nm8[rnd] === nameParts.nm10[rnd3] || nameParts.nm10[rnd3] === nameParts.nm14[rnd5]) {
        rnd3 = Math.floor(Math.random() * nameParts.nm10.length);
      }
      first = nameParts.nm8[rnd] + nameParts.nm9[rnd2] + nameParts.nm10[rnd3] + nameParts.nm13[rnd4] + nameParts.nm14[rnd5];
    } else {
      let rnd6 = Math.floor(Math.random() * nameParts.nm11.length);
      let rnd7 = Math.floor(Math.random() * nameParts.nm12.length);
      while (nameParts.nm12[rnd7] === nameParts.nm10[rnd3] || nameParts.nm12[rnd7] === nameParts.nm14[rnd5]) {
        rnd7 = Math.floor(Math.random() * nameParts.nm12.length);
      }
      first = nameParts.nm8[rnd] + nameParts.nm9[rnd2] + nameParts.nm10[rnd3] + nameParts.nm11[rnd6] + nameParts.nm12[rnd7] + nameParts.nm13[rnd4] + nameParts.nm14[rnd5];
    }
  }
  let last = "";
  if (sr.surname && sr.surname.length) {
    const pattern = sr.surname[Math.floor(Math.random() * sr.surname.length)];
    last = generateNameParts(pattern);
  }

  let nMs = ""
  if (g === "male") {
    nMs = (capitalize(first) + " " + capitalize(last)).trim() + " (m)"
  }
  else {
    nMs = (capitalize(first) + " " + capitalize(last)).trim() + " (f)"
  }

  return nMs + "###" + subrace;
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
