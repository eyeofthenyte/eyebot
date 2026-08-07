var nm1 = ["","","","","","h","m","n","s","sh","ss","ssh","sz","t","th","y","z","zh","zs"];
var nm2 = ["a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","oa","ui"];
var nm3 = ["h","hl","htl","hl","hs","hsh","k","kh","kl","ktl","ks","l","lk","ls","ltl","lts","lsh","m","n","s","sh","ss","st","stl","sz","sk","t","tl","ts","tsh","tsz","tz","tstl","zs","zh","zsh","zt","ztl"];
var nm4 = ["h","hs","hl","l","ll","s","sh","ss","shl","t","th","y","z","zh"];
var nm5 = ["a","i","u","a","i","u","a","i","u","a","i","u","a","i","u","a","i","u","ie","ia","ei","ee","iu","ui"];
var nm6 = ["","","","","","","","","h","h","l","ll","s","ss","sh"];

var br = "";

function legacyBrowserNameGen(type){
	$('#placeholder').css('textTransform', 'capitalize');
	var tp = type;
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
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd3 = Math.random() * nm3.length | 0;
	rnd4 = Math.random() * nm5.length | 0;
	rnd5 = Math.random() * nm6.length | 0;
	if(i < 6){
		while(nm1[rnd] === nm3[rnd3] || nm3[rnd3] === nm6[rnd5]){
			rnd3 = Math.random() * nm3.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm5[rnd4] + nm6[rnd5];
	}else{
		rnd6 = Math.random() * nm4.length | 0;
		rnd7 = Math.random() * nm2.length | 0;
		while(nm3[rnd4] === nm4[rnd6] || nm4[rnd6] === nm6[rnd5]){
			rnd6 = Math.random() * nm4.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm2[rnd7] + nm4[rnd6] + nm5[rnd4] + nm6[rnd5];
	}
	testSwear(nMs);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "yuanti";

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
