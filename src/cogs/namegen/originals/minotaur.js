var nmFF = ["Aam","Ane","Are","Ase","Den","Duo","Duu","Em","Enti","Era","Este","Fas","Fen","Hene","Hes","Hila","Hine","Ias","Ire","Ki","Kia","Kuo","Laan","Line","Loo","Mira","Mou","Muu","Nan","Nea","Neo","Noo","Nuo","Oen","Oes","Raas","Ras","Reo","Rina","Sees","Seo","Sina","Tee","Tes","Tia","Tina","Uova","Veo","Vi","Via","Weo","Wina"];
var nmFL = ["dane","dera","din","dra","fa","fen","fin","kane","kea","ken","kia","la","las","len","lian","lin","lo","mas","me","mi","min","mira","na","nan","nas","nim","nore","nu","pe","pen","ra","ren","res","rin","ris","ru","sen","sia","ta","ter","tin","tra","tred","tri","trin","tris","ven","vena","vera","vin","za","zara","zin"];
var nmMF = ["Ar","Are","Aste","Bar","Bjor","Bran","Car","Cod","Da","Djar","Djun","Doen","Dor","Drin","Dur","Far","Foos","Gar","Goe","Gra","Gran","Gun","Har","Hir","Hun","Ja","Jar","Kar","Kin","Kir","Koo","Koor","Kran","Krum","Kur","Man","Min","Mir","Mun","Nar","Noe","Noo","Pod","Rak","Te","Tir","Toon","Trak","Tur","Zam","Zar","Zun"];
var nmML = ["ban","baran","bur","dak","daran","diar","dor","drin","fajar","faruk","fran","furan","gajan","garak","giran","gur","jar","kan","kar","karat","kun","kurat","kus","manuk","marin","maruk","narak","nark","narun","nir","nus","paran","piran","raduk","rak","rakar","ranak","rapak","ras","rat","rilak","rios","ron","rus","rut","tagar","taruk","tiran","toron","turok","tus","vrak"];
var nmSF = ["Agile","Bear","Bold","Boulder","Brave","Bright","Fearless","Fist","Glory","Goblin","Great","Heavy","Honor","Iron","Jagged","Keen","Nimble","Orc","Rock","Rugged","Sharp","Silent","Single","Steady","Steel","Stone","Storm","Stout","Strong","Swift","Thick","Thunder","Tough","Truth","Valiant","Vigil","Wolf"];
var nmSL = ["bane","body","eye","fighter","fist","fury","hand","heart","hide","hoof","horn","horns","hunter","leader","mind","pelt","roar","runner","skin","skull","slash","slayer","speaker","step","striker","vigor","walker","warrior"];

function nameGen(type){
	var tp = type;
	var br = "";
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		rnd = Math.floor(Math.random() * nmSF.length);
		rnd2 = Math.floor(Math.random() * nmSL.length);
		nSr = nmSF[rnd] + nmSL[rnd2];
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
	if(i < 5){
		rnd = Math.floor(Math.random() * nmFF.length);
		rnd2 = Math.floor(Math.random() * nmFL.length);
		nMs = nmFF[rnd] + nmFL[rnd2];
	}else{
		rnd = Math.floor(Math.random() * nmMF.length);
		rnd2 = Math.floor(Math.random() * nmML.length);
		nMs = nmMF[rnd] + nmML[rnd2];
	}
	testSwear(nMs);
}