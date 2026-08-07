var nm1 = ["","","","","","h","m","n","s","sh","ss","ssh","sz","t","th","y","z","zh","zs"];
var nm2 = ["a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","oa","ui"];
var nm3 = ["h","hl","htl","hl","hs","hsh","k","kh","kl","ktl","ks","l","lk","ls","ltl","lts","lsh","m","n","s","sh","ss","st","stl","sz","sk","t","tl","ts","tsh","tsz","tz","tstl","zs","zh","zsh","zt","ztl"];
var nm4 = ["h","hs","hl","l","ll","s","sh","ss","shl","t","th","y","z","zh"];
var nm5 = ["a","i","u","a","i","u","a","i","u","a","i","u","a","i","u","a","i","u","ie","ia","ei","ee","iu","ui"];
var nm6 = ["","","","","","","","","h","h","l","ll","s","ss","sh"];

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
	rnd4 = Math.random() * nm5.length | 0;
	rnd5 = Math.random() * nm6.length | 0;
	if(i < 6){
		while(nm1[rnd] === nm3[rnd3] || nm3[rnd3] === nm6[rnd5]){
			rnd3 = Math.random() * nm3.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm5[rnd4] + nm6[rnd5];
	}else{
		rnd6 = Math.random() * nm4.length | 0;
		rnd7 = Math.random() * nm2.length | 0;
		while(nm3[rnd4] === nm4[rnd6] || nm4[rnd6] === nm6[rnd5]){
			rnd6 = Math.random() * nm4.length | 0;
		}
		nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm2[rnd7] + nm4[rnd6] + nm5[rnd4] + nm6[rnd5];
	}
	testSwear(nMs);
}