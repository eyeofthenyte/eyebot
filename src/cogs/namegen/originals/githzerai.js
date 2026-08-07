var nm1 = ["Am","Ar","Ara","Aza","Bar","Bra","Bran","Bru","Da","Dar","Dor","Dra","Dro","Du","Duu","Fa","Far","Fe","Fer","Fur","Gan","Gra","Gran","Gre","Gro","Gru","Hra","Hu","Ka","Kar","Kha","Kra","Kro","Ma","Mar","Mu","Muu","Na","Nar","Nir","Nu","On","Or","Ora","Oro","Ra","Ran","Rhu","Rin","Ru","Sa","Sha","Shra","Sra","Un","Una","Ur","Ura","Xa","Xha","Xo","Zar","Zra"];
var nm2 = ["d","d","d","dahn","dak","dar","dh","dh","dh","dran","gahr","gh","gh","gh","gor","k","k","kh","kh","kahr","kar","khar","kiak","kk","kk","kk","kk","kk","kran","lag","lahr","lian","lid","lis","lla","llak","loth","mag","mak","miak","mir","nag","nak","niar","nod","rad","rag","rak","ram","rath","rek","rg","rg","rg","rg","rm","rm","rm","rm","rra","rth","rth","rth","rth","ruk","rzth","rzth","rzth","tar","th","th","th","th","tig","zad","zag","zak","zar","zeg","zirg","zth"];
var nm3 = ["Ad","Alm","Ar","Arw","Ash","Dah","Dhar","Dolm","Dran","El","Ell","Erzh","Esz","Ezh","Genr","Grel","Grin","Halm","Han","Harn","Heln","Ihr","Iln","Imm","Immil","Iz","Jan","Kan","Kharm","Khaz","Krez","Laz","Lez","Lhash","Lir","Lor","Magd","Marm","Meir","Mir","Nagr","Nah","Nalm","Nash","Niar","Ohn","Or","Rasz","Rez","Sham","Sharm","Shund","Sil","Um","Ur","Uw","Vith"];
var nm4 = ["a","ah","aka","al","alin","alla","ane","anith","anya","arah","arin","aya","ayah","ayis","eah","eka","ekus","el","ela","elna","elya","elzal","ena","enah","era","erah","erath","erra","eth","eya","ihn","ila","ilias","ilzin","in","ina","ines","ira","iren","iris","ith","iza","la","mina","mira","nara","nel","nera","nia","niya","ra","ya","yara","zin"];

function nameGen(type){
	var tp = type;
	var br = "";
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
	rnd = Math.floor(Math.random() * nm3.length);
	rnd2 = Math.floor(Math.random() * nm4.length);
	charL = nm3[rnd].charAt(nm3[rnd].length -1);
	charF = nm4[rnd2].charAt(0);
	while(charL === charF){
		rnd2 = Math.floor(Math.random() * nm4.length);
		charF = nm4[rnd2].charAt(0);
	}
	nMs = nm3[rnd] + nm4[rnd2];
	testSwear(nMs);
}

function nameMas(){
	rnd = Math.floor(Math.random() * nm1.length);
	rnd2 = Math.floor(Math.random() * nm2.length);
	charL = nm1[rnd].charAt(nm1[rnd].length -1);
	charF = nm2[rnd2].charAt(0);
	while(charL === charF){
		rnd2 = Math.floor(Math.random() * nm2.length);
		charF = nm2[rnd2].charAt(0);
	}
	nMs = nm1[rnd] + nm2[rnd2];
	testSwear(nMs);
}