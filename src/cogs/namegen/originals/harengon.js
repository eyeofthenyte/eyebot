var nm1 = ["Ad","Ae","Bal","Bei","Car","Cra","Dae","Dor","El","Ela","Er","Far","Fen","Gen","Glyn","Hei","Her","Ian","Ili","Kea","Kel","Leo","Lu","Mira","Mor","Nae","Nor","Olo","Oma","Pa","Per","Pet","Qi","Qin","Ralo","Ro","Sar","Syl","The","Tra","Ume","Uri","Va","Vir","Waes","Wran","Yel","Yin","Zin","Zum"];
var nm2 = ["balar","beros","can","ceran","dan","dithas","faren","fir","geiros","golor","hice","horn","jeon","jor","kas","kian","lamin","lar","len","maer","maris","menor","myar","nan","neiros","nelis","norin","peiros","petor","qen","quinal","ran","ren","ric","ris","ro","salor","sandoral","toris","tumal","valur","ven","warin","wraek","xalim","xidor","yarus","ydark","zeiros","zumin"];
var nm3 = ["Ad","Ara","Bi","Bry","Cai","Chae","Da","Dae","Eil","En","Fa","Fae","Gil","Gre","Hele","Hola","Iar","Ina","Jo","Key","Kris","Lia","Lora","Mag","Mia","Neri","Ola","Ori","Phi","Pres","Qi","Qui","Rava","Rey","Sha","Syl","Tor","Tris","Ula","Uri","Val","Ven","Wyn","Wysa","Xil","Xyr","Yes","Ylla","Zin","Zyl"];
var nm4 = ["banise","bella","caryn","cyne","di","dove","fiel","fina","gella","gwyn","hana","harice","jyre","kalyn","krana","lana","lee","leth","lynn","moira","mys","na","nala","phine","phyra","qirelle","ra","ralei","rel","rie","rieth","rona","rora","roris","satra","stina","sys","thana","thyra","tris","varis","vyre","wenys","wynn","xina","xisys","ynore","yra","zana","zorwyn"];

var nm5 = ["","","b","br","d","dr","g","j","l","m","n","r","t","th","tr","v","z"];
var nm6 = ["a","e","i","o","u","a","e","o"];
var nm7 = ["b","b","bb","br","d","d","dd","dr","g","g","gd","gl","l","l","ld","ll","ln","lm","lr","m","m","mm","mn","n","n","nb","nd","nn","r","r","rd","rl","rn","rr","rv","v","v","vl","vr","z","z","zd","zl","zn","zz"];
var nm8 = ["a","e","i","o","a","e","o","i","a","e","o","u"];
var nm9 = ["b","d","g","l","ll","m","n","nn","r","v","z"];
var nm10 = ["","h","k","l","n","r","t"];

function nameGen(type){
	$('#placeholder').css('textTransform', 'capitalize');
	var tp = type;
	var br = "";
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		if(tp === 1){
			if(i < 6){
				nameFem();
				while(nMs === ""){
					nameFem();
				}
			}else{
				nameFemT();
				while(nMs === ""){
					nameFemT();
				}
			}
		}else{
			if(i < 6){
				nameFem();
				while(nMs === ""){
					nameFem();
				}
			}else{
				nameMasT();
				while(nMs === ""){
					nameMasT();
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
function nameFem(){
	nTp = Math.random() * 3 | 0;
	rnd = Math.random() * nm5.length | 0;
	rnd2 = Math.random() * nm6.length | 0;
	rnd3 = Math.random() * nm7.length | 0;
	rnd4 = Math.random() * nm8.length | 0;
	rnd5 = Math.random() * nm10.length | 0;
	while(nm7[rnd3] === nm5[rnd] && nm10[rnd5]){
		rnd3 = Math.random() * nm7.length | 0;
	}
	if(nTp < 2){
		nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm8[rnd4] + nm10[rnd5];
	}else{
		nTp = Math.random() * 2 | 0;
		rnd6 = Math.random() * nm8.length | 0;
		rnd7 = Math.random() * nm9.length | 0;
		if(nTp === 0){
			nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm8[rnd4] + nm9[rnd7] + nm8[rnd6] + nm10[rnd5];
		}else{
			nMs = nm5[rnd] + nm6[rnd2] + nm9[rnd7] + nm8[rnd6] + nm7[rnd3] + nm8[rnd4] + nm10[rnd5];
		}
	}
	testSwear(nMs);
}

function nameFemT(){
	rnd = Math.random() * nm3.length | 0;
	rnd2 = Math.random() * nm4.length | 0;
	nMs = nm3[rnd] + nm4[rnd2];
	testSwear(nMs);
}

function nameMasT(){
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	nMs = nm1[rnd] + nm2[rnd2];
	testSwear(nMs);
}