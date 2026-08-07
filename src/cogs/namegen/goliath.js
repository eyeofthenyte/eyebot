var nmFF = ["Age","Ane","Are","Daa","Dau","Di","Ga","Gal","Gau","Ge","Gel","Ila","Ina","Ka","Kau","Ke","Ki","Kuo","La","Lau","Le","Lo","Maa","Man","Mau","Me","Na","Nal","Nau","Ni","No","Ola","One","Ore","Ori","Pa","Paa","Pau","Pe","Tha","Thau","The","Thu","Vaa","Vau","Ve","Vo","Vu","Za","Zaa","Zau","Zo"];
var nmFL = ["gea","geo","ggeo","ghu","gia","gu","kea","keo","kha","ki","kia","kio","kko","la","lai","lane","lea","leo","lo","lu","ma","meo","mi","mia","ne","nea","neo","ni","nia","nna","nnio","nu","peo","peu","pu","rea","rheo","ri","ria","rra","rrea","the","thea","thi","thia","thio","thu","vea","vi","via","vu"];
var nmMF = ["Ag","Apa","Ar","Au","Aug","Aur","Eag","Eg","Erg","Ga","Gau","Gea","Gha","Gra","Ila","Ili","Ira","Kana","Kava","Kaza","Keo","Khu","Kora","Kra","La","Lau","Laza","Loro","Ma","Mara","Mau","Mea","Mo","Na","Nara","Nau","Neo","Pa","Pu","Tara","Tau","Tha","Thava","Tho","Va","Vara","Vau","Vaura","Vega","Vi","Vo","Za","Zau"];
var nmML = ["dak","dath","dhan","gak","gal","gan","gath","ghan","gith","glath","gun","kan","kein","khal","kin","kon","lath","lig","lok","mahg","mahk","mahl","mak","man","mith","mul","nak","nath","nihl","noth","path","phak","rad","rath","rein","rhak","rhan","riak","rian","rin","rok","roth","thag","thak","tham","thi","thok","veith","vek","vhal","vhik","vith","voi","zak","ziath"];
var nmMdF = ["Adept","Bear","Brave","Bright","Dawn","Day","Deer","Dream","Flint","Fearless","Flower","Food","Fright","Goat","Hard","Hide","High","Honest","Horn","Keen","Lone","Long","Low","Lumber","Master","Mind","Mountain","Night","Rain","River","Rock","Root","Silent","Sky","Sly","Smart","Steady","Stone","Storm","Strong","Swift","Thread","Thunder","Tree","Tribe","True","Truth","Wander","Wild","Wise","Wound"];
var nmMdL = ["aid","bearer","breaker","caller","carver","chaser","climber","cook","dream","drifter","eye","finder","fist","friend","frightener","guard","hand","hauler","heart","herder","hunter","jumper","killer","lander","leader","leaper","logger","maker","mender","picker","runner","shot","smasher","speaker","stalker","striker","tanner","twister","vigor","walker","wanderer","warrior","watcher","weaver","worker"];
var nmSF= ["Agu-Ul","Agu-V","Anakal","Apuna-M","Athun","Egena-V","Egum","Elan","Ganu-M","Gathak","Gean","Inul","Kalag","Kaluk","Katho-Ol","Kolae-G","Kolak","Kulan","Kulum","Lakum","Maluk","Munak","Muthal","Nalak","Nola-K","Nugal","Nulak","Ogol","Oveth","Thenal","Thul","Thunuk","Ugun","Uthenu-K","Vaimei-L","Valu-N","Vathun","Veom","Vuma-Th","Vunak"];
var nmSL = ["aga","ageane","akane","akanu","akume","alathi","amino","amune","anathi","atake","athai","athala","atho","avea","avi","avone","eaku","ekali","elo","iaga","iago","iala","iano","igala","igane","igano","igo","igone","ileana","ithino","olake","ugate","ugoni","ukane","ukate","ukena","ulane","upine","utha","uthea"];

function legacyBrowserNameGen(type){
	var tp = type;
	var br = "";
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		rnd = Math.floor(Math.random() * nmMdF.length);
		rnd2 = Math.floor(Math.random() * nmMdL.length);
		rnd3 = Math.floor(Math.random() * nmSF.length);
		rnd4 = Math.floor(Math.random() * nmSL.length);
		nSr = nmMdF[rnd] + nmMdL[rnd2] + " " + nmSF[rnd3] + nmSL[rnd4];
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
	rnd = Math.floor(Math.random() * nmMF.length);
	rnd2 = Math.floor(Math.random() * nmML.length);
	nMs = nmMF[rnd] + nmML[rnd2];
	testSwear(nMs);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "goliath";

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
