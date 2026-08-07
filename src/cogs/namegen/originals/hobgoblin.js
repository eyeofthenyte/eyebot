var nm1 = ["","","","","","d","dr","g","gl","gr","k","kh","kl","kr","l","m","n","r","rh","sh","v","vr","z","zr"];
var nm2 = ["a","o","a","o","e","u"];
var nm3 = ["d","dr","g","gr","gn","k","kk","kr","kn","kv","ldr","lv","lz","lvr","nd","ndr","nk","r","rb","rd","rk","v","vr","vl","z","zr"];
var nm4 = ["e","e","a","o","i","u","e","a","o"];
var nm5 = ["d","l","n","r","v","z"];
var nm6 = ["a","e","o","u"];
var nm7 = ["c","d","g","k","l","n","r","rg","rz"];
var nm8 = ["Bark","Bash","Bellow","Bleed","Blow","Bolster","Bolt","Brawl","Break","Bruise","Buckle","Bully","Burn","Burst","Butcher","Cackle","Carve","Chomp","Conquer","Crash","Crunch","Crush","Dash","Devour","Dodge","Duel","Edge","Etch","Feign","Flail","Flare","Forge","Froth","Fume","Glare","Gnash","Grimace","Grin","Growl","Hook","Impale","Jolt","Kill","Lash","Lurch","Mangle","Mark","Maul","Pierce","Prowl","Pummel","Quake","Rage","Rebuke","Reign","Rend","Repel","Retch","Revel","Roam","Ruin","Rush","Saw","Scorch","Scrub","Seethe","Sever","Shock","Shred","Slay","Smirk","Smush","Snarl","Squish","Stalk","Sting","Stomp","Strike","Stunt","Swipe","Thrash","Thunder","Trail","Trample","Twist","Twitch","Vex","Whack","the Beast","the Behemoth","the Blade","the Boar","the Bold","the Brute","the Bull","the Butcher","the Cold","the Corrupt","the Cruel","the Dagger","the Demon","the Edge","the Fury","the Giant","the Grand","the Grim","the Harsh","the Hollow","the Hook","the Hungry","the Hunter","the Insane","the Knife","the Loud","the Mad","the Maniac","the Manslayer","the Marked","the Mask","the Mighty","the Monster","the Oaf","the Ox","the Razor","the Reckless","the Red","the Rogue","the Rotten","the Sabre","the Serpent","the Shallow","the Shank","the Shield","the Shiv","the Skeleton","the Slayer","the Snake","the Strong","the Sword","the Thief","the Tyrant","the Vengeful","the Vicious","the Violent","the Vulture","the Warlord","the Warmonger","the Warrior","the Watcher","the Wrath","the Wretched"];

var br = "";

function nameGen(){
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