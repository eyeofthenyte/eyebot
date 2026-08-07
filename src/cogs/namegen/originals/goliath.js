var nmFF = ["Age","Ane","Are","Daa","Dau","Di","Ga","Gal","Gau","Ge","Gel","Ila","Ina","Ka","Kau","Ke","Ki","Kuo","La","Lau","Le","Lo","Maa","Man","Mau","Me","Na","Nal","Nau","Ni","No","Ola","One","Ore","Ori","Pa","Paa","Pau","Pe","Tha","Thau","The","Thu","Vaa","Vau","Ve","Vo","Vu","Za","Zaa","Zau","Zo"];
var nmFL = ["gea","geo","ggeo","ghu","gia","gu","kea","keo","kha","ki","kia","kio","kko","la","lai","lane","lea","leo","lo","lu","ma","meo","mi","mia","ne","nea","neo","ni","nia","nna","nnio","nu","peo","peu","pu","rea","rheo","ri","ria","rra","rrea","the","thea","thi","thia","thio","thu","vea","vi","via","vu"];
var nmMF = ["Ag","Apa","Ar","Au","Aug","Aur","Eag","Eg","Erg","Ga","Gau","Gea","Gha","Gra","Ila","Ili","Ira","Kana","Kava","Kaza","Keo","Khu","Kora","Kra","La","Lau","Laza","Loro","Ma","Mara","Mau","Mea","Mo","Na","Nara","Nau","Neo","Pa","Pu","Tara","Tau","Tha","Thava","Tho","Va","Vara","Vau","Vaura","Vega","Vi","Vo","Za","Zau"];
var nmML = ["dak","dath","dhan","gak","gal","gan","gath","ghan","gith","glath","gun","kan","kein","khal","kin","kon","lath","lig","lok","mahg","mahk","mahl","mak","man","mith","mul","nak","nath","nihl","noth","path","phak","rad","rath","rein","rhak","rhan","riak","rian","rin","rok","roth","thag","thak","tham","thi","thok","veith","vek","vhal","vhik","vith","voi","zak","ziath"];
var nmMdF = ["Adept","Bear","Brave","Bright","Dawn","Day","Deer","Dream","Flint","Fearless","Flower","Food","Fright","Goat","Hard","Hide","High","Honest","Horn","Keen","Lone","Long","Low","Lumber","Master","Mind","Mountain","Night","Rain","River","Rock","Root","Silent","Sky","Sly","Smart","Steady","Stone","Storm","Strong","Swift","Thread","Thunder","Tree","Tribe","True","Truth","Wander","Wild","Wise","Wound"];
var nmMdL = ["aid","bearer","breaker","caller","carver","chaser","climber","cook","dream","drifter","eye","finder","fist","friend","frightener","guard","hand","hauler","heart","herder","hunter","jumper","killer","lander","leader","leaper","logger","maker","mender","picker","runner","shot","smasher","speaker","stalker","striker","tanner","twister","vigor","walker","wanderer","warrior","watcher","weaver","worker"];
var nmSF= ["Agu-Ul","Agu-V","Anakal","Apuna-M","Athun","Egena-V","Egum","Elan","Ganu-M","Gathak","Gean","Inul","Kalag","Kaluk","Katho-Ol","Kolae-G","Kolak","Kulan","Kulum","Lakum","Maluk","Munak","Muthal","Nalak","Nola-K","Nugal","Nulak","Ogol","Oveth","Thenal","Thul","Thunuk","Ugun","Uthenu-K","Vaimei-L","Valu-N","Vathun","Veom","Vuma-Th","Vunak"];
var nmSL = ["aga","ageane","akane","akanu","akume","alathi","amino","amune","anathi","atake","athai","athala","atho","avea","avi","avone","eaku","ekali","elo","iaga","iago","iala","iano","igala","igane","igano","igo","igone","ileana","ithino","olake","ugate","ugoni","ukane","ukate","ukena","ulane","upine","utha","uthea"];

function nameGen(type){
	var tp = type;
	var br = "";
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		rnd = Math.floor(Math.random() * nmMdF.length);
		rnd2 = Math.floor(Math.random() * nmMdL.length);
		rnd3 = Math.floor(Math.random() * nmSF.length);
		rnd4 = Math.floor(Math.random() * nmSL.length);
		nSr = nmMdF[rnd] + nmMdL[rnd2] + " " + nmSF[rnd3] + nmSL[rnd4];
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
		nMs = nMs + " " + nSr;
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
	rnd = Math.floor(Math.random() * nmFF.length);
	rnd2 = Math.floor(Math.random() * nmFL.length);
	nMs = nmFF[rnd] + nmFL[rnd2];
	testSwear(nMs);
}

function nameMas(){
	rnd = Math.floor(Math.random() * nmMF.length);
	rnd2 = Math.floor(Math.random() * nmML.length);
	nMs = nmMF[rnd] + nmML[rnd2];
	testSwear(nMs);
}