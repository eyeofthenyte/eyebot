var nm1 = ["b","c","ch","d","g","gh","h","k","kh","l","m","n","s","t","v","z"];
var nm2 = ["a","e","o","a","e","o","i"];
var nm3 = ["l","n","r","s","v","w","y","z"];
var nm4 = ["a","a","e","i","i","o"];
var nm5 = ["ulad","hareth","khad","kosh","melk","tash","vash"];
var nm6 = ["ashana","ashtai","ishara","nari","tara","vakri"];

var nm7 = ["Ad","Ae","Bal","Bei","Car","Cra","Dae","Dor","El","Ela","Er","Far","Fen","Gen","Glyn","Hei","Her","Ian","Ili","Kea","Kel","Leo","Lu","Mira","Mor","Nae","Nor","Olo","Oma","Pa","Per","Pet","Qi","Qin","Ralo","Ro","Sar","Syl","The","Tra","Ume","Uri","Va","Vir","Waes","Wran","Yel","Yin","Zin","Zum"];
var nm8 = ["balar","beros","can","ceran","dan","dithas","faren","fir","geiros","golor","hice","horn","jeon","jor","kas","kian","lamin","lar","len","maer","maris","menor","myar","nan","neiros","nelis","norin","peiros","petor","qen","quinal","ran","ren","ric","ris","ro","salor","sandoral","toris","tumal","valur","ven","warin","wraek","xalim","xidor","yarus","ydark","zeiros","zumin"];
var nm9 = ["Ad","Ara","Bi","Bry","Cai","Chae","Da","Dae","Eil","En","Fa","Fae","Gil","Gre","Hele","Hola","Iar","Ina","Jo","Key","Kris","Lia","Lora","Mag","Mia","Neri","Ola","Ori","Phi","Pres","Qi","Qui","Rava","Rey","Sha","Syl","Tor","Tris","Ula","Uri","Val","Ven","Wyn","Wysa","Xil","Xyr","Yes","Ylla","Zin","Zyl"];
var nm10 = ["banise","bella","caryn","cyne","di","dove","fiel","fina","gella","gwyn","hana","harice","jyre","kalyn","krana","lana","lee","leth","lynn","moira","mys","na","nala","phine","phyra","qirelle","ra","ralei","rel","rie","rieth","rona","rora","roris","satra","stina","sys","thana","thyra","tris","varis","vyre","wenys","wynn","xina","xisys","ynore","yra","zana","zorwyn"];

var br = "";

function nameGen(type){
	var tp = type;
	$('#placeholder').css('textTransform', 'capitalize');
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		if(i < 5){
			nameMas();
			while(nMs === ""){
				nameMas();
			}
			if(tp === 1){
				rnd = Math.random() * 3 | 0;
				if(nTp === 0 || nTp === 3){
					nMs = nMs + nm6[rnd];
				}else{
					rnd += 3;
					nMs = nMs + nm6[rnd];
				}
			}else{
				if(nTp === 0 || nTp === 3){
					nMs = nMs + nm5[0];
				}else{
					rnd = Math.random() * 5 | 0;
					nMs = nMs + nm5[rnd + 1];
				}
			}
		}else{
			if(tp === 1){
				nameSec();
				while(nMs === ""){
					nameSec();
				}
			}else{
				nameFir();
				while(nMs === ""){
					nameFir();
				}
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
	nTp = Math.random() * 4 | 0;
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	if(nTp < 2){
		if(nTp === 0){
			nMs = nm1[rnd];
		}else{
			nMs = nm1[rnd] + nm2[rnd2];
		}
	}else{
		rnd3 = Math.random() * nm3.length | 0;
		rnd4 = Math.random() * nm4.length | 0;
		if(nTp === 2){
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3];
		}else{
			nMs = nm1[rnd] + nm2[rnd2] + nm3[rnd3] + nm4[rnd4];
		}
	}
	testSwear(nMs);
}

function nameFir(){
	rnd = Math.random() * nm7.length | 0;
	rnd2 = Math.random() * nm8.length | 0;
	nMs = nm7[rnd] + nm8[rnd2];
	testSwear(nMs);
}

function nameSec(){
	rnd = Math.random() * nm9.length | 0;
	rnd2 = Math.random() * nm10.length | 0;
	nMs = nm9[rnd] + nm10[rnd2];
	testSwear(nMs);
}