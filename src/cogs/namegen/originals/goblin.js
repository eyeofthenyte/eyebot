var nm1 = ["","","c","cr","d","g","h","j","kr","m","n","p","r","s","st","t","v","vr","z","zr"];
var nm2 = ["a","e","i","o","u","a","u"];
var nm3 = ["ch","dg","dr","g","gd","gl","gg","gr","j","ll","rr","rd"];
var nm4 = ["","b","g","gg","k","lk","rg","rk","s","t"];

var nm5 = ["","","b","d","g","j","m","n","p","q","r","v","z"];
var nm6 = ["a","i","u","a","i","u","o","e"];
var nm7 = ["b","br","d","dr","g","gn","gv","gr","lg","lgr","ld","ldr","lv","lz","ln","nd","nv","nr","rg","rz","rdr","rgr","rt"];
var nm8 = ["d","dd","g","l","ld","ll","n","nd","nn","y","v","z"];
var nm9 = ["","","k","l","n","r","s","t"];

var nm10 = ["Ant","Bait","Baitworm","Bearbelch","Bearbite","Beardung","Beetle","Belch","Bigchin","Birdbrain","Bitenose","Bitesize","Blockhead","Boarbait","Boardung","Bonehead","Bottomfeeder","Bottomfood","Brainmush","Breadstick","Bucket","Buffoon","Bugbite","Candlestick","Chickenbrain","Chowder","Clam","Coldnose","Crawly","Deviant","Dirtbrain","Dirtface","Donkey","Dungbreath","Fly","Frogface","Froghead","Frogwart","Gnat","Gnatface","Grubface","Grubgrub","Guano","Ingrate","Insect","Larva","Leech","Leechbrain","Leechhead","Leechnose","Louse","Lousehead","Maggot","Maggotbrain","Malformed","Mealworm","Mite","Mitemouth","Moldbrain","Moldnose","Mongrel","Mud","Mudface","Mudmouth","Mudmug","Mudnose","Mule","No-Ear","No-Ears","No-Eyes","No-Nose","No-Toes","One-Eye","Owlball","Peon","Pest","Pig","Pigface","Pighead","Pigmud","Pigmug","Pinkeye","Redeye","Sleaze","Slime","Slug","Slugmug","Snack","Snailbrain","Snailnose","Snot","Snotnose","Spiderbait","Toadbrain","Toadface","Toadwart","Toenail","Uglymug","Vermin","Wartface","Weasel","Weevil","Worm","Wormfood","Wormmouth","Wriggler"];
var nm11 = ["Wide","Ugly","Strange","Slime","Pale","Grime","Grease","Bone","Bent","Bitter","Broken","Dirt","Dull","Fat","Flat","Frail","Glob","Gout","Grim","Grub","Half","Ichor","Limp","Lump","Mad","Meek","Mold","Moss","Muck","Mud","Murk","Numb","Oaf","Shrill","Sick","Smug","Snail","Snot","Slug","Stink","Stub","Wart","Weak","Worm"];
var nm12 = ["arm","arms","ear","eye","eyes","bone","bones","brain","cheek","cheeks","chin","face","flab","flank","foot","feet","gob","gut","guts","head","knuckle","knuckles","leg","legs","maw","mug","nose","tooth","teeth","will"];

var br = "";

function nameGen(type){
	var tp = type;
	$('#placeholder').css('textTransform', 'capitalize');
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		if(i < 5){
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
		}else{
			nTp = Math.random() * 2 | 0;
			if(nTp === 0){
				rnd = Math.random() * nm10.length | 0;
				nMs = nm10[rnd];
			}else{
				rnd = Math.random() * nm11.length | 0;
				rnd2 = Math.random() * nm12.length | 0;
				if(nm11[rnd].charAt(nm11[rnd].length, -1) === "y" || nm11[rnd].charAt(nm11[rnd].length, -1) === "e"){
					while(nm12[rnd2].charAt(0) === "a" || nm12[rnd2].charAt(0) === "e"){
						rnd2 = Math.random() * nm12.length | 0;
					}
				}
				nMs = nm11[rnd] + nm12[rnd2];
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
	nTp = Math.random() * 3 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd5 = Math.random() * nm4.length | 0;
	if(nTp === 0){
		while(nm1[rnd] === ""){
			rnd = Math.random() * nm1.length | 0;
		}
		while(nm4[rnd5] === ""){
			rnd5 = Math.random() * nm4.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm4[rnd5];
	}else{
		rnd3 = Math.random() * nm3.length | 0;
		rnd4 = Math.random() * nm2.length | 0;
		while(nm3[rnd3] === nm1[rnd] || nm3[rnd3] === nm4[rnd5]){
			rnd3 = Math.random() * nm3.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm2[rnd4] + nm4[rnd5];
	}
	testSwear(nMs);
}

function nameFem(){
	nTp = Math.random() * 5 | 0;
	rnd = Math.random() * nm5.length | 0;
	rnd2 = Math.random() * nm6.length | 0;
	rnd5 = Math.random() * nm9.length | 0;
	if(nTp === 0){
		while(nm5[rnd] === ""){
			rnd = Math.random() * nm5.length | 0;
		}
		while(nm9[rnd5] === ""){
			rnd5 = Math.random() * nm9.length | 0;
		}
		nMs = nm5[rnd] + nm6[rnd2] + nm9[rnd5];
	}else{
		rnd3 = Math.random() * nm7.length | 0;
		rnd4 = Math.random() * nm6.length | 0;
		while(nm7[rnd3] === nm5[rnd] || nm7[rnd3] === nm9[rnd5]){
			rnd3 = Math.random() * nm7.length | 0;
		}
		if(nTp < 4){
			nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm6[rnd4] + nm9[rnd5];
		}else{			
			rnd6 = Math.random() * nm8.length | 0;
			rnd7 = Math.random() * nm6.length | 0;
			while(nm7[rnd3] === nm8[rnd6] || nm8[rnd6] === nm9[rnd5]){
				rnd6 = Math.random() * nm8.length | 0;
			}
			nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm6[rnd4] + nm8[rnd6] + nm6[rnd7] + nm9[rnd5];
		}
	}
	testSwear(nMs);
}