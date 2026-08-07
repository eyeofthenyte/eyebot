const nameParts = {
nm1: ["Ad","Ans","Ars","Ay","Bav","Ber","Dar","Eb","Ely","Er","Ery","Gal","Gam","Gar","Hiy","Iann","Ker","Mah","Mahr","Man","Mar","Math","Mor","Nat","Neh","Ner","Ob","Or","Rah","Ron","Sam","Sav","Ser","Sor","Tar","Tav","Vat","Ver","Zach","Zay"],
nm2: ["ab","ach","ad","ahk","ahm","ahn","ahr","ak","al","am","an","ar","as","ath","eb","ech","ed","ehr","ek","el","em","en","er","es","iah","ihm","ihn","im","in","ir","is"],
nm3: ["Ab","Ad","An","Ar","Ash","Chan","Dan","Dar","Dav","Din","Elk","Eran","Eys","Han","Hav","Hen","Idr","Is","Jan","Jen","Kal","Kan","Kay","Len","Lih","Mah","Mar","Nal","Nav","Nom","Paz","Rav","Ren","Riy","Sad","Shar","Sir","Tar","Tel","Tir"],
nm4: ["a","ael","aen","ah","ahne","ana","anaeh","anael","anah","ane","anel","aniah","ara","araeh","are","ariah","ea","ehl","ek","el","ele","elle","era","ey","eya","i","ia","iah","im","ima"],

nm1: ["","","","","b","d","g","h","k","m","n","r","s","t","v","z"],
nm2: ["a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o","ia","ie","ea","ei"],
nm3: ["b","ch","d","h","hr","l","ly","m","n","nn","ns","r","rs","ry","t","th","v","y"],
nm4: ["a","e","i"],
nm5: ["b","ch","d","h","hk","hm","hn","hr","k","l","m","n","r","s","th"],

nm6: ["","","","","","ch","d","h","j","k","l","m","n","p","r","s","sh","t","th"],
nm7: ["a","e","i"],
nm8: ["b","d","dr","h","l","lk","m","n","r","s","sh","v","y","ys","z"],
nm9: ["a","e","i","a","e","i","a","e","i","a","e","i","a","e","i","a","e","i","ia","ae","ea"],
nm10: ["hn","l","ll","m","n","r","y"],
nm11: ["","","","","","","h","h","hl","k","l","l","n","n","m","m"],
};

const nameData = {
  "deva": {
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
  let sr = nameData[subrace] || nameData[subrace.toLowerCase()] || nameData["deva"];
  if (!sr) return "";

  const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "male" : "female") : (type === "f" ? "female" : "male");

  let first = "";
  const i = Math.floor(Math.random() * 10);

  if (subrace.toLowerCase() === "deva") {
    if (g === "male") {
      let rnd = Math.floor(Math.random() * nameParts.nm1.length);
      let rnd2 = Math.floor(Math.random() * nameParts.nm2.length);
      let rnd3 = Math.floor(Math.random() * nameParts.nm3.length);
      let rnd4 = Math.floor(Math.random() * nameParts.nm4.length);
      let rnd5 = Math.floor(Math.random() * nameParts.nm5.length);
      while (nameParts.nm3[rnd3] === nameParts.nm1[rnd] || nameParts.nm3[rnd3] === nameParts.nm5[rnd5]) {
        rnd3 = Math.floor(Math.random() * nameParts.nm3.length);
      }
      first = nameParts.nm1[rnd] + nameParts.nm2[rnd2] + nameParts.nm3[rnd3] + nameParts.nm4[rnd4] + nameParts.nm5[rnd5];
    } else {
      let rnd = Math.floor(Math.random() * nameParts.nm6.length);
      let rnd2 = Math.floor(Math.random() * nameParts.nm7.length);
      let rnd3 = Math.floor(Math.random() * nameParts.nm8.length);
      let rnd4 = Math.floor(Math.random() * nameParts.nm9.length);
      let rnd5 = Math.floor(Math.random() * nameParts.nm11.length);
      while (nameParts.nm8[rnd3] === nameParts.nm6[rnd] || nameParts.nm8[rnd3] === nameParts.nm11[rnd5]) {
        rnd3 = Math.floor(Math.random() * nameParts.nm8.length);
      }
      if (i < 6) {
        first = nameParts.nm6[rnd] + nameParts.nm7[rnd2] + nameParts.nm8[rnd3] + nameParts.nm9[rnd4] + nameParts.nm11[rnd5];
      } else {
        let rnd6 = Math.floor(Math.random() * nameParts.nm10.length);
        let rnd7 = Math.floor(Math.random() * nameParts.nm9.length);
        while (nameParts.nm10[rnd6] === nameParts.nm11[rnd5] || nameParts.nm10[rnd6] === nameParts.nm8[rnd3]) {
          rnd6 = Math.floor(Math.random() * nameParts.nm10.length);
        }
        first = nameParts.nm6[rnd] + nameParts.nm7[rnd2] + nameParts.nm8[rnd3] + nameParts.nm9[rnd4] + nameParts.nm10[rnd6] + nameParts.nm9[rnd7] + nameParts.nm11[rnd5];
      }
    }
  }

  let nMs = ""
  if (g === "male") {
      nMs = (capitalize(first)).trim() + " (m)"
  }
  else {
      nMs = (capitalize(first)).trim() + " (f)"
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
