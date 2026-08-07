var nmFF = ["Aam","Ane","Are","Ase","Den","Duo","Duu","Em","Enti","Era","Este","Fas","Fen","Hene","Hes","Hila","Hine","Ias","Ire","Ki","Kia","Kuo","Laan","Line","Loo","Mira","Mou","Muu","Nan","Nea","Neo","Noo","Nuo","Oen","Oes","Raas","Ras","Reo","Rina","Sees","Seo","Sina","Tee","Tes","Tia","Tina","Uova","Veo","Vi","Via","Weo","Wina"];
var nmFL = ["dane","dera","din","dra","fa","fen","fin","kane","kea","ken","kia","la","las","len","lian","lin","lo","mas","me","mi","min","mira","na","nan","nas","nim","nore","nu","pe","pen","ra","ren","res","rin","ris","ru","sen","sia","ta","ter","tin","tra","tred","tri","trin","tris","ven","vena","vera","vin","za","zara","zin"];
var nmMF = ["Ar","Are","Aste","Bar","Bjor","Bran","Car","Cod","Da","Djar","Djun","Doen","Dor","Drin","Dur","Far","Foos","Gar","Goe","Gra","Gran","Gun","Har","Hir","Hun","Ja","Jar","Kar","Kin","Kir","Koo","Koor","Kran","Krum","Kur","Man","Min","Mir","Mun","Nar","Noe","Noo","Pod","Rak","Te","Tir","Toon","Trak","Tur","Zam","Zar","Zun"];
var nmML = ["ban","baran","bur","dak","daran","diar","dor","drin","fajar","faruk","fran","furan","gajan","garak","giran","gur","jar","kan","kar","karat","kun","kurat","kus","manuk","marin","maruk","narak","nark","narun","nir","nus","paran","piran","raduk","rak","rakar","ranak","rapak","ras","rat","rilak","rios","ron","rus","rut","tagar","taruk","tiran","toron","turok","tus","vrak"];
var nmSF = ["Agile","Bear","Bold","Boulder","Brave","Bright","Fearless","Fist","Glory","Goblin","Great","Heavy","Honor","Iron","Jagged","Keen","Nimble","Orc","Rock","Rugged","Sharp","Silent","Single","Steady","Steel","Stone","Storm","Stout","Strong","Swift","Thick","Thunder","Tough","Truth","Valiant","Vigil","Wolf"];
var nmSL = ["bane","body","eye","fighter","fist","fury","hand","heart","hide","hoof","horn","horns","hunter","leader","mind","pelt","roar","runner","skin","skull","slash","slayer","speaker","step","striker","vigor","walker","warrior"];

function legacyBrowserNameGen(type){
	var tp = type;
	var br = "";
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		rnd = Math.floor(Math.random() * nmSF.length);
		rnd2 = Math.floor(Math.random() * nmSL.length);
		nSr = nmSF[rnd] + nmSL[rnd2];
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
		nMs = nMs + " " + nSr;
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
	rnd = Math.floor(Math.random() * nmFF.length);
	rnd2 = Math.floor(Math.random() * nmFL.length);
	nMs = nmFF[rnd] + nmFL[rnd2];
	testSwear(nMs);
}

function nameMas(){
	if(i < 5){
		rnd = Math.floor(Math.random() * nmFF.length);
		rnd2 = Math.floor(Math.random() * nmFL.length);
		nMs = nmFF[rnd] + nmFL[rnd2];
	}else{
		rnd = Math.floor(Math.random() * nmMF.length);
		rnd2 = Math.floor(Math.random() * nmML.length);
		nMs = nmMF[rnd] + nmML[rnd2];
	}
	testSwear(nMs);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "minotaur";

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
