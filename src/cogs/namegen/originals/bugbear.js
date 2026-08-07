var nm1 = ["b","br","chr","d","g","gh","hr","kh","n","r","st","t","th","v","z","zh"];
var nm2 = ["a","e","i","o","u"];
var nm3 = ["d","dd","dr","g","gh","gg","gr","rr","rd","rg","rn","t","tt","tr","v","vr","z","zz"];
var nm4 = ["a","i","o","u"];
var nm5 = ["k","lk","mkk","n","nn","nk","r","rk","rr","th"];

var br = "";

function nameGen(){
	$('#placeholder').css('textTransform', 'capitalize');
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		nameMas();
		while(nMs === ""){
			nameMas();
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
	rnd2 = Math.random() * nm4.length | 0;
	rnd3 = Math.random() * nm5.length | 0;
	if(nTp === 0){
		nMs = nm1[rnd] + nm4[rnd2] + nm5[rnd3];
	}else{
		rnd4 = Math.random() * nm2.length | 0;
		rnd5 = Math.random() * nm3.length | 0;
		nMs = nm1[rnd] + nm2[rnd4] + nm3[rnd5] + nm4[rnd2] + nm5[rnd3];
	}
	testSwear(nMs);
}