var nm1 = ["br","cr","d","dr","gr","h","j","k","kl","l","p","pr","r","s","sh","sl","st","str","t","v","w","wr"];
var nm2 = ["ee","ea","ae","oi","y","a","a","e","i","o","u"];
var nm3 = ["b","d","gl","hm","k","l","ll","ls","m","mv","n","nv","r","rk","rx","s","ss","th","v","vl","zn"];
var nm4 = ["y","a","e","i","a","e","i","a","e","i"];
var nm5 = ["c","g","k","l","n","r"];
var nm6 = ["ee","ii","a","i","o","u","a","i","o","u"];
var nm7 = ["","","","","","g","l","ld","lk","lm","ls","n","nn","q","r","rm","rt","sh","t"];

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
	nTp = Math.random() * 5 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	rnd5 = Math.random() * nm7.length | 0;
	if(nTp < 2){
		while(nm7[rnd5] === ""){
			rnd5 = Math.random() * nm7.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm7[rnd5];
	}else{
		if(nTp < 4){
			rnd3 = Math.random() * nm3.length | 0;
			rnd4 = Math.random() * nm4.length | 0;
			while(nm3[rnd3] === nm7[rnd5] || nm3[rnd3] === nm1[rnd]){
				rnd3 = Math.random() * nm3.length | 0;
			}
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd4] + nm7[rnd5];
		}else{
			rnd6 = Math.random() * nm6.length | 0;
			rnd7 = Math.random() * nm5.length | 0;
			while(nm3[rnd5] === nm5[rnd7] || nm5[rnd7] === nm7[rnd5]){
				rnd7 = Math.random() * nm5.length | 0;
			}
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd4] + nm5[rnd7] + nm6[rnd6] + nm7[rnd5];
		}
	}
	testSwear(nMs);
}