var nm1 = ["","","","","b","d","g","j","k","kr","l","n","pl","q","s","t","w","x","y"];
var nm2 = ["ue","uo","ua","ia","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u"];
var nm3 = ["b","d","k","l","lb","ld","lk","m","n","nn","nl","nq","nqw","qw","p","pp","r","rdl","rt","rtl","z","zl"];
var nm4 = ["y","a","e","i","o","u","a","e","i","o","u"];
var nm5 = ["","","","","","c","d","g","k","l","ll","m","n","r","t","tt"];

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
	rnd2 = Math.random() * nm2.length | 0;
	rnd3 = Math.random() * nm5.length | 0;
	if(nTp === 0){
		while(nm1[rnd] === "" && nm5[rnd3] === ""){
			rnd = Math.random() * nm1.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm5[rnd3];
	}else{
		rnd4 = Math.random() * nm4.length | 0;
		rnd5 = Math.random() * nm3.length | 0;
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd5] + nm4[rnd4] + nm5[rnd3];
	}
	testSwear(nMs);
}