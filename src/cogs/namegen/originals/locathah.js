var nm1 = ["d","dh","g","gh","h","k","kh","l","m","n","r","th","v","z"];
var nm2 = ["a","e","i","o","u"];
var nm3 = ["ao","au","ou","oa","d","l","ll","m","n","nn","r","rr","v","z","d","l","ll","m","n","nn","r","rr","v","z"];
var nm4 = ["a","i","u"];
var nm5 = ["l","m","n","s","t","th"];

var br = "";

function nameGen(type){
	$('#placeholder').css('textTransform', 'capitalize');
	var tp = type;
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
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd3 = Math.random() * nm3.length | 0;
	rnd4 = Math.random() * nm4.length | 0;
	rnd5 = Math.random() * nm5.length | 0;
	while(nm3[rnd3] === nm5[rnd5] || nm3[rnd3] === nm1[rnd]){
		rnd3 = Math.random() * nm3.length | 0;
	}
	nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd4] + nm5[rnd5];
	testSwear(nMs);
}