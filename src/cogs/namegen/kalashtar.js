var nm1 = ["b","c","ch","d","g","gh","h","k","kh","l","m","n","s","t","v","z"];
var nm2 = ["a","e","o","a","e","o","i"];
var nm3 = ["l","n","r","s","v","w","y","z"];
var nm4 = ["a","a","e","i","i","o"];
var nm5 = ["ulad","hareth","khad","kosh","melk","tash","vash"];
var nm6 = ["ashana","ashtai","ishara","nari","tara","vakri"];

var nm7 = ["d","h","g","gh","k","kh","m","n","r","sh","sht","t","v","z"];
var nm8 = ["a","e","i","o","u"];
var nm9 = ["dr","kr","l","ld","ldr","lr","n","r","rr","v","z"];
var nm10 = ["ai","ei","ia","a","e","i","a","e","i","a","e","i","a","e","i","a","e","i"];
var nm11 = ["","","","","","d","l","lk","n","ns","nt","s","ss","sh","th"];
var nTp = 0;
var br = "";

function legacyBrowserNameGen(type){
	var tp = type;
	$('#placeholder').css('textTransform', 'capitalize');
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		nameMas();
		while(nMs === ""){
			nameMas();
		}
		if(i < 5){
			if(tp === 1){
				rnd = Math.random() * 3 | 0;
				if(nTp === 0 || nTp === 3){
					nMs = nMs + nm6[rnd];
				}else{
					rnd += 3;
					nMs = nMs + nm6[rnd];
				}
			}else{
				if(nTp === 0 || nTp === 3){
					nMs = nMs + nm5[0];
				}else{
					rnd = Math.random() * 5 | 0;
					nMs = nMs + nm5[rnd + 1];
				}
			}
		}else{
			nTps = Math.random() * 2 | 0;
			rnd = Math.random() * nm7.length | 0;
			rnd2 = Math.random() * nm8.length | 0;
			rnd3 = Math.random() * nm11.length | 0;
			if(nTps === 0 && nMs.length > 1){
				if(nTp === 0 || nTp === 2){
					if(rnd3 < 5){
						rnd3 += 5;
					}
					nMs = nMs + nm8[rnd2] + nm11[rnd3];
				}else{
					nMs = nMs + nm7[rnd] + nm8[rnd2] + nm11[rnd3];
				}
			}else{
				rnd4 = Math.random() * nm9.length | 0;
				rnd5 = Math.random() * nm10.length | 0;
				if(nTp === 0 || nTp === 2){
					nMs = nMs + nm8[rnd2] + nm9[rnd4] + nm10[rnd5] + nm11[rnd3];
				}else{
					nMs = nMs + nm7[rnd] + nm8[rnd2] + nm9[rnd4] + nm10[rnd5] + nm11[rnd3];
				}
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

function nameMas(){
	nTp = Math.random() * 4 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	if(nTp < 2){
		if(nTp === 0){
			nMs = nm1[rnd];
		}else{
			nMs = nm1[rnd] + nm2[rnd2];
		}
	}else{
		rnd3 = Math.random() * nm3.length | 0;
		rnd4 = Math.random() * nm4.length | 0;
		if(nTp === 2){
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3];
		}else{
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd4];
		}
	}
	testSwear(nMs);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "kalashtar";

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
