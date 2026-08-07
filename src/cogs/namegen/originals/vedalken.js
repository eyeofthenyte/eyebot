var nm1 = ["","","","","","","b","bh","d","dh","dr","f","k","kh","l","m","n","nh","p","r","tr","y","z"];
var nm2 = ["a","e","i","o","u"];
var nm3 = ["b","bl","d","dr","dv","g","gg","gl","l","ld","ll","lv","m","n","pl","r","rd","rv","t","th","tl","thv","tr","v","vl","vr"];
var nm4 = ["l","ll","n","r","v","z"];
var nm5 = ["c","d","l","ll","n","r","sh","t","tt","v","z"];

var nm6 = ["","","","","","b","bl","br","d","dr","f","gr","h","k","kl","l","m","n","p","r","s","sl","tr","y","z","zl"];
var nm7 = ["ai","ie","ia","ei","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o"];
var nm8 = ["d","dd","dr","dv","g","gr","gg","l","ld","lg","ll","ln","lv","r","rr","rv","s","ss","str","tr","v","y","z"];
var nm9 = ["a","e","i","a","e","i","o"];
var nm10 = ["l","ll","n","nn","s","v","y","z"];
var nm11 = ["ia","ai","aa","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o"];
var nm12 = ["","","","","","","h","l","ll","n","nn","s","sh","ss"];

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
	nTp = Math.random() * 3 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd3 = Math.random() * nm3.length | 0;
	rnd4 = Math.random() * nm2.length | 0;
	rnd5 = Math.random() * nm5.length | 0;
	if(nTp < 2){
		while(nm1[rnd] === nm3[rnd3] || nm3[rnd3] === nm5[rnd5]){
			rnd3 = Math.random() * nm3.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm2[rnd4] + nm5[rnd5];
	}else{
		rnd6 = Math.random() * nm2.length | 0;
		rnd7 = Math.random() * nm4.length | 0;
		while(nm4[rnd7] === nm3[rnd3] || nm4[rnd7] === nm5[rnd5]){
			rnd7 = Math.random() * nm4.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm2[rnd4] + nm4[rnd7] + nm2[rnd6] + nm5[rnd5];
	}
	testSwear(nMs);
}

function nameFem(){
	nTp = Math.random() * 3 | 0;
	rnd = Math.random() * nm6.length | 0;
	rnd2 = Math.random() * nm7.length | 0;
	rnd3 = Math.random() * nm8.length | 0;
	rnd4 = Math.random() * nm11.length | 0;
	rnd5 = Math.random() * nm12.length | 0;
	if(rnd2 < 4){
		while(rnd4 < 3){
			rnd4 = Math.random() * nm11.length | 0;
		}
	}
	if(nTp < 2){
		while(nm6[rnd] === nm8[rnd3] || nm8[rnd3] === nm12[rnd5]){
			rnd3 = Math.random() * nm8.length | 0;
		}
		nMs = nm6[rnd] + nm7[rnd2] + nm8[rnd3] + nm11[rnd4] + nm12[rnd5];
	}else{
		rnd6 = Math.random() * nm9.length | 0;
		rnd7 = Math.random() * nm10.length | 0;
		while(nm10[rnd7] === nm8[rnd3] || nm10[rnd7] === nm12[rnd5]){
			rnd7 = Math.random() * nm10.length | 0;
		}
		nMs = nm6[rnd] + nm7[rnd2] + nm8[rnd3] + nm9[rnd6] + nm10[rnd7] + nm11[rnd4] + nm12[rnd5];
	}
	testSwear(nMs);
}