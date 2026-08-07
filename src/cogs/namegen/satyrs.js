var nm1 = ["","","","d","f","k","n","p","sp","t","z"];
var nm2 = ["eo","y","a","e","i","o"];
var nm3 = ["f","k","l","m","n","nt","r"];
var nm4 = ["ia","y","a","e","i","y","a","e","i"];
var nm5 = ["k","l","m","n","pp","r","t","v","z"];
var nm6 = ["ia","a","i","o","o","o"];
var nm7 = ["","n","s","s","s","n","s","s","s","n","s","s","s"];

var nm8 = ["ch","d","k","l","n","t","x","y","z","",""];
var nm9 = ["ei","ai","oi","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o"];
var nm10 = ["fn","k","l","lp","n","nn","r","s","t","vr"];
var nm11 = ["a","e","i","i"];
var nm12 = ["d","l","n","r","y"];
var nm13 = ["ia","oi","oe","a","i","a","i","a","i","a","i","a","i","a","i"];

var nm14 = ["amber","auburn","bristle","bronze","copper","crimson","dapple","fawn","frazzle","frizzle","ginger","hazel","messy","orange","ragged","rough","scarlet","scraggy","scruffle","scruffy","shaggy","stubble","umber"];
var nm15 = ["back","beard","chin","crest","crown","fluff","fringe","fur","fuzz","hair","mane","ridge","ruff","tuft"];

var nm16 = ["dark","flat","free","great","hard","keen","little","nobble","proud","quick","skip","still","stout","strong","stubby","swift","twinkle"];
var nm17 = ["horn","horns","foot","hoof","hoofs","hooves","feet"];

var nm18 = ["Arrow","Bash","Basher","Berry","Bigby","Bitsy","Blaze","Blossom","Blush","Blusher","Bouncer","Bounder","Buster","Caper","Chip","Comet","Crimson","Cuddles","Curles","Dancer","Diamond","Digger","Dimple","Dimples","Dizzy","Dusty","Ember","Flounce","Flutters","Fuzz","Fuzzy","Gambol","Grace","Grouch","Happy","Hopper","Jitter","Jolly","Kindle","Leaper","Little","Lopper","Lucky","Mellow","Mistletoe","Mouse","Mugs","Mugsy","Nimble","Parade","Petal","Pitch","Plummet","Prancer","Pyro","Quickstep","Rags","Rebel","Red","Robin","Rose","Rouge","Ruby","Rusty","Scruffy","Shimmer","Shimmy","Sketch","Skip","Skipper","Skippy","Slick","Slim","Smiles","Smiley","Spark","Sparkle","Sparkles","Sparrow","Spike","Springstep","Stretch","Strutter","Thunder","Torch","Tricks","Tricky","Twinkle","Twinkles","Twitch","Waver","Wiggles","Wobble","Zero","Ziggy"];

var br = "";

function legacyBrowserNameGen(type){
	$('#placeholder').css('textTransform', 'capitalize');
	var tp = type;
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		if(tp === 2){
			nTp = Math.random() * 5 | 0;
			if(nTp === 0){
				rnd = Math.random() * nm18.length | 0;
				nMs = nm18[rnd];
			}else if(nTp < 3){
				rnd = Math.random() * nm14.length | 0;
				rnd2 = Math.random() * nm15.length | 0;
				while(nm14[rnd] === nm15[rnd2]){
					rnd2 = Math.random() * nm15.length | 0;
				}
				nMs = nm14[rnd] + nm15[rnd2];
			}else{
				rnd = Math.random() * nm16.length | 0;
				rnd2 = Math.random() * nm17.length | 0;
				while(nm16[rnd] === nm17[rnd2]){
					rnd2 = Math.random() * nm17.length | 0;
				}
				nMs = nm16[rnd] + nm17[rnd2];
			}
		}else if(tp === 1){
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
	nTp = Math.random() * 8 | 0;
	if(nTp === 0){
		rnd = Math.random() * 9 | 0;
		rnd2 = Math.random() * 3 | 0;
		nMs = nm8[rnd] + nm13[rnd2];
	}else{
		rnd = Math.random() * nm8.length | 0;
		rnd2 = Math.random() * nm9.length | 0;
		rnd3 = Math.random() * nm10.length | 0;
		rnd4 = Math.random() * nm13.length | 0;
		if(nTp < 3){
			while(nm8[rnd] === nm10[rnd3]){
				rnd3 = Math.random() * nm10.length | 0;
			}
			while(rnd2 < 3){
				rnd2 = Math.random() * nm9.length | 0;
			}
			nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm13[rnd4];
		}else{
			rnd5 = Math.random() * nm11.length | 0;
			rnd6 = Math.random() * nm12.length | 0;
			while(nm12[rnd6] === nm10[rnd3] && nm10[rnd3] === nm8[rnd]){
				rnd3 = Math.random() * nm10.length | 0;
			}
			while(rnd2 < 3 && rnd4 < 3){
				rnd2 = Math.random() * nm9.length | 0;
			}
			nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm11[rnd5] + nm12[rnd6] + nm13[rnd4];
		}
	}
	testSwear(nMs);
}

function nameMas(){
	nTp = Math.random() * 2 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd3 = Math.random() * nm3.length | 0;
	rnd4 = Math.random() * nm6.length | 0;
	rnd5 = Math.random() * nm7.length | 0;
	while(rnd2 === 0 && rnd4 === 0){
		rnd2 = Math.random() * nm2.length | 0;
	}
	if(nTp === 0){
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
		while(rnd6 === 0 && rnd4 === 0){
			rnd6 = Math.random() * nm4.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd6] + nm5[rnd7] + nm6[rnd4] + nm7[rnd5];
	}
	testSwear(nMs);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "satyrs";

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
