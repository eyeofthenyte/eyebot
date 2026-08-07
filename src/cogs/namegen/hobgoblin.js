var nm1 = ["","","","","","d","dr","g","gl","gr","k","kh","kl","kr","l","m","n","r","rh","sh","v","vr","z","zr"];
var nm2 = ["a","o","a","o","e","u"];
var nm3 = ["d","dr","g","gr","gn","k","kk","kr","kn","kv","ldr","lv","lz","lvr","nd","ndr","nk","r","rb","rd","rk","v","vr","vl","z","zr"];
var nm4 = ["e","e","a","o","i","u","e","a","o"];
var nm5 = ["d","l","n","r","v","z"];
var nm6 = ["a","e","o","u"];
var nm7 = ["c","d","g","k","l","n","r","rg","rz"];
var nm8 = ["Bark","Bash","Bellow","Bleed","Blow","Bolster","Bolt","Brawl","Break","Bruise","Buckle","Bully","Burn","Burst","Butcher","Cackle","Carve","Chomp","Conquer","Crash","Crunch","Crush","Dash","Devour","Dodge","Duel","Edge","Etch","Feign","Flail","Flare","Forge","Froth","Fume","Glare","Gnash","Grimace","Grin","Growl","Hook","Impale","Jolt","Kill","Lash","Lurch","Mangle","Mark","Maul","Pierce","Prowl","Pummel","Quake","Rage","Rebuke","Reign","Rend","Repel","Retch","Revel","Roam","Ruin","Rush","Saw","Scorch","Scrub","Seethe","Sever","Shock","Shred","Slay","Smirk","Smush","Snarl","Squish","Stalk","Sting","Stomp","Strike","Stunt","Swipe","Thrash","Thunder","Trail","Trample","Twist","Twitch","Vex","Whack","the Beast","the Behemoth","the Blade","the Boar","the Bold","the Brute","the Bull","the Butcher","the Cold","the Corrupt","the Cruel","the Dagger","the Demon","the Edge","the Fury","the Giant","the Grand","the Grim","the Harsh","the Hollow","the Hook","the Hungry","the Hunter","the Insane","the Knife","the Loud","the Mad","the Maniac","the Manslayer","the Marked","the Mask","the Mighty","the Monster","the Oaf","the Ox","the Razor","the Reckless","the Red","the Rogue","the Rotten","the Sabre","the Serpent","the Shallow","the Shank","the Shield","the Shiv","the Skeleton","the Slayer","the Snake","the Strong","the Sword","the Thief","the Tyrant","the Vengeful","the Vicious","the Violent","the Vulture","the Warlord","the Warmonger","the Warrior","the Watcher","the Wrath","the Wretched"];

var br = "";

function legacyBrowserNameGen(){
	$('#placeholder').css('textTransform', 'capitalize');
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		nameFem();
		while(nMs === ""){
			nameFem();
		}
		if(i > 4){
			rnd = Math.random() * nm8.length | 0;
			nMs = nMs + " " + nm8[rnd];
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
	nTp = Math.random() * 5 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd5 = Math.random() * nm7.length | 0;
	if(nTp === 0){
		while(nm1[rnd] === ""){
			rnd = Math.random() * nm1.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm7[rnd5];
	}else{
		rnd3 = Math.random() * nm3.length | 0;
		rnd4 = Math.random() * nm6.length | 0;
		while(nm3[rnd3] === nm1[rnd] || nm3[rnd3] === nm7[rnd5]){
			rnd3 = Math.random() * nm3.length | 0;
		}
		if(nTp < 4){
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm6[rnd4] + nm7[rnd5];
		}else{			
			rnd6 = Math.random() * nm5.length | 0;
			rnd7 = Math.random() * nm4.length | 0;
			while(nm3[rnd3] === nm5[rnd6] || nm5[rnd6] === nm7[rnd5]){
				rnd6 = Math.random() * nm5.length | 0;
			}
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd7] + nm5[rnd6] + nm6[rnd4] + nm7[rnd5];
		}
	}
	testSwear(nMs);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "hobgoblin";

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
