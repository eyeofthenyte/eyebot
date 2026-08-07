var nm1 = ["","","","b","br","d","dr","g","gr","k","kr","p","pr","t","tr","x","z"];
var nm2 = ["y","a","e","i","o"];
var nm3 = ["g","g","gn","gt","kn","kr","kt","kn","m","mn","pt","r","r","r","rt","rth","th","th","x","x"];
var nm4 = ["a","a","e","e","i","o"];
var nm5 = ["g","k","m","n","r","th"];
var nm6 = ["io","eo","io","e","i","o","u","e","i","o","u","e","i","o","u","e","i","o","u"];
var nm7 = ["","","n","r","s","z","n","r","s","z","n","r","s","z"];

var nm8 = ["","","c","d","d","dr","g","g","gr","k","k","s","s","z","z"];
var nm9 = ["ia","oi","io","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o"];
var nm10 = ["c","g","l","m","n","nn","r","rr","t","x","z","dn","dm","gn","lm","ln","lr","mn","rm","rn","zr"];
var nm11 = ["a","e","o"];
var nm12 = ["g","l","m","mn","n","nd","r","t","th"];
var nm13 = ["ia","a","e","e","a","e","e","a","e","e","a","e","e","a","e","e"];
var nm14 = ["","","","","","","","","","","","z"];

var nm16 = ["amber","autumn","bold","bronze","dawn","ember","fierce","flint","free","full","gloom","glow","golden","grand","great","hazel","iron","keen","light","lone","long","lunar","moon","plain","prime","proud","quick","rough","shadow","silent","smooth","soft","solar","spirit","star","storm","strong","summer","sun","swift","thunder","wild","wind","wise"];
var nm17 = ["brace","breath","brow","caller","claw","dream","dreamer","drifter","eye","eyes","field","force","front","guide","guides","heart","hide","hold","kith","mane","mask","moon","pelt","pride","reach","rest","rider","roar","seeker","shadow","shield","song","stride","tail","tale","tooth","ward","watcher","weaver","whisper","wind"];

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
		rnd = Math.random() * nm16.length | 0;
		rnd2 = Math.random() * nm17.length | 0;
		while(nm16[rnd] === nm17[rnd2]){
			rnd2 = Math.random() * nm17.length | 0;
		}
		nMs += " " + nm16[rnd] + nm17[rnd2];
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
	nTp = Math.random() * 7 | 0;
	rnd = Math.random() * nm8.length | 0;
	rnd2 = Math.random() * nm9.length | 0;
	rnd3 = Math.random() * nm10.length | 0;
	rnd4 = Math.random() * nm13.length | 0;
	rnd5 = Math.random() * nm14.length | 0;
	if(nTp < 3){
		while(nm10[rnd3] === nm14[rnd5] || nm10[rnd3] === nm8[rnd]){
			rnd3 = Math.random() * nm10.length | 0;
		}
		nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm13[rnd4] + nm14[rnd5];
	}else{
		rnd6 = Math.random() * nm11.length | 0;
		rnd7 = Math.random() * nm12.length | 0;
		while(nm14[rnd5] === nm12[rnd7] || nm12[rnd7] === nm10[rnd3]){
			rnd7 = Math.random() * nm12.length | 0;
		}
		if(nTp < 6){
			nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm11[rnd6] + nm12[rnd7] + nm13[rnd4] + nm14[rnd5];
		}else{
			rnd8 = Math.random() * nm11.length | 0;
			rnd9 = Math.random() * nm12.length | 0;
			while(nm14[rnd5] === nm12[rnd9] || nm12[rnd9] === nm12[rnd7]){
				rnd9 = Math.random() * nm12.length | 0;
			}
			nMs = nm8[rnd] + nm9[rnd2] + nm10[rnd3] + nm11[rnd6] + nm12[rnd7] + nm11[rnd8] + nm12[rnd9] + nm13[rnd4] + nm14[rnd5];
		}
	}
	testSwear(nMs);
}

function nameMas(){
	nTp = Math.random() * 5 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * 3 | 0;
	rnd5 = Math.random() * nm7.length | 0;
	if(nTp === 0){
		while(nm1[rnd] === ""){
			rnd = Math.random() * nm1.length | 0;
		}
		while(nm7[rnd5] === ""){
			rnd5 = Math.random() * nm7.length | 0;
		}
		nMs = nm1[rnd] + nm6[rnd2] + nm7[rnd5];
	}else{
		if(nTp < 4){
			rnd2 = Math.random() * nm2.length | 0;
			rnd3 = Math.random() * nm3.length | 0;
			rnd4 = Math.random() * nm6.length | 0;
			while(nm3[rnd3] === nm7[rnd5] || nm3[rnd3] === nm1[rnd]){
				rnd3 = Math.random() * nm3.length | 0;
			}
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm6[rnd4] + nm7[rnd5];
		}else{
			rnd6 = Math.random() * nm4.length | 0;
			rnd7 = Math.random() * nm5.length | 0;
			while(nm3[rnd5] === nm5[rnd7] || nm5[rnd7] === nm7[rnd5]){
				rnd7 = Math.random() * nm5.length | 0;
			}
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd6] + nm5[rnd7] + nm6[rnd4] + nm7[rnd5];
		}
	}
	testSwear(nMs);
}