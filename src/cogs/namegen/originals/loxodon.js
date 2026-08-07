var nm1 = ["","","","b","br","ch","d","dr","g","h","k","n","r","s","sv","t","thr","v","vr","z"];
var nm2 = ["oo","a","e","i","o","a","e","i","o","a","e","i","o"];
var nm3 = ["b","br","d","dj","dr","g","h","j","k","m","nd","ndr","nj","nr","nt","l","ld","ldr","lr","r","rd","s","t","y"];
var nm4 = ["oo","e","o","u","o","u","e","o","u","o","u"];
var nm5 = ["l","m","n","r"];
var nm6 = ["j","l","m","n","s","v","z","zh"];

var nm7 = ["","","","b","d","f","j","k","l","ly","m","r","s","sh","t","v","y","z"];
var nm8 = ["oo","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u"];
var nm9 = ["d","f","fy","j","l","ln","lr","lt","ly","n","nc","nt","ny","r","rj","s","sn","sm","sr","t","tr","v"];
var nm10 = ["oo","a","i","u","a","i","u","a","i","u","e","e"];
var nm11 = ["j","l","n","r","v","z"];
var nm12 = ["a","e","i","o","u"];
var nm13 = ["","","","","","j","l","m","n","r","s","y"];

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
	rnd5 = Math.random() * nm6.length | 0;
	if(nTp === 0){
		while(nm1[rnd] === ""){
			rnd = Math.random() * nm1.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm6[rnd5];
	}else{
		rnd3 = Math.random() * nm3.length | 0;
		rnd4 = Math.random() * nm4.length | 0;
		while(nm3[rnd3] === nm1[rnd] || nm3[rnd3] === nm6[rnd5]){
			rnd3 = Math.random() * nm3.length | 0;
		}
		if(rnd2 === 0){
			while(rnd4 === 0){
				rnd4 = Math.random() * nm4.length | 0;
			}
		}
		if(nTp < 4){
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd4] + nm6[rnd5];
		}else{
			rnd6 = Math.random() * nm5.length | 0;
			while(nm3[rnd3] === nm5[rnd6] || nm5[rnd6] === nm6[rnd5]){
				rnd6 = Math.random() * nm5.length | 0;
			}
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd4] + nm5[rnd6] + "o" + nm6[rnd5];
		}
	}
	testSwear(nMs);
}

function nameFem(){
	nTp = Math.random() * 3 | 0;
	rnd = Math.random() * nm7.length | 0;
	rnd2 = Math.random() * nm8.length | 0;
	rnd3 = Math.random() * nm9.length | 0;
	rnd4 = Math.random() * nm12.length | 0;
	rnd5 = Math.random() * nm13.length | 0;
	if(nTp < 2){
		while(nm7[rnd] === nm9[rnd3] || nm9[rnd3] === nm13[rnd5]){
			rnd3 = Math.random() * nm9.length | 0;
		}
		nMs = nm7[rnd] + nm8[rnd2] + nm9[rnd3] + nm12[rnd4] + nm13[rnd5];
	}else{
		rnd6 = Math.random() * nm10.length | 0;
		rnd7 = Math.random() * nm11.length | 0;
		while(nm11[rnd7] === nm9[rnd3] || nm11[rnd7] === nm13[rnd5]){
			rnd7 = Math.random() * nm11.length | 0;
		}
		nMs = nm7[rnd] + nm8[rnd2] + nm9[rnd3] + nm12[rnd4] + nm13[rnd5];
	}
	testSwear(nMs);
}