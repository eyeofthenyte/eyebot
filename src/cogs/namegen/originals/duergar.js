var nm1 = ["Ad","Am","Arm","Baer","Daer","Bal","Ban","Bar","Bel","Ben","Ber","Bhal","Bhar","Bhel","Bram","Bran","Brom","Brum","Bun","Dal","Dar","Dol","Dul","Eb","Em","Erm","Far","Gal","Gar","Ger","Gim","Gral","Gram","Gran","Grem","Gren","Gril","Gry","Gul","Har","Hjal","Hjol","Hjul","Hor","Hul","Hur","Kar","Khar","Kram","Krom","Krum","Mag","Mal","Mel","Mor","Muir","Mur","Rag","Ran","Reg","Rot","Thal","Thar","Thel","Ther","Tho","Thor","Thul","Thur","Thy","Tor","Ty","Um","Urm","Von"];
var nm2 = ["adin","bek","brek","dahr","dain","dal","dan","dar","dek","dir","dohr","dor","drak","dram","dren","drom","drum","drus","duhr","dur","dus","garn","gram","gran","grim","grom","gron","grum","grun","gurn","gus","iggs","kahm","kam","kohm","kom","kuhm","kum","kyl","man","mand","mar","mek","miir","min","mir","mond","mor","mun","mund","mur","mus","myl","myr","nam","nar","nik","nir","nom","num","nur","nus","nyl","rak","ram","ren","rig","rigg","rik","rim","rom","ron","rum","rus","ryl","tharm","tharn","thran","thrum","thrun"];
var nm3 = ["An","Ar","Baer","Bar","Bel","Belle","Bon","Bonn","Braen","Bral","Bralle","Bran","Bren","Bret","Bril","Brille","Brol","Bron","Brul","Bryl","Brylle","Bryn","Bryt","Byl","Bylle","Daer","Dear","Dim","Ed","Ein","El","Gem","Ger","Gwan","Gwen","Gwin","Gwyn","Gym","Ing","Jen","Jenn","Jin","Jyn","Kait","Kar","Kat","Kath","Ket","Las","Lass","Les","Less","Lyes","Lys","Lyss","Maer","Maev","Mar","Mis","Mist","Myr","Mys","Myst","Naer","Nal","Nas","Nass","Nes","Nis","Nys","Raen","Ran","Red","Reyn","Run","Ryn","Sar","Sol","Tas","Taz","Tis","Tish","Tiz","Tor","Tys","Tysh"];
var nm4 = ["belle","bera","delle","deth","dielle","dille","dish","dora","dryn","dyl","giel","glia","glian","gwyn","la","leen","leil","len","lin","linn","lyl","lyn","lynn","ma","mera","mora","mura","myl","myla","nan","nar","nas","nera","nia","nip","nis","niss","nora","nura","nyl","nys","nyss","ra","ras","res","ri","ria","rielle","rin","ris","ros","ryl","ryn","sael","selle","sora","syl","thel","thiel","tin","tyn","va","van","via","vian","waen","win","wyn","wynn"];

var nm5 = ["b","br","c","d","dr","f","g","gl","gr","h","l","m","r","str","t","thr"];
var nm6 = ["ae","a","e","o","u","a","e","o","u","a","e","o","u","a","e","o","u"];
var nm7 = ["br","d","fd","h","k","lbr","ld","ll","mn","ng","nh","nk","r","rd","rth","tg","thg","zz"];
var nm8 = ["a","e","i","o","u"];
var nm9 = ["g","h","k","n","r","v"];
var nm10 = ["a","a","e","e","i","o","u"];
var nm11 = ["ck","g","hk","hr","k","ln","m","n","nn","r","rk","rr","rt"];

var nm12 = ["ash","barren","battle","black","blast","blind","blood","bold","bone","bright","broad","broken","bronze","burn","craven","dark","doom","earth","fire","flame","flint","fore","forge","giant","goblin","gore","grave","grim","hell","hollow","iron","keen","knife","mad","mind","molten","neck","onyx","ore","proud","rage","red","rock","rune","rust","shadow","silent","skull","stark","steel","stone","storm","stout","thunder","troll","under","venge","vice","war","wicked","wild","wrath"];
var nm13 = ["axe","basher","battle","beard","belch","belcher","belt","blade","bleeder","boot","boots","braid","brand","breaker","breath","bringer","brow","buster","chain","chains","champion","chewer","cleaver","crag","crusher","drum","dust","earth","eater","edge","eye","fall","favor","feast","fight","fist","flayer","flow","force","forge","fury","gift","gore","grace","guard","hammer","hand","handle","head","heart","helm","hold","honor","horn","hunt","hunter","lord","mantle","march","mask","master","might","minder","pass","past","pride","reach","rest","ripper","rock","runner","slayer","slice","snapper","sorrow","spite","stand","stone","storm","strike","striker","tale","tamer","ward"];

function nameGen(type){
	$('#placeholder').css('textTransform', 'capitalize');
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
		rnd = Math.random() * nm12.length | 0;
		rnd2 = Math.random() * nm13.length | 0;
		while(nm12[rnd] === nm13[rnd2]){
			rnd2 = Math.random() * nm13.length | 0;
		}
		nMs = nMs + " " + nm12[rnd] + nm13[rnd2];
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
}

function nameMas(){
	rnd = Math.random() * nm1.length | 0;
	rnd2 = Math.random() * nm2.length | 0;
	nMs = nm1[rnd] + nm2[rnd2];
}

function nameSur(){
	nTp = Math.random() * 2 | 0;
	rnd = Math.random() * nm5.length | 0;
	rnd2 = Math.random() * nm6.length | 0;
	rnd3 = Math.random() * nm7.length | 0;
	rnd4 = Math.random() * nm10.length | 0;
	rnd5 = Math.random() * nm11.length | 0;
	if(nTp === 0){
		while(nm11[rnd5] === nm7[rnd3] && nm7[rnd3] === nm5[rnd]){
			rnd3 = Math.random() * nm7.length | 0;
		}
		nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm10[rnd4] + nm11[rnd5];
	}else{
		rnd6 = Math.random() * nm8.length | 0;
		rnd7 = Math.random() * nm9.length | 0;
		while(nm11[rnd5] === nm9[rnd6] && nm9[rnd6] === nm7[rnd3]){
			rnd6 = Math.random() * nm9.length | 0;
		}
		nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm8[rnd6] + nm9[rnd7] + nm10[rnd4] + nm11[rnd5];
	}
}