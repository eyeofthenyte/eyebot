const nameParts = {
  nm1: ["","","","","","c","cl","cr","d","g","gr","h","k","kh","kl","kr","q","qh","ql","qr","r","rh","s","y","z"],
  nm2: ["a","e","i","u","a","e","i","u","a","e","i","u","a","e","i","u","a","e","i","u","a","e","i","u","a","e","i","u","ae","aia","ee","oo","ou","ua","uie"],
  nm3: ["c","cc","k","kk","l","ll","q","r","rr"],
  nm4: ["a","e","i","a","e","i","a","e","i","a","e","i","a","e","i","aa","ea","ee","ia","ie"],
  nm5: ["","","","","c","ck","d","f","g","hk","k","l","r","rr","rc","rk","rrk","s","ss"],
};
const nameData = {
  "arakocra": {
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
  let sr = nameData[subrace] || nameData[subrace.toLowerCase()] || nameData["arakocra"];
  if (!sr) return "";

  const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "male" : "female") : (type === "f" ? "female" : "male");

  const i = Math.floor(Math.random() * 10);
  let nMs;

  if (i < 5) {
    let rnd = Math.floor(Math.random() * nameParts.nm1.length);
    let rnd2 = Math.floor(Math.random() * nameParts.nm2.length);
    let rnd3 = Math.floor(Math.random() * nameParts.nm5.length);
    let attempts = 0;

    while (nameParts.nm1[rnd] === nameParts.nm5[rnd3] && attempts++ < 10) {
      rnd3 = Math.floor(Math.random() * nameParts.nm5.length);
    }

    nMs = nameParts.nm1[rnd] + nameParts.nm2[rnd2] + nameParts.nm5[rnd3] + " (m)";
  } else {
    let rnd = Math.floor(Math.random() * nameParts.nm1.length);
    let rnd2 = Math.floor(Math.random() * nameParts.nm2.length);
    let rnd3 = Math.floor(Math.random() * nameParts.nm5.length);
    let rnd4 = Math.floor(Math.random() * nameParts.nm3.length);
    let rnd5 = Math.floor(Math.random() * nameParts.nm4.length);
    nMs = nameParts.nm1[rnd] + nameParts.nm2[rnd2] + nameParts.nm3[rnd4] + nameParts.nm4[rnd5] + nameParts.nm5[rnd3] + " (f)";
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
