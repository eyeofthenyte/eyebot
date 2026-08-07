var nm1 = ["Al","Aro","Bar","Bel","Cor","Cra","Dav","Dor","Eir","El","Fal","Fril","Gaer","Gra","Hal","Hor","Ian","Ilo","Jam","Kev","Kri","Leo","Lor","Mar","Mei","Nil","Nor","Ori","Os","Pan","Pet","Quo","Raf","Ri","Sar","Syl","Tra","Tyr","Uan","Ul","Van","Vic","Wal","Wil","Xan","Xav","Yen","Yor","Zan","Zyl"];
var nm2 = ["avor","ben","borin","coril","craes","deyr","dithas","elor","enas","faelor","faerd","finas","fyr","gotin","gretor","homin","horn","kas","koris","lamir","lanann","lumin","minar","morn","nan","neak","neiros","orin","ovar","parin","phanis","qarim","qinor","reak","ril","ros","sariph","staer","torin","tumil","valor","voril","warith","word","xian","xiron","yeras","ynor","zaphir","zaren"];
var nm3 = ["Alu","Aly","Ar","Bren","Byn","Car","Co","Dar","Del","El","Eli","Fae","Fha","Gal","Gif","Haly","Ho","Ile","Iro","Jen","Jil","Kri","Kys","Les","Lora","Ma","Mar","Mare","Neri","Nor","Ol","Ophi","Phaye","Pri","Qi","Que","Rel","Res","Sael","Saf","Syl","Ther","Tyl","Una","Uri","Ven","Vyl","Win","Wol","Xil","Xyr","Yes","Yll","Zel","Zin"];
var nm4 = ["aerys","anys","bellis","bwynn","cerys","charis","diane","dove","elor","enyphe","faen","fine","galyn","gwynn","hana","hophe","kaen","kilia","lahne","lynn","mae","malis","mythe","nalore","noa","nys","ona","phira","pisys","qarin","qwyn","rila","rora","seris","stine","sys","thana","theris","tihne","trana","viel","vyre","walyn","waris","xaris","xipha","yaries","yra","zenya","zira"];

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
	nMs = nm3[rnd] + nm4[rnd2];
	testSwear(nMs);
}

function nameMas(){
	rnd = Math.floor(Math.random() * nm1.length);
	rnd2 = Math.floor(Math.random() * nm2.length);
	nMs = nm1[rnd] + nm2[rnd2];
	testSwear(nMs);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "halfelf";

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
