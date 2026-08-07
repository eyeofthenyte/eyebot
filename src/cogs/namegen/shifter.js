var names1 = ["Acor","Almond","Ash","Astro","Badger","Barb","Basalt","Basil","Beast","Birch","Blast","Blaze","Bluff","Bog","Boulder","Bramble","Breach","Briar","Brock","Brook","Burst","Canyon","Char","Chasm","Cinder","Claw","Cliff","Cloud","Coal","Cobalt","Cobble","Comet","Cosmo","Crag","Crater","Dash","Drake","Drift","Dune","Dusk","Dust","Echo","Fang","Flame","Flare","Flax","Flint","Flood","Foam","Fog","Forest","Fox","Frost","Frostbite","Fume","Fury","Gale","Glare","Gorge","Grime","Grit","Grove","Gulch","Gust","Kindle","Light","Lumber","Magma","Mahogany","Marsh","Mercury","Midnight","Mire","Moss","Mountain","Nebula","Newt","Nightfall","Nightshade","Nimbus","North","Nova","Nyx","Oak","Ocean","Onyx","Pitch","Pyre","Pyro","Quicksilver","Ravine","Ridge","Rift","River","Rock","Rubble","Scar","Shrub","Silver","Smoke","Soot","Spark","Spike","Spine","Steam","Steel","Stone","Storm","Surge","Talon","Thicket","Thistle","Thorn","Thunder","Tide","Tiger","Timber","Tinder","Tor","Torrent","Vapor","Vermin","Vine","Void","Wave","Willow","Wolf","Woods"];
var names2 = ["Abyss","Almond","Amber","Amethyst","Anemone","Aqua","Aurora","Autumn","Birch","Bloom","Blossom","Breeze","Briar","Brook","Canyon","Chestnut","Cloud","Coral","Coyote","Crest","Cricket","Crystal","Dawn","Dew","Dewdrop","Diamond","Elm","Ember","Emerald","Evening","Feather","Fern","Flare","Floe","Flora","Floret","Flow","Fluff","Galaxy","Gem","Hail","Harley","Haze","Hazel","Horizon","Ice","Indigo","Iris","Isle","Ivy","Jade","Jasmine","Juniper","Karma","Lake","Lavender","Leaf","Lily","Luna","Magenta","Maple","Marigold","Meadow","Midnight","Mist","Moon","Moss","Nebula","Nutmeg","Ocean","Olive","Opal","Orchid","Pearl","Petal","Pine","Pinecone","Plume","Poison","Pyro","Quill","Rain","Raven","Rill","River","Robin","Rose","Rosemary","Ruby","Saffron","Sage","Sapphire","Scarlet","Shade","Silver","Sky","Snow","Snowflake","Spring","Star","Stardust","Sugar","Summer","Sun","Sunrise","Sunset","Sunshine","Swill","Thistle","Tidal","Tiger","Tinder","Topaz","Twig","Twilight","Urchin","Vapor","Violet","Whirl","Willow","Wind","Wing","Winter"];

function legacyBrowserNameGen(type){
	var tp = type;
	var br = "";
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		if(tp === 1){
			rnd2 = Math.floor(Math.random() * names2.length);
			names = names2[rnd2];
		}else{
			rnd = Math.floor(Math.random() * names1.length);
			names = names1[rnd];
		}
		br = document.createElement('br');	
		element.appendChild(document.createTextNode(names));
		element.appendChild(br);
	}
	if(document.getElementById("result")){
		document.getElementById("placeholder").removeChild(document.getElementById("result"));
	}		
	document.getElementById("placeholder").appendChild(element);
}

// ---------------------------------------------------------------------------
// Node.js compatibility layer
// ---------------------------------------------------------------------------
const __legacyRace = "shifter";

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
