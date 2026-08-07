var nm1 = ["Am","Ar","Ara","Aza","Bar","Bra","Bran","Bru","Da","Dar","Dor","Dra","Dro","Du","Duu","Fa","Far","Fe","Fer","Fur","Gan","Gra","Gran","Gre","Gro","Gru","Hra","Hu","Ka","Kar","Kha","Kra","Kro","Ma","Mar","Mu","Muu","Na","Nar","Nir","Nu","On","Or","Ora","Oro","Ra","Ran","Rhu","Rin","Ru","Sa","Sha","Shra","Sra","Un","Una","Ur","Ura","Xa","Xha","Xo","Zar","Zra"];
var nm2 = ["d","d","d","dahn","dak","dar","dh","dh","dh","dran","gahr","gh","gh","gh","gor","k","k","kh","kh","kahr","kar","khar","kiak","kk","kk","kk","kk","kk","kran","lag","lahr","lian","lid","lis","lla","llak","loth","mag","mak","miak","mir","nag","nak","niar","nod","rad","rag","rak","ram","rath","rek","rg","rg","rg","rg","rm","rm","rm","rm","rra","rth","rth","rth","rth","ruk","rzth","rzth","rzth","tar","th","th","th","th","tig","zad","zag","zak","zar","zeg","zirg","zth"];
var nm3 = ["Ad","Alm","Ar","Arw","Ash","Dah","Dhar","Dolm","Dran","El","Ell","Erzh","Esz","Ezh","Genr","Grel","Grin","Halm","Han","Harn","Heln","Ihr","Iln","Imm","Immil","Iz","Jan","Kan","Kharm","Khaz","Krez","Laz","Lez","Lhash","Lir","Lor","Magd","Marm","Meir","Mir","Nagr","Nah","Nalm","Nash","Niar","Ohn","Or","Rasz","Rez","Sham","Sharm","Shund","Sil","Um","Ur","Uw","Vith"];
var nm4 = ["a","ah","aka","al","alin","alla","ane","anith","anya","arah","arin","aya","ayah","ayis","eah","eka","ekus","el","ela","elna","elya","elzal","ena","enah","era","erah","erath","erra","eth","eya","ihn","ila","ilias","ilzin","in","ina","ines","ira","iren","iris","ith","iza","la","mina","mira","nara","nel","nera","nia","niya","ra","ya","yara","zin"];

function legacyBrowserNameGen(type){
	var tp = type;
	var br = "";
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		if(tp === 1){
			nameFem();
			while(nMs === ""){
				nameFem();
			}
		}else{
			nameMas();
			while(nMs === ""){
				nameMas();
			}
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
function nameFem(){
	rnd = Math.floor(Math.random() * nm3.length);
	rnd2 = Math.floor(Math.random() * nm4.length);
	charL = nm3[rnd].charAt(nm3[rnd].length -1);
	charF = nm4[rnd2].charAt(0);
	while(charL === charF){
		rnd2 = Math.floor(Math.random() * nm4.length);
		charF = nm4[rnd2].charAt(0);
	}
	nMs = nm3[rnd] + nm4[rnd2];
	testSwear(nMs);
}

function nameMas(){
	rnd = Math.floor(Math.random() * nm1.length);
	rnd2 = Math.floor(Math.random() * nm2.length);
	charL = nm1[rnd].charAt(nm1[rnd].length -1);
	charF = nm2[rnd2].charAt(0);
	while(charL === charF){
		rnd2 = Math.floor(Math.random() * nm2.length);
		charF = nm2[rnd2].charAt(0);
	}
	nMs = nm1[rnd] + nm2[rnd2];
	testSwear(nMs);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "githzerai";

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
