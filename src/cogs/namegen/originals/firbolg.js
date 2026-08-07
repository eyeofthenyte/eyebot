var nm1 = ["Ad","Ae","Bal","Bei","Car","Cra","Dae","Dor","El","Ela","Er","Far","Fen","Gen","Glyn","Hei","Her","Ian","Ili","Kea","Kel","Leo","Lu","Mira","Mor","Nae","Nor","Olo","Oma","Pa","Per","Pet","Qi","Qin","Ralo","Ro","Sar","Syl","The","Tra","Ume","Uri","Va","Vir","Waes","Wran","Yel","Yin","Zin","Zum"];
var nm2 = ["balar","beros","can","ceran","dan","dithas","faren","fir","geiros","golor","hice","horn","jeon","jor","kas","kian","lamin","lar","len","maer","maris","menor","myar","nan","neiros","nelis","norin","peiros","petor","qen","quinal","ran","ren","ric","ris","ro","salor","sandoral","toris","tumal","valur","ven","warin","wraek","xalim","xidor","yarus","ydark","zeiros","zumin"];
var nm3 = ["Ad","Ara","Bi","Bry","Cai","Chae","Da","Dae","Eil","En","Fa","Fae","Gil","Gre","Hele","Hola","Iar","Ina","Jo","Key","Kris","Lia","Lora","Mag","Mia","Neri","Ola","Ori","Phi","Pres","Qi","Qui","Rava","Rey","Sha","Syl","Tor","Tris","Ula","Uri","Val","Ven","Wyn","Wysa","Xil","Xyr","Yes","Ylla","Zin","Zyl"];
var nm4 = ["banise","bella","caryn","cyne","di","dove","fiel","fina","gella","gwyn","hana","harice","jyre","kalyn","krana","lana","lee","leth","lynn","moira","mys","na","nala","phine","phyra","qirelle","ra","ralei","rel","rie","rieth","rona","rora","roris","satra","stina","sys","thana","thyra","tris","varis","vyre","wenys","wynn","xina","xisys","ynore","yra","zana","zorwyn"];

var nm5 = ["","","","b","c","d","dr","f","fl","g","h","k","l","m","n","r","qu","s","sh","t","th","v","w","x","y"];
var nm6 = ["ae","ie","ia","ei","ey","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u"];
var nm7 = ["dr","l","l","ld","ldr","ll","lph","lt","lth","m","n","ndr","nn","nt","ph","r","r","rd","rn","s","sh","st","str","th","thr","v"];
var nm8 = ["a","e","i","o"];
var nm9 = ["dr","lk","ndr","nthr","sc","st","str","thr","c","h","l","m","n","nn","ph","r","rr","s","ss","v","x"];
var nm10 = ["ii","ie","aea","ia","ua","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o","a","e","i","o"];
var nm11 = ["","","","","","l","n","nn","nt","r","s","sh","th"];

var nm12 = ["alder","amber","ash","aspen","autumn","azure","beech","birch","blue","bold","bronze","cedar","crimson","dawn","dew","diamond","dusk","eager","elder","elm","ember","even","fall","far","feather","fir","flower","fog","forest","gem","gold","green","hazel","light","lunar","mist","moon","moss","night","oak","oaken","ocean","poplar","rain","rapid","raven","sage","shadow","silent","silver","spark","spirit","spring","star","still","stone","summer","sun","swift","wild","willow","wind","winter","wood"];
var nm13 = ["beam","bell","birth","blossom","breath","breeze","brook","cloud","crown","dew","dream","dreamer","fall","fate","flight","flow","flower","fond","gaze","gazer","gift","gleam","grove","guard","heart","heel","hold","kind","light","mane","might","mind","moon","path","petal","pride","rest","river","seeker","sense","shadow","shard","shine","singer","smile","song","spark","spell","spirit","star","vale","walker","watcher","whisper","wish"];

var nm14 = ["br","ph","th","tr","c","d","f","g","j","k","l","m","n","p","r","s","t","v","w","z","","","",""];
var nm15 = ["ae","ay","oe","ue","ai","ia","y","a","e","i","o","a","e","i","o"];
var nm16 = ["k","l","ll","m","n","nn","r"];
var nm17 = ["a","i"];
var nm18 = ["ll","ng","nn","th","rn","l","m","n","r","s","",""];

function nameGen(type){
	$('#placeholder').css('textTransform', 'capitalize');
	var tp = type;
	var br = "";
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		if(type === 2){
			nameChild();
			while(nMs === ""){
				nameChild();
			}
		}else{
			if(i < 5){
				rnd = Math.random() * nm12.length | 0;
				rnd2 = Math.random() * nm13.length | 0;
				while(nm12[rnd] === nm13[rnd2]){
					rnd2 = Math.random() * nm13.length | 0;
				}
				nMs = nm12[rnd] + nm13[rnd2];
			}else{
				nameSur();
				while(nMs === ""){
					nameSur();
				}
			}
			names = nMs;
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
			nMs = nMs + " " + names;
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
	rnd = Math.random() * nm3.length | 0;
	rnd2 = Math.random() * nm4.length | 0;
	nMs = nm3[rnd] + nm4[rnd2];
	testSwear(nMs);
}

function nameMas(){
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	nMs = nm1[rnd] + nm2[rnd2];
	testSwear(nMs);
}

function nameSur(){
	nTp = Math.random() * 8 | 0;
	rnd = Math.random() * nm5.length | 0;
	rnd2 = Math.random() * nm6.length | 0;
	rnd3 = Math.random() * nm7.length | 0;
	rnd4 = Math.random() * nm10.length | 0;
	rnd5 = Math.random() * nm11.length | 0;
	if(nTp < 3){
		while(nm11[rnd5] === nm7[rnd3] && nm7[rnd3] === nm5[rnd]){
			rnd3 = Math.random() * nm7.length | 0;
		}
		nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm10[rnd4] + nm11[rnd5];
	}else{
		rnd6 = Math.random() * nm8.length | 0;
		rnd7 = Math.random() * nm9.length | 0;
		while(nm11[rnd5] === nm9[rnd6] && nm9[rnd6] === nm7[rnd3]){
			rnd7 = Math.random() * nm9.length | 0;
		}
		if(nTp < 6){
			nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm8[rnd6] + nm9[rnd7] + nm10[rnd4] + nm11[rnd5];
		}else{
			rnd8 = Math.random() * nm8.length | 0;
			rnd9 = Math.random() * nm9.length | 0;
			while(nm11[rnd5] === nm9[rnd6] && nm9[rnd6] === nm9[rnd9]){
				rnd7 = Math.random() * nm9.length | 0;
			}
			while(rnd9 < 8 && rnd7 < 8){
				rnd7 = Math.random() * nm9.length | 0;
			}
			if(nTp === 6){
				nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm8[rnd6] + nm9[rnd7] + nm8[rnd8] + nm9[rnd9] + nm10[rnd4] + nm11[rnd5];
			}else{
				nMs = nm5[rnd] + nm6[rnd2] + nm9[rnd7] + nm8[rnd8] + nm7[rnd3] + nm8[rnd6] + nm9[rnd9] + nm10[rnd4] + nm11[rnd5];
			}
		}
	}
	testSwear(nMs);
}

function nameChild(){
	nTp = Math.random() * 2 | 0;
	rnd = Math.random() * nm14.length | 0;
	rnd2 = Math.random() * nm15.length | 0;
	rnd3 = Math.random() * nm18.length | 0;
	if(nTp === 0){
		if(nm14[rnd] === ""){
			while(nm18[rnd3] === ""){
				rnd3 = Math.random() * nm18.length | 0;
			}
		}
		if(nm18[rnd3] === ""){
			rnd2 = Math.random() * 7 | 0;
		}
		nMs = nm14[rnd] + nm15[rnd2] + nm18[rnd3];
	}else{
		rnd4 = Math.random() * nm16.length | 0;
		rnd5 = Math.random() * nm17.length | 0;
		nMs = nm14[rnd] + nm15[rnd2] + nm16[rnd4] + nm17[rnd5] + nm18[rnd3];
	}
	testSwear(nMs);
}