var nm1 = ["b","c","d","g","n","p","r"];
var nm2 = ["","d","l","n","r"];
var nm3 = ["ee","oo","ie","ou","a","e","i","o","u"];
var nm4 = ["hb","hp","hn","b","h","n","ng","p","ph","s","sh"];
var nm5 = ["bh","kh","rh","b","br","k","r"];
var nm6 = ["Ã«","Ã¼","Ã¶","a","a","e","e","i","o","a","a","e","e","i","o"];
var nm7 = ["ht","hr","hk","b","d","k","kh","l","n","r","t"];
var nm8 = ["a","a","e","e","i","o"];

function nameGen(type){
	var tp = type;
	var br = "";
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
	nTp = Math.random() * 8 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd3 = Math.random() * nm3.length | 0;
	rnd4 = Math.random() * nm4.length | 0;
	if(nTp < 4){
		rnd2 = Math.random() * nm2.length | 0;
		while(nm1[rnd] === nm2[rnd2]){
			rnd2 = Math.random() * nm2.length | 0;
		}
		nTmp = nm2[rnd2] + nm3[rnd3] + nm4[rnd4];
		nTmp = nTmp.charAt(0).toUpperCase() + nTmp.slice(1);
		nMs = nm1[rnd] + "'" + nTmp;
	}else if(nTp < 6){
		rnd2 = Math.random() * nm1.length | 0;
		nTmp = nm3[rnd3];
		nTmp = nTmp.charAt(0).toUpperCase() + nTmp.slice(1);
		nMs = nm1[rnd] + "'" + nTmp + nm4[rnd4] + "'" + nm1[rnd2] + "'" + nTmp + nm4[rnd4];
	}else{
		rnd2 = Math.random() * nm2.length | 0;
		rnd5 = Math.random() * nm5.length | 0;
		rnd6 = Math.random() * nm6.length | 0;
		rnd7 = Math.random() * nm7.length | 0;
		rnd8 = Math.random() * nm8.length | 0;
		rnd9 = Math.random() * nm4.length | 0;
		if(nTp === 6){
			while(rnd7 < 3 && rnd9 < 3){
				rnd9 = Math.random() * nm4.length | 0;
			}
			nTmp = nm2[rnd2] + nm3[rnd3] + nm4[rnd4] + "-" + nm5[rnd5] + nm6[rnd6] + nm7[rnd7] + nm8[rnd8] + nm4[rnd9];
			nTmp = nTmp.charAt(0).toUpperCase() + nTmp.slice(1);
			nMs = nm1[rnd] + "'" + nTmp;
		}else{
			while(rnd5 < 3 && rnd9 < 3){
				rnd9 = Math.random() * nm4.length | 0;
			}
			while(rnd5 < 3 && rnd4 < 3){
				rnd4 = Math.random() * nm4.length | 0;
			}
			nTmp = nm2[rnd2] + nm3[rnd3] + nm7[rnd7] + nm8[rnd8] + nm4[rnd9] + "'" + nm5[rnd5] + nm6[rnd6] + nm4[rnd4];
			nTmp = nTmp.charAt(0).toUpperCase() + nTmp.slice(1);
			nMs = nm1[rnd] + "'" + nTmp;
		}
	}
	testSwear(nMs);
}