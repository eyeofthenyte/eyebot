var nm1 = ["","","","b","bh","br","d","dh","dr","g","gh","gr","j","l","m","n","r","rh","sh","z","zh"];
var nm2 = ["a","o","u"];
var nm3 = ["b","br","bz","d","dd","dz","dg","dr","g","gg","gr","gz","gv","hr","hz","j","kr","kz","m","mz","mv","n","ng","nd","nz","r","rt","rz","rd","rl","rz","t","tr","v","vr","z","zz"];
var nm4 = ["b","d","g","g","k","k","kk","kk","l","ll","n","r"];

var nm5 = ["","","","","b","bh","d","dh","g","gh","h","k","m","n","r","rh","s","sh","v","z"];
var nm6 = ["a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","ee","au","ye","ie","aa","ou","ua","ao"];
var nm7 = ["d","dd","dk","dg","dv","g","gg","gn","gv","gz","l","ll","lv","lz","m","md","mz","mv","ng","nk","ns","nz","t","thr","th","v","vn","vr","vg","vd","wnk","wg","wn"];
var nm8 = ["","","","","","f","h","k","l","m","n","ng","v","z"];

var nm9 = ["Aberrant","Ancient","Angry","Anguished","Arrogant","Barbarian","Barbaric","Barren","Berserk","Bitter","Bloody","Broad","Broken","Brutal","Brute","Butcher","Coarse","Cold","Colossal","Crazy","Crooked","Cruel","Dark","Defiant","Delirious","Deranged","Disfigured","Enormous","Enraged","Fearless","Feisty","Fierce","Filthy","Forsaken","Frantic","Gargantuan","Giant","Glorious","Grand","Grave","Grim","Gross","Gruesome","Hollow","Infernal","Lethal","Lost","Loyal","Macabre","Mad","Maniac","Merciless","Mighty","Miscreant","Noxious","Outlandish","Powerful","Prime","Proud","Putrid","Radical","Reckless","Repulsive","Rotten","Ruthless","Shady","Sick","Silent","Simple","Smug","Spiteful","Swift","Turbulent","Ugly","Unsightly","Vengeful","Venomous","Vicious","Violent","Vivid","Volatile","Vulgar","Warped","Wicked","Wild","Worthless","Wrathful","Wretched"];
var nm10 = ["Anger","Ankle","Ash","Battle","Beast","Bitter","Black","Blood","Bone","Brain","Brass","Breath","Chaos","Chest","Chin","Cold","Dark","Death","Dirt","Doom","Dream","Elf","Eye","Fang","Feet","Fiend","Finger","Flame","Flesh","Foot","Ghost","Giant","Gnoll","Gnome","Gore","Hand","Hate","Head","Heart","Heel","Hell","Horror","Iron","Joint","Kidney","Kill","Knee","Muscle","Nose","Pest","Poison","Power","Pride","Rib","Scale","Skin","Skull","Slave","Smoke","Sorrow","Spine","Spite","Steel","Storm","Talon","Teeth","Throat","Thunder","Toe","Tooth","Vein","Venom","Vermin","War"];
var nm11 = ["Axe","Blade","Brand","Breaker","Bruiser","Burster","Butcher","Carver","Chopper","Cleaver","Clobberer","Conquerer","Cracker","Cruncher","Crusher","Cutter","Dagger","Defacer","Despoiler","Destroyer","Dissector","Ender","Flayer","Gasher","Glaive","Gouger","Hacker","Hammer","Killer","Lance","Marauder","Masher","Mutilator","Piercer","Pummel","Quasher","Quelcher","Queller","Razer","Render","Ripper","Saber","Sabre","Scalper","Shatterer","Skinner","Slayer","Slicer","Smasher","Snapper","Spear","Splitter","Squasher","Squelcher","Squisher","Strangler","Sunderer","Sword","Trampler","Trasher","Vanquisher","Wrecker"];

var br = "";

function nameGen(type){
	$('#placeholder').css('textTransform', 'capitalize');
	var tp = type;
	var element = document.createElement("div");
	element.setAttribute("id", "result");

	for(i = 0; i < 10; i++){
		rSr = Math.random() * 2 | 0;
		if(rSr === 0){
			nSr = "The " + nm9[Math.random() * nm9.length | 0];
		}else{
			nSr = nm10[Math.random() * nm10.length | 0] + " " + nm11[Math.random() * nm11.length | 0];
		}
		if(tp === 1){
			nameFem();
			while(nFm === ""){
				nameFem();
			}
			names = nFm + " " + nSr;
		}else{
			nameMas();
			while(nMs === ""){
				nameMas();
			}
			names = nMs + " " + nSr;
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

function nameFem(){
	rnd = Math.random() * nm5.length | 0;
	rnd2 = Math.random() * nm6.length | 0;
	rnd3 = Math.random() * nm8.length | 0;
	if(i < 4){
		while(rnd < 4){
			rnd = Math.random() * nm5.length | 0;
		}
		while(rnd3 < 5 || nm8[rnd3] === nm5[rnd]){
			rnd3 = Math.random() * nm8.length | 0;
		}
		nFm = nm5[rnd] + nm6[rnd2] + nm8[rnd3];
	}else{
		rnd4 = Math.random() * nm7.length | 0;
		rnd5 = Math.random() * nm6.length | 0;
		while(nm7[rnd4] === nm8[rnd3]){
			rnd4 = Math.random() * nm7.length | 0;
		}
		nFm = nm5[rnd] + nm6[rnd2] + nm7[rnd4] + nm6[rnd5] + nm8[rnd3];
	}
	testSwear(nFm);
}

function nameMas(){
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd3 = Math.random() * nm4.length | 0;
	if(i < 4){
		while(rnd < 3 || nm1[rnd] === nm4[rnd3]){
			rnd = Math.random() * nm1.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm4[rnd3];
	}else{
		rnd4 = Math.random() * nm3.length | 0;
		rnd5 = Math.random() * nm2.length | 0;
		while(nm3[rnd4] === nm1[rnd] || nm3[rnd4] === nm4[rnd3]){
			rnd4 = Math.random() * nm3.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd4] + nm2[rnd5] + nm4[rnd3];
	}
	testSwear(nMs);
}