var nm1 = ["","","c","cr","h","l","m","n","r","s","sk","th","tr","v","z"];
var nm2 = ["ee","au","ie","ae","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u"];
var nm3 = ["d","g","m","n","nn","r","rr","sh","t","th","v","w","z"];
var nm4 = ["ie","a","a","e","i","o","a","a","e","i","o","a","a","e","i","o","a","a","e","i","o","a","a","e","i","o"];
var nm5 = ["l","n","r","th","v","y"];
var nm6 = ["a","e","i","o"];
var nm7 = ["","","ch","k","l","n","s","l","n","s","l","n","s"];

var nm8 = ["","","","","","","","","c","h","l","n","r","s","th","v","y","z"];
var nm9 = ["a","e","i"];
var nm10 = ["d","dr","gl","gn","gr","gv","l","ld","lk","ll","ln","lr","lv","m","mn","mt","n","nd","nk","nm","nn","nt","rk","rl","rn","rr","rv","v","vl","vr"];
var nm11 = ["a","a","e","e","i"];
var nm12 = ["d","dr","l","ll","ln","lr","lth","n","nt","nth","r","rn","rth","th","thr","v"];
var nm13 = ["a","a","e","i","i"];
var nm14 = ["","","","","","","","","","","","","l","ll","n","nn","s","ss","th"];

var br = "";

function legacyBrowserNameGen(type){
	$('#placeholder').css('textTransform', 'capitalize');
	var tp = type;
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
	nTp = Math.random() * 7 | 0;
	rnd = Math.random() * nm8.length | 0;
	rnd2 = Math.random() * nm9.length | 0;
	rnd3 = Math.random() * nm10.length | 0;
	rnd4 = Math.random() * nm13.length | 0;
	rnd5 = Math.random() * nm14.length | 0;
	if(nTp < 3){
		while(nm10[rnd3] === nm14[rnd5] || nm10[rnd3] === nm8[rnd]){
			rnd3 = Math.random() * nm10.length | 0;
		}
		nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm13[rnd4] + nm14[rnd5];
	}else{
		rnd6 = Math.random() * nm11.length | 0;
		rnd7 = Math.random() * nm12.length | 0;
		while(nm14[rnd5] === nm12[rnd7] || nm12[rnd7] === nm10[rnd3]){
			rnd7 = Math.random() * nm12.length | 0;
		}
		nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm11[rnd6] + nm12[rnd7] + nm13[rnd4] + nm14[rnd5];
	}
	testSwear(nMs);
}

function nameMas(){
	nTp = Math.random() * 8 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd3 = Math.random() * nm3.length | 0;
	rnd4 = Math.random() * nm6.length | 0;
	rnd5 = Math.random() * nm7.length | 0;
	if(nTp < 7){
		while(nm3[rnd3] === nm7[rnd5] && nm3[rnd3] === nm1[rnd]){
			rnd3 = Math.random() * nm3.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm6[rnd4] + nm7[rnd5];
	}else{
		rnd6 = Math.random() * nm4.length | 0;
		rnd7 = Math.random() * nm5.length | 0;
		while(nm3[rnd5] === nm5[rnd3] && nm3[rnd5] === nm1[rnd]){
			rnd5 = Math.random() * nm3.length | 0;
		}
		while(rnd2 < 4 && rnd6 === 0){
			rnd2 = Math.random() * nm2.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd6] + nm5[rnd7] + nm6[rnd4] + nm7[rnd5];
	}
	testSwear(nMs);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "shadarkai";

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
