const nameParts = {
nm1: ["b","br","d","dr","fr","g","gh","gr","k","kh","kr","sch","schn","sn","sh","t","th","w","z","zh"],
nm2: ["a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","ie","ee","ai","aa","ei"],
nm3: ["ck","ckt","ckh","cn","dg","dl","ddl","dm","g","gg","gn","gl","ggl","kt","kth","kl","kn","lsch","lw","lth","lk","lkr","ltr","ll","ld","ldr","nth","nt","nd","ndr","ntr","rbl","rthm","rt","rdr","t","tt","tl","ttl","tr","thr","th"],
nm4: ["a","e","i","u"],
nm5: ["","","","c","ck","d","g","l","ll","ld","n","nd","nk","r","rs","t"],

nm6: ["","","","","","b","d","fr","gh","gr","h","k","kh","kr","l","m","n","s","sh","sn","sch","schn","t","th","y","w","z"],
nm7: ["a","e","i","u"],
nm8: ["ckn","d","dl","dd","g","gg","gd","gn","gh","l","ll","lg","lm","lv","ls","lsch","lsh","m","mk","mg","n","nn","nt","ny","ng","nk","rb","rg","rl","rsh","rv","rt","rth","rs","s","ss","sh","sn","sk","sg","sl","th","t","tr","thr","v","vr","vy","z"],
nm9: ["a","e","i","a","e","i","a","e","i","a","e","i","ee","ie","ei","ai","ia"],
nm10: ["d","dd","l","ll","ld","ln","lk","n","nn","r","rr","ry","rt","sh","sch"],
nm11: ["a","e","i","a","i","a","i"],
nm12: ["","","","","","","","d","dd","h","l","ll","n","nn","s","ss"],

nm13: ["adamant","agate","alabaster","alloy","amethyst","basalt","bedrock","block","boulder","brass","brick","bronze","clay","cobalt","cobble","copper","crag","crystal","deposit","diamond","dirt","dust","emerald","flint","fossil","garnet","gem","geo","geode","gold","granite","gravel","grime","ground","ingot","iron","jade","jewel","joint","lapis","lazuli","lead","lime","lodge","lump","marble","mason","metal","mill","mineral","mold","nickel","nugget","obsidian","onyx","opal","ore","pebble","pellet","peridot","pit","quartz","rock","rough","rubble","ruby","sand","sapphire","scrap","seam","shelf","silver","slab","slate","smelt","soil","spinel","steel","stone","stony","sturdy","terra","tile","tin","topaz","turf","wedge","wire","zinc","zircon"],
nm14: ["back","basher","bender","biter","bleacher","bone","bones","brander","breaker","bringer","browser","brusher","carrier","carver","catcher","checker","cheek","chest","chewer","chin","chiseler","cleaner","cleanser","collector","counter","crusher","cutter","designer","digger","duster","ear","eye","eyes","face","feet","finder","finger","fingers","fist","foot","forger","gatherer","gazer","getter","grasper","grinder","hand","head","heart","hewer","holder","knuckle","leg","legs","lifter","loader","maker","marker","mask","melter","mender","merger","molder","moulder","mug","neck","nose","packer","presser","pusher","rater","recorder","rinser","saver","scanner","scratcher","sealer","searcher","seeker","seizer","senser","shaper","shoveler","skin","smasher","smelter","snatcher","sniffer","sorter","splitter","stamper","stasher","stocker","surveyor","sweeper","switcher","teeth","temperer","tooth","trader","twirler","twister","vein","viewer","warper","watcher"],
};
const nameData = {
  "deepgnome": {
    male: [["nm1", "nm2", "nm3", "nm4", "nm5"]],
    female: [["nm6", "nm7", "nm8", "nm9"]],
    surname:[["nm13", "nm14"]]
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
  let sr = nameData[subrace] || nameData[subrace.toLowerCase()];
  if (!sr) return "";

  const g = (type === "b" || type === "") ? (Math.random() < 0.5 ? "female" : "male") : (type === "f" ? "female" : "male");

  let first = "";

  // Manual construction for Deep Gnome or other hardcoded races
  if (subrace.toLowerCase() === "deepgnome") {
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
      let i = Math.floor(Math.random() * 10);
      let rnd = Math.floor(Math.random() * nameParts.nm6.length);
      let rnd2 = Math.floor(Math.random() * nameParts.nm7.length);
      let rnd3 = Math.floor(Math.random() * nameParts.nm8.length);
      let rnd4 = Math.floor(Math.random() * nameParts.nm9.length);

      if (i < 5) {
        let rnd5 = Math.floor(Math.random() * nameParts.nm12.length);
        if (rnd < 5 && rnd5 < 7) {
          while (rnd5 < 7) {
            rnd5 = Math.floor(Math.random() * nameParts.nm12.length);
          }
        }
        while (nameParts.nm8[rnd3] === nameParts.nm6[rnd] || nameParts.nm8[rnd3] === nameParts.nm12[rnd5]) {
          rnd3 = Math.floor(Math.random() * nameParts.nm8.length);
        }
        first = nameParts.nm6[rnd] + nameParts.nm7[rnd2] + nameParts.nm8[rnd3] + nameParts.nm9[rnd4] + nameParts.nm12[rnd5];
      } else {
        let rnd5 = Math.floor(Math.random() * nameParts.nm10.length);
        let rnd6 = Math.floor(Math.random() * nameParts.nm11.length);
        while (nameParts.nm10[rnd5] === nameParts.nm8[rnd3] || nameParts.nm8[rnd3] === nameParts.nm6[rnd]) {
          rnd3 = Math.floor(Math.random() * nameParts.nm8.length);
        }
        first = nameParts.nm6[rnd] + nameParts.nm7[rnd2] + nameParts.nm8[rnd3] + nameParts.nm9[rnd4] + nameParts.nm10[rnd5] + nameParts.nm11[rnd6];
      }
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
