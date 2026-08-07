var nm1 = ["","","","b","d","dw","g","gh","gw","j","k","kh","m","n","rh","t","th","v","vr","z"];
var nm2 = ["ae","ai","a","e","i","o","a","e","o","a","e","i","o","a","e","o"];
var nm3 = ["f'r","l'n","l'd","m'v","m'z","n'z","n'v","n'r","sh'r","s'r","s'z","s'l","z'r","z'h","d","dr","g","gl","gr","k","kr","kl","l","ll","ld","ldr","ln","lr","lv","lz","lzr","m","mr","n","nn","nd","nv","r","rl","th","z","zl","zr"];
var nm4 = ["a","e","i","u","e","i","u"];
var nm5 = ["d","g","k","l","m","n","r","th","v"];
var nm6 = ["a","e","i","o"];
var nm7 = ["","","","d","g","h","l","ld","lk","n","nd","r","rd","s","t","th"];

var nm8 = ["b","d","f","h","l","m","n","ph","r","s","sh","v","z"];
var nm9 = ["a","e","i","a","e","i","o","y"];
var nm10 = ["d","dh","dr","fr","fl","fn","g","gl","gr","ld","ldr","lg","ln","lr","lth","lv","lz","n","nr","nv","r","rl","rn","rg","rs","rz","rsh","z","zh","zr","zl"];
var nm11 = ["a","e","i","i","o","y","y"];
var nm12 = ["l","n","r","v","z"];
var nm13 = ["ea","ia","ae","a","e","a","e","i","a","e","a","e","i","a","e","a","e","i","o","a","e","a","e","i","a","e","a","e","i","a","e","a","e","i","o"];
var nm14 = ["g","h","l","n","r","s","sh","t","th"];

var nm15 = ["Aspen","Autumn","Birch","Bloom","Boulder","Brook","Brown","Bright","Brush","Burrow","Cedar","Crater","Creek","Drift","Dust","Earthen","Elm","Fall","Flood","Fog","Forest","Grass","Green","Grove","Hail","Hazel","Hill","Hollow","Ice","Iron","Laurel","Maple","Moon","Moss","Mountain","Oaken","Peak","Pine","Plain","Rain","Ridge","River","Rock","Snow","Spring","Star","Stone","Storm","Summer","Sun","Thorn","Timber","Valley","Vine","Willow","Winter","Wood","Yew"];
var nm16 = ["bark","basker","bearer","binder","blade","blesser","blossom","blossoms","booster","borne","braid","braider","braids","breaker","bringer","bruiser","caller","carver","catcher","chanter","charger","chaser","cleanser","conqueror","crest","dancer","darter","defender","divider","dreamer","drinker","eyes","fader","fighter","force","forcer","former","gatherer","glow","groom","groomer","guard","heart","herald","hold","hoof","laugh","leaf","leaper","leaves","limp","love","mane","mangle","march","mask","mind","muse","pass","pelt","petals","prowl","prowler","push","reign","rest","reveler","ride","rise","roamer","roar","run","runner","rush","rusher","scorn","screamer","seeker","shadow","shield","shifter","shine","sign","sleep","slumber","smile","smirk","spark","spell","stare","strength","tail","temper","thread","trampler","tree","twister","voice","volley","wander","wanderer","watch","watcher","whisper","whisperer","wish"];

var br = "";

function nameGen(type){
	var tp = type;
	$('#placeholder').css('textTransform', 'capitalize');
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
		rnd = Math.random() * nm15.length | 0;
		rnd2 = Math.random() * nm16.length | 0;
		nMs = nMs + " " + nm15[rnd] + nm16[rnd2];
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
	nTp = Math.random() * 5 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd5 = Math.random() * nm7.length | 0;
	if(nTp === 0){
		while(nm1[rnd] === ""){
			rnd = Math.random() * nm1.length | 0;
		}
		while(nm7[rnd5] === ""){
			rnd5 = Math.random() * nm7.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm7[rnd5];
	}else{
		rnd3 = Math.random() * nm3.length | 0;
		rnd4 = Math.random() * nm4.length | 0;
		while(nm3[rnd3] === nm1[rnd] || nm3[rnd3] === nm7[rnd5]){
			rnd3 = Math.random() * nm3.length | 0;
		}
		if(rnd2 === 0){
			while(rnd4 === 0){
				rnd4 = Math.random() * nm4.length | 0;
			}
		}
		if(nTp < 4){
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd4] + nm7[rnd5];
		}else{
			rnd6 = Math.random() * nm5.length | 0;
			rnd7 = Math.random() * nm6.length | 0;
			while(nm3[rnd3] === nm5[rnd6] || nm5[rnd6] === nm7[rnd5]){
				rnd6 = Math.random() * nm5.length | 0;
			}
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd4] + nm5[rnd6] + nm6[rnd7] + nm7[rnd5];
		}
	}
	testSwear(nMs);
}

function nameFem(){
	nTp = Math.random() * 3 | 0;
	rnd = Math.random() * nm8.length | 0;
	rnd2 = Math.random() * nm9.length | 0;
	rnd3 = Math.random() * nm10.length | 0;
	rnd4 = Math.random() * nm13.length | 0;
	rnd5 = Math.random() * nm14.length | 0;
	if(nTp < 2){
		while(nm8[rnd] === nm10[rnd3] || nm10[rnd3] === nm14[rnd5]){
			rnd3 = Math.random() * nm10.length | 0;
		}
		nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm13[rnd4] + nm14[rnd5];
	}else{
		rnd6 = Math.random() * nm11.length | 0;
		rnd7 = Math.random() * nm12.length | 0;
		while(nm12[rnd7] === nm10[rnd3] || nm12[rnd7] === nm14[rnd5]){
			rnd7 = Math.random() * nm12.length | 0;
		}
		nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm11[rnd6] + nm12[rnd7] + nm13[rnd4] + nm14[rnd5];
	}
	testSwear(nMs);
}