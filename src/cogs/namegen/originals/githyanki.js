var nm1 = ["","","d","g","j","k","l","q","r","tr","v","vr","x"];
var nm2 = ["a'a","'a'","'a'a","y","a","e","i","o","y","a","e","i","o","y","a","e","i","o"];
var nm3 = ["d","k","l","m","n","p","r","s"];
var nm4 = ["'i'","'a'","'a'a","a","i","o","a","i","o","a","i","o"];
var nm5 = ["d","l","ld","lr","m","n","nd","r","rd"];
var nm6 = ["aa","ai","a","a","o","u","a","a","o","u","a","a","o","u","a","a","o","u"];
var nm7 = ["c","n","s","th","n","s","th"];

var nm8 = ["b'l","b'n","s'r","v'n","","","","f","j","p","q","s","v","y","z","f","j","p","q","s","v","y","z","f","j","p","q","s","v","y","z"];
var nm9 = ["aa","ai","a","e","i","a","e","i","a","e","i","a","e","i"];
var nm10 = ["h'z","n'l","r'r","dr","gr","l","ll","lr","mr","n","nd","r","rr","rst","ss","str","tr"];
var nm11 = ["a","e","u"];
var nm12 = ["d","dr","l","lz","n","s","sr","r","rl","rz","z"];
var nm13 = ["i'i","'i'","oo","y","a","e","i","y","a","e","i","y","a","e","i","y","a","e","i","y","a","e","i","u","u","u"];
var nm14 = ["","","g","l","r","th"];

var br = "";

function nameGen(type){
	$('#placeholder').css('textTransform', 'capitalize');
	var tp = type;
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

function nameFem(){
	nTp = Math.random() * 5 | 0;
	rnd = Math.random() * nm8.length | 0;
	rnd2 = Math.random() * nm9.length | 0;
	rnd3 = Math.random() * nm14.length | 0;
	rnd4 = Math.random() * nm10.length | 0;
	rnd5 = Math.random() * nm11.length | 0;
	while(rnd < 4 && rnd4 < 3){
		rnd4 = Math.random() * nm10.length | 0;
	}
	if(nTp < 4){
		while(nm10[rnd4] === nm8[rnd] || nm10[rnd4] === nm14[rnd3]){
			rnd4 = Math.random() * nm10.length | 0;
		}
		nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd4] + nm11[rnd5] + nm14[rnd3];
	}else{
		rnd6 = Math.random() * nm12.length | 0;
		rnd7 = Math.random() * nm13.length | 0;
		while(rnd7 < 4 && rnd4 < 3){
			rnd7 = Math.random() * nm13.length | 0;
		}
		while(rnd7 < 4 && rnd < 3){
			rnd7 = Math.random() * nm13.length | 0;
		}
		while(nm10[rnd4] === nm12[rnd6] || nm12[rnd6] === nm14[rnd3]){
			rnd6 = Math.random() * nm12.length | 0;
		}
		nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd4] + nm11[rnd5] + nm12[rnd6] + nm13[rnd7] + nm14[rnd3];
	}
	testSwear(nMs);
}

function nameMas(){
	nTp = Math.random() * 5 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd3 = Math.random() * nm7.length | 0;
	if(nTp === 0){
		while(nm1[rnd] === ""){
			rnd = Math.random() * nm1.length | 0;
		}
		while(nm1[rnd] === nm7[rnd3] || nm7[rnd3] === ""){
			rnd3 = Math.random() * nm7.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm7[rnd3];
	}else{
		rnd4 = Math.random() * nm3.length | 0;
		rnd5 = Math.random() * nm4.length | 0;
		while(rnd2 < 3 && rnd5 < 3){
			rnd2 = Math.random() * nm2.length | 0;
		}
		if(nTp < 4){
			while(nm3[rnd4] === nm1[rnd] || nm3[rnd4] === nm7[rnd3]){
				rnd4 = Math.random() * nm3.length | 0;
			}
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd4] + nm4[rnd5] + nm7[rnd3];
		}else{
			rnd6 = Math.random() * nm5.length | 0;
			rnd7 = Math.random() * nm6.length | 0;
			while(nm3[rnd4] === nm5[rnd6] || nm5[rnd6] === nm7[rnd3]){
				rnd6 = Math.random() * nm5.length | 0;
			}
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd4] + nm4[rnd5] + nm5[rnd6] + nm6[rnd7] + nm7[rnd3];
		}
	}
	testSwear(nMs);
}