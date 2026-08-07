var nm1 = ["b","c","d","g","n","p","r"];
var nm2 = ["","d","l","n","r"];
var nm3 = ["ee","oo","ie","ou","a","e","i","o","u"];
var nm4 = ["hb","hp","hn","b","h","n","ng","p","ph","s","sh"];
var nm5 = ["bh","kh","rh","b","br","k","r"];
var nm6 = ["Ã«","Ã¼","Ã¶","a","a","e","e","i","o","a","a","e","e","i","o"];
var nm7 = ["ht","hr","hk","b","d","k","kh","l","n","r","t"];
var nm8 = ["a","a","e","e","i","o"];

function legacyBrowserNameGen(type){
	var tp = type;
	var br = "";
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		nameMas();
		while(nMs === ""){
			nameMas();
		}
		br = document.createElement('br');	
		element.appendChild(document.createTextNode(nMs));
		element.appendChild(br);
	}
	if(document.getElementById("result")){
		document.getElementById("placeholder").removeChild(document.getElementById("result"));
	}		
	document.getElementById("placeholder").appendChild(element);
}

function nameMas(){
	nTp = Math.random() * 8 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd3 = Math.random() * nm3.length | 0;
	rnd4 = Math.random() * nm4.length | 0;
	if(nTp < 4){
		rnd2 = Math.random() * nm2.length | 0;
		while(nm1[rnd] === nm2[rnd2]){
			rnd2 = Math.random() * nm2.length | 0;
		}
		nTmp = nm2[rnd2] + nm3[rnd3] + nm4[rnd4];
		nTmp = nTmp.charAt(0).toUpperCase() + nTmp.slice(1);
		nMs = nm1[rnd] + "'" + nTmp;
	}else if(nTp < 6){
		rnd2 = Math.random() * nm1.length | 0;
		nTmp = nm3[rnd3];
		nTmp = nTmp.charAt(0).toUpperCase() + nTmp.slice(1);
		nMs = nm1[rnd] + "'" + nTmp + nm4[rnd4] + "'" + nm1[rnd2] + "'" + nTmp + nm4[rnd4];
	}else{
		rnd2 = Math.random() * nm2.length | 0;
		rnd5 = Math.random() * nm5.length | 0;
		rnd6 = Math.random() * nm6.length | 0;
		rnd7 = Math.random() * nm7.length | 0;
		rnd8 = Math.random() * nm8.length | 0;
		rnd9 = Math.random() * nm4.length | 0;
		if(nTp === 6){
			while(rnd7 < 3 && rnd9 < 3){
				rnd9 = Math.random() * nm4.length | 0;
			}
			nTmp = nm2[rnd2] + nm3[rnd3] + nm4[rnd4] + "-" + nm5[rnd5] + nm6[rnd6] + nm7[rnd7] + nm8[rnd8] + nm4[rnd9];
			nTmp = nTmp.charAt(0).toUpperCase() + nTmp.slice(1);
			nMs = nm1[rnd] + "'" + nTmp;
		}else{
			while(rnd5 < 3 && rnd9 < 3){
				rnd9 = Math.random() * nm4.length | 0;
			}
			while(rnd5 < 3 && rnd4 < 3){
				rnd4 = Math.random() * nm4.length | 0;
			}
			nTmp = nm2[rnd2] + nm3[rnd3] + nm7[rnd7] + nm8[rnd8] + nm4[rnd9] + "'" + nm5[rnd5] + nm6[rnd6] + nm4[rnd4];
			nTmp = nTmp.charAt(0).toUpperCase() + nTmp.slice(1);
			nMs = nm1[rnd] + "'" + nTmp;
		}
	}
	testSwear(nMs);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "grung";

function testSwear(value) {
    return value;
}

function __legacyGeneratedNames(type) {
    const names = [];
    const browserType = type === "f" ? 1 : 0;
    const originalSplice = Array.prototype.splice;
    const previousDollar = globalThis.$;
    const previousDocument = globalThis.document;
    const previousType = globalThis.tp;

    // Legacy browser generators removed chosen entries to avoid duplicates in
    // a ten-name screen. Keep their selection logic without consuming the
    // source arrays, allowing the CLI quantity contract to reach 100 safely.
    Array.prototype.splice = function(start, deleteCount, ...items) {
        if (deleteCount === 1 && items.length === 0) {
            return [this[start]];
        }
        return originalSplice.call(this, start, deleteCount, ...items);
    };

    globalThis.tp = browserType;
    globalThis.$ = function() {
        return { css() {} };
    };
    globalThis.document = {
        createTextNode(value) {
            return { __nameText: String(value ?? "") };
        },
        createElement() {
            return {
                setAttribute() {},
                appendChild(node) {
                    if (node && Object.hasOwn(node, "__nameText")) {
                        const value = node.__nameText.trim();
                        if (value && value !== "undefined") names.push(value);
                    }
                }
            };
        },
        getElementById(id) {
            if (id === "result") return null;
            return {
                appendChild() {},
                removeChild() {}
            };
        }
    };

    try {
        legacyBrowserNameGen(browserType);
    } finally {
        Array.prototype.splice = originalSplice;
        globalThis.$ = previousDollar;
        globalThis.document = previousDocument;
        globalThis.tp = previousType;
    }
    return names;
}

function capitalizeName(value) {
    return String(value)
        .trim()
        .split(/\s+/)
        .map(part => part ? part.charAt(0).toUpperCase() + part.slice(1) : "")
        .join(" ");
}

function generateName(type = "b") {
    const normalized = ["m", "f", "b"].includes(type) ? type : "b";
    const gender = normalized === "b"
        ? (Math.random() < 0.5 ? "m" : "f")
        : normalized;
    const generated = __legacyGeneratedNames(gender);
    if (!generated.length) {
        throw new Error(`No name was generated for ${__legacyRace}`);
    }
    const selected = generated[Math.floor(Math.random() * generated.length)];
    return `${capitalizeName(selected)} (${gender})###${__legacyRace}`;
}

if (typeof module !== "undefined") {
    module.exports = { generateName };
}

if (typeof require !== "undefined" && require.main === module) {
    let gender = String(process.argv[2] || "b").toLowerCase();
    if (!["m", "f", "b"].includes(gender)) gender = "b";
    const quantity = Math.min(
        Math.max(Number.parseInt(process.argv[3], 10) || 1, 1),
        100
    );
    for (let index = 0; index < quantity; index += 1) {
        console.log(generateName(gender));
    }
}
