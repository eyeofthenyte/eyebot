var nm1 = ["Al","Ari","Bil","Bri","Cal","Cor","Dav","Dor","Eni","Er","Far","Fel","Ga","Gra","His","Hor","Ian","Ipa","Je","Jor","Kas","Kel","Lan","Lo","Man","Mer","Nes","Ni","Or","Oru","Pana","Po","Qua","Quo","Ras","Ron","Sa","Sal","Sin","Tan","To","Tra","Um","Uri","Val","Vor","War","Wil","Wre","Xal","Xo","Ye","Yos","Zan","Zil"];
var nm2 = ["bar","ben","bis","corin","cryn","don","dri","fan","fiz","gim","grim","hik","him","ji","jin","kas","kur","len","lin","min","mop","morn","nan","ner","ni","pip","pos","rick","ros","rug","ryn","ser","ston","tix","tor","ver","vyn","win","wor","xif","xim","ybar","yur","ziver","zu"];
var nm3 = ["Alu","Ari","Ban","Bree","Car","Cel","Daphi","Do","Eili","El","Fae","Fen","Fol","Gal","Gren","Hel","Hes","Ina","Iso","Jel","Jo","Klo","Kri","Lil","Lori","Min","My","Ni","Ny","Oda","Or","Phi","Pri","Qi","Que","Re","Rosi","Sa","Sel","Spi","Ta","Tifa","Tri","Ufe","Uri","Ven","Vo","Wel","Wro","Xa","Xyro","Ylo","Yo","Zani","Zin"];
var nm4 = ["bi","bys","celi","ci","dira","dysa","fi","fyx","gani","gyra","hana","hani","kasys","kini","la","li","lin","lys","mila","miphi","myn","myra","na","niana","noa","nove","phina","pine","qaryn","qys","rhana","roe","sany","ssa","sys","tina","tra","wyn","wyse","xi","xis","yaris","yore","za","zyre"];

var nm5 = ["","","b","d","f","g","h","l","m","n","p","r","s","t","w","z"];
var nm6 = ["ae","oo","ee","aa","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u","a","e","i","o","u"];
var nm7 = ["bbl","ckl","f","ff","ggl","kk","lb","lk","ln","lr","lw","mb","ml","mm","mml","mp","mpl","nb","ng","ngg","nn","np","p","pl","pp","r","rc","rg","rk","rn","rr","s","sg","sgr"];
var nm8 = ["a","a","e","e","i","o","u"];
var nm9 = ["b","d","n","r","s","t"];
var nm10 = ["a","e","e","i","o"];
var nm11 = ["","","ck","g","l","l","ll","mp","n","n","n","nd","r","r","rs","s","s"];
var nm12 = ["bl","bbl","ckl","dl","ddl","ggl","gl","mbl","mpl","pl","ppl"];

var nm13 = ["babble","baffle","bellow","belly","berry","billow","bold","boon","brass","brisk","broad","bronze","cobble","copper","dapple","dark","dazzle","deep","fapple","fiddle","fine","fizzle","flicker","fluke","glitter","gobble","gold","iron","kind","last","light","long","loud","lucky","marble","pale","pebble","puddle","quick","quiet","quill","shadow","short","silver","single","sparkle","spring","squiggle","stark","stout","strong","swift","thistle","thunder","tinker","toggle","tossle","true","twin","twist","waggle","whistle","wiggle","wild","wobble"];
var nm14 = ["back","badge","belch","bell","belt","bit","block","bonk","boot","boots","bottom","braid","branch","brand","case","cheek","cloak","collar","cord","craft","crag","diggles","drop","dust","dwadle","fall","feast","fen","fern","field","firn","flight","flow","front","gem","gift","grace","guard","hand","heart","helm","hide","hold","kind","ligt","lob","mane","mantle","mask","patch","peak","pitch","pocket","reach","rest","river","rock","shield","song","span","spark","spell","spring","stamp","stand","stitch","stone","thread","top","trick","twist","wander"];

function nameGen(type){
	$('#placeholder').css('textTransform', 'capitalize');
	var tp = type;
	var br = "";
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		if(i < 5){
			rnd = Math.random() * nm13.length | 0;
			rnd2 = Math.random() * nm14.length | 0;
			while(nm13[rnd] === nm14[rnd2]){
				rnd2 = Math.random() * nm14.length | 0;
			}
			nMs = nm13[rnd] + nm14[rnd2];
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
	if(nTp < 2){
		rnd = Math.random() * nm5.length | 0;
		rnd2 = Math.random() * nm10.length | 0;
		rnd3 = Math.random() * nm12.length | 0;
		rnd4 = Math.random() * nm5.length | 0;
		rnd5 = Math.random() * nm10.length | 0;
		while(nm5[rnd] === ""){
			rnd = Math.random() * nm5.length | 0;
		}
		while(nm5[rnd4] === ""){
			rnd4 = Math.random() * nm5.length | 0;
		}
		nMs = nm5[rnd] + nm10[rnd2] + nm12[rnd3] + "e" + nm5[rnd4] + nm10[rnd5] + nm12[rnd3] + "e";
	}else{
		rnd = Math.random() * nm5.length | 0;
		rnd2 = Math.random() * nm6.length | 0;
		rnd3 = Math.random() * nm7.length | 0;
		rnd4 = Math.random() * nm8.length | 0;
		rnd5 = Math.random() * nm11.length | 0;
		if(nTp < 3){
			while(nm7[rnd3] === nm5[rnd] || nm7[rnd3] === nm11[rnd5]){
				rnd3 = Math.random() * nm7.length | 0;
			}
			nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm8[rnd4] + nm11[rnd5];
		}else{
			rnd6 = Math.random() * nm9.length | 0;
			rnd7 = Math.random() * nm10.length | 0;
			while(nm7[rnd3] === nm9[rnd6] || nm9[rnd6] === nm11[rnd5]){
				rnd6 = Math.random() * nm9.length | 0;
			}
			if(nTp < 5){
				nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm8[rnd4] + nm9[rnd6] + nm10[rnd7] + nm11[rnd5];
			}else{
				rnd8 = Math.random() * nm9.length | 0;
				rnd9 = Math.random() * nm10.length | 0;
				while(nm7[rnd3] === nm9[rnd8] || nm9[rnd6] === nm9[rnd8]){
					rnd8 = Math.random() * nm9.length | 0;
				}
				nMs = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm8[rnd4] + nm9[rnd6] + nm10[rnd7] + nm9[rnd8] + nm10[rnd9] + nm11[rnd5];
			}
		}
	}
	testSwear(nMs);
}