var nmMFf = ["Ban","Bar","Dal","Dam","Dun","Dur","Fas","Fin","Kan","Kin","Kor","Lan","Lim","Lon","Man","Mar","Mas","Mid","Mor","Mur","Nam","Nor","Rad","Ran","Ras","Rod","San","Sin","Tor","Tum"];
var nmMFl = ["darras","darris","dommar","donnir","durrun","farran","fidden","garron","kammin","karran","lammir","larrin","mannor","marden","mennar","mennor","mindin","mirron","morrin","murrin","norren","norten","rammas","sammas","sannim","sarrin","sarris","sorran","tarrin","torrin"];
var nmMSf = ["Barrun","Burrin","Darras","Farran","Farrin","Fidden","Garrin","Harren","Harrun","Karrat","Karren","Ketten","Korrin","Larras","Lommir","Lorrin","Marrad","Mirren","Mirrun","Morrin","Parran","Purren","Tarris","Torren","Torrim","Turrus","Venner","Vunnar","Zakkan","Zarrak"];
var nmMSl = ["bar","bor","bun","das","din","dun","dur","fas","fum","gar","gun","kas","kin","las","lis","mar","mas","min","mur","nas","nim","nor","pan","rak","ras","tor","tur","zad","zim","zor"];
var nmFF = ["Allin","Ashin","Bunn","Dann","Darn","Diss","Enn","Eril","Fenn","Fert","Firr","Fiss","Genn","Grin","Kalk","Kenn","Kers","Krin","Lerm","Less","Linn","Lorr","Minn","Mirt","Mist","Nem","Niss","Shall","Shan","Shenn","Tarr","Taz","Tell","Tin","Tirr","Tris","Wenn","Zar","Zaz","Zell"];
var nmFL = ["ahai","akei","alin","amai","anai","annar","annas","arris","arrel","arresh","artish","asha","atish","elbis","embin","enna","ennash","entah","eris","erla","erlis","imai","imbel","imei","immesh","inah","inash","inda","inna","innem","irrah","ishai","issa","itas","onnes","onteh","orda","oren","oris","orren"];

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
	rnd = Math.floor(Math.random() * nmFF.length);
	rnd2 = Math.floor(Math.random() * nmFL.length);
	nMs = nmFF[rnd] + nmFL[rnd2];
	testSwear(nMs);
}

function nameMas(){
	if(i < 5){
		rnd = Math.floor(Math.random() * nmMFf.length);
		rnd2 = Math.floor(Math.random() * nmMFl.length);
		nMs = nmMFf[rnd] + nmMFl[rnd2];
	}else{
		rnd = Math.floor(Math.random() * nmMSf.length);
		rnd2 = Math.floor(Math.random() * nmMSl.length);
		nMs = nmMSf[rnd] + nmMSl[rnd2];
	}
	testSwear(nMs);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "wilden";

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
