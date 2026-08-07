const nameParts = {
nm1: ["Ali","Ar","Ba","Bal","Bel","Bha","Bren","Caer","Calu","Dur","Do","Dra","Era","Faer","Fro","Gre","Ghe","Gora","He","Hi","Ior","Jin","Jar","Kil","Kriv","Lor","Lumi","Mar","Mor","Med","Nar","Nes","Na","Oti","Orla","Pri","Pa","Qel","Ravo","Ras","Rho","Sa","Sha","Sul","Taz","To","Trou","Udo","Uro","Vor","Vyu","Vrak","Wor","Wu","Wra","Wul","Xar","Yor","Zor","Zra"],
nm2: ["barum","bor","broth","ciar","crath","daar","dhall","dorim","farn","fras","gar","ghull","grax","hadur","hazar","jhan","jurn","kax","kris","kul","lasar","lin","mash","morn","naar","prax","qiroth","qrin","qull","rakas","rash","rinn","roth","sashi","seth","skan","trin","turim","varax","vroth","vull","warum","wunax","xan","xiros","yax","ythas","zavur","zire","ziros"],
nm3: ["Ari","A","Bi","Bel","Cris","Ca","Drys","Da","Erli","Esh","Fae","Fen","Gur","Gri","Hin","Ha","Irly","Irie","Jes","Jo","Ka","Kel","Ko","Lilo","Lora","Mal","Mi","Na","Nes","Nys","Ori","O","Ophi","Phi","Per","Qi","Quil","Rai","Rashi","So","Su","Tha","Ther","Uri","Ushi","Val","Vyra","Welsi","Wra","Xy","Xis","Ya","Yr","Zen","Zof"],
nm4: ["birith","bis","bith","coria","cys","dalynn","drish","drith","faeth","fyire","gil","gissa","gwen","hime","hymm","karyn","kira","larys","liann","lyassa","meila","myse","norae","nys","patys","pora","qorel","qwen","rann","riel","rina","rinn","rish","rith","saadi","shann","sira","thibra","thyra","vayla","vyre","vys","wophyl","wyn","xiris","xora","yassa","yries","zita","zys"],

nm5: ["","","","","c","cl","cr","d","dr","f","g","k","kl","kr","l","m","my","n","ny","pr","sh","t","th","v","y"],
nm6: ["a","e","i","a","e","i","o","u","a","e","i","a","e","i","o","u","a","e","i","a","e","i","o","u","aa","ia","ea","ua","uu"],
nm7: ["c","cc","ch","lm","lk","lx","ld","lr","ldr","lt","lth","mb","mm","mp","mph","mr","mt","nk","nx","nc","p","ph","r","rd","rj","rn","rrh","rth","st","tht","x"],
nm8: ["c","cm","cn","d","j","k","km","l","n","nd","ndr","nk","nsht","nth","r","s","sht","shkm","st","t","th","x"],
nm9: ["d","j","l","ll","m","n","nd","rg","r","rr","rd"],
nm10: ["c","d","k","l","n","r","s","sh","th"],
};

const nameData = {
  "dragonborn": {
    male: [["nm1", "nm2"]],
    female: [["nm3", "nm4"]]
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
  let sr = nameData[subrace] || nameData[subrace.toLowerCase()] || nameData["dragonborn"];
  if (!sr) return "";

  const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "male" : "female") : (type === "f" ? "female" : "male");

  const patternList = sr[g];
  const pattern = Array.isArray(patternList[0])
    ? patternList[Math.floor(Math.random() * patternList.length)]
    : patternList;

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

function generateSurname() {
  const ntp = Math.floor(Math.random() * 10);
  const rnd = Math.floor(Math.random() * nameParts.nm5.length);
  const rnd2 = Math.floor(Math.random() * nameParts.nm6.length);
  let rnd3 = Math.floor(Math.random() * nameParts.nm7.length);
  const rnd4 = Math.floor(Math.random() * nameParts.nm6.length);
  const rnd5 = Math.floor(Math.random() * nameParts.nm10.length);
  while (nameParts.nm7[rnd3] === nameParts.nm5[rnd] || nameParts.nm7[rnd3] === nameParts.nm10[rnd5]) {
    rnd3 = Math.floor(Math.random() * nameParts.nm7.length);
  }

  if (ntp < 4) {
    return nameParts.nm5[rnd] + nameParts.nm6[rnd2] + nameParts.nm7[rnd3] + nameParts.nm6[rnd4] + nameParts.nm10[rnd5];
  } else {
    const rnd6 = Math.floor(Math.random() * nameParts.nm6.length);
    let rnd7 = Math.floor(Math.random() * nameParts.nm8.length);
    while (nameParts.nm7[rnd3] === nameParts.nm8[rnd7] || nameParts.nm8[rnd7] === nameParts.nm10[rnd5]) {
      rnd7 = Math.floor(Math.random() * nameParts.nm8.length);
    }
    if (ntp < 7) {
      return nameParts.nm5[rnd] + nameParts.nm6[rnd2] + nameParts.nm7[rnd3] + nameParts.nm6[rnd4] + nameParts.nm8[rnd7] + nameParts.nm6[rnd6] + nameParts.nm10[rnd5];
    } else {
      const rnd8 = Math.floor(Math.random() * nameParts.nm6.length);
      let rnd9 = Math.floor(Math.random() * nameParts.nm9.length);
      while (nameParts.nm9[rnd9] === nameParts.nm8[rnd7] || nameParts.nm9[rnd9] === nameParts.nm10[rnd5]) {
        rnd9 = Math.floor(Math.random() * nameParts.nm9.length);
      }
      return nameParts.nm5[rnd] + nameParts.nm6[rnd2] + nameParts.nm7[rnd3] + nameParts.nm6[rnd4] + nameParts.nm8[rnd7] + nameParts.nm6[rnd6] + nameParts.nm9[rnd9] + nameParts.nm6[rnd8] + nameParts.nm10[rnd5];
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
