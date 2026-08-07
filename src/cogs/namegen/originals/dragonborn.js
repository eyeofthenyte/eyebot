var nm1 = ["Ali","Ar","Ba","Bal","Bel","Bha","Bren","Caer","Calu","Dur","Do","Dra","Era","Faer","Fro","Gre","Ghe","Gora","He","Hi","Ior","Jin","Jar","Kil","Kriv","Lor","Lumi","Mar","Mor","Med","Nar","Nes","Na","Oti","Orla","Pri","Pa","Qel","Ravo","Ras","Rho","Sa","Sha","Sul","Taz","To","Trou","Udo","Uro","Vor","Vyu","Vrak","Wor","Wu","Wra","Wul","Xar","Yor","Zor","Zra"];
var nm2 = ["barum","bor","broth","ciar","crath","daar","dhall","dorim","farn","fras","gar","ghull","grax","hadur","hazar","jhan","jurn","kax","kris","kul","lasar","lin","mash","morn","naar","prax","qiroth","qrin","qull","rakas","rash","rinn","roth","sashi","seth","skan","trin","turim","varax","vroth","vull","warum","wunax","xan","xiros","yax","ythas","zavur","zire","ziros"];
var nm3 = ["Ari","A","Bi","Bel","Cris","Ca","Drys","Da","Erli","Esh","Fae","Fen","Gur","Gri","Hin","Ha","Irly","Irie","Jes","Jo","Ka","Kel","Ko","Lilo","Lora","Mal","Mi","Na","Nes","Nys","Ori","O","Ophi","Phi","Per","Qi","Quil","Rai","Rashi","So","Su","Tha","Ther","Uri","Ushi","Val","Vyra","Welsi","Wra","Xy","Xis","Ya","Yr","Zen","Zof"];
var nm4 = ["birith","bis","bith","coria","cys","dalynn","drish","drith","faeth","fyire","gil","gissa","gwen","hime","hymm","karyn","kira","larys","liann","lyassa","meila","myse","norae","nys","patys","pora","qorel","qwen","rann","riel","rina","rinn","rish","rith","saadi","shann","sira","thibra","thyra","vayla","vyre","vys","wophyl","wyn","xiris","xora","yassa","yries","zita","zys"];

var nm5 = ["","","","","c","cl","cr","d","dr","f","g","k","kl","kr","l","m","my","n","ny","pr","sh","t","th","v","y"];
var nm6 = ["a","e","i","a","e","i","o","u","a","e","i","a","e","i","o","u","a","e","i","a","e","i","o","u","aa","ia","ea","ua","uu"];
var nm7 = ["c","cc","ch","lm","lk","lx","ld","lr","ldr","lt","lth","mb","mm","mp","mph","mr","mt","nk","nx","nc","p","ph","r","rd","rj","rn","rrh","rth","st","tht","x"];
var nm8 = ["c","cm","cn","d","j","k","km","l","n","nd","ndr","nk","nsht","nth","r","s","sht","shkm","st","t","th","x"];
var nm9 = ["d","j","l","ll","m","n","nd","rg","r","rr","rd"];
var nm10 = ["c","d","k","l","n","r","s","sh","th"];

var nm12 = ["Barrel","Bed","Bow","Chair","Door","Plank","Plate","Roof","Room","Shelf","Shield","Spoon","Staff","Steel","Table","Tree","Wall","Wood"];
var nm13 = ["bender","biter","breaker","carver","chomper","crumbler","cruncher","crusher","cutter","gnawer","masher","nibbler","piercer","razer","scraper","scratcher","scrawler","snapper","squasher","wrecker"];

function nameGen(type){
	var nm11 = ["Able","Adamant","Adapter","Ambitious","Amuser","Analyzer","Babbler","Baffler","Barger","Basher","Battler","Bender","Binder","Biter","Blunderer","Bouncer","Bragger","Brawler","Brilliant","Bruiser","Bustler","Cackler","Calm","Caring","Charger","Chomper","Chuckler","Cleaver","Climber","Clinker","Composed","Cougher","Courageous","Courteous","Crackler","Crawler","Creative","Crumbler","Cruncher","Crusher","Dancer","Dangerous","Defender","Delightful","Devourer","Devout","Discreet","Diver","Dodger","Draconian","Dreamer","Drifter","Elegant","Enchanter","Enchanting","Energizer","Esteemed","Evader","Exalted","Fainter","Faithful","Faker","Favorable","Favoured","Fearless","Feigner","Flexer","Flincher","Flouncer","Flourisher","Folder","Follower","Forger","Fortunate","Frowner","Fumbler","Gatherer","Giggler","Glamorous","Glider","Gobbler","Grabber","Graceful","Gracious","Grappler","Grasper","Grounded","Growler","Grunter","Harmonious","Heartfelt","Heckler","Helper","Honorable","Hopeful","Humorous","Innocent","Intrepid","Joyous","Jumper","Kindhearted","Laugher","Launcher","Leaper","Limper","Lovable","Lunger","Lurker","Majestic","Marcher","Meddler","Mumbler","Murmurer","Mysterious","Napper","Nibbler","Nuzzler","Peaceful","Pious","Pouncer","Powerful","Proud","Puffer","Radiant","Reflective","Rester","Roarer","Rustler","Seeker","Serene","Serious","Shifter","Shusher","Silent","Sleeper","Sloucher","Smiler","Smoocher","Snuggler","Sophisticated","Spirited","Sprinter","Stamper","Stumbler","Tackler","Taunter","Thunderous","Tickler","Trampler","Trembler","Trustworthy","Truthful","Tumbler","Vigilant","Wanderer","Wandering","Whisperer","Zealous"];
	$('#placeholder').css('textTransform', 'capitalize');
	var tp = type;
	var br = "";
	var element = document.createElement("div");
	element.setAttribute("id", "result");
	
	for(i = 0; i < 10; i++){
		if(tp === 2){
			nTp = Math.random() * 4 | 0;
			if(nTp === 0){
				rnd = Math.random() * nm12.length | 0 ;
				rnd2 = Math.random() * nm13.length | 0 ;
				name = nm12[rnd] + nm13[rnd2];
			}else{
				rnd = Math.random() * nm11.length | 0 ;
				name = nm11[rnd];
				nm11.splice(rnd, 1);
			}
		}else{
			nameSur();
			while(nSr === ""){
				nameSur();
			}
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
			var name = nSr + " " + nMs;
		}
		br = document.createElement('br');	
		element.appendChild(document.createTextNode(name));
		element.appendChild(br);
	}
	if(document.getElementById("result")){
		document.getElementById("placeholder").removeChild(document.getElementById("result"));
	}		
	document.getElementById("placeholder").appendChild(element);
}
function nameFem(){
	rnd = Math.random() * nm3.length | 0 ;
	rnd2 = Math.random() * nm4.length | 0 ;
	nMs = nm3[rnd] + nm4[rnd2];
	testSwear(nMs);
}

function nameMas(){
	rnd = Math.random() * nm1.length | 0 ;
	rnd2 = Math.random() * nm2.length | 0 ;
	nMs = nm1[rnd] + nm2[rnd2];
	testSwear(nMs);
}
function nameSur(){
	ntp = Math.random() * 10 | 0;
	rnd = Math.random() * nm5.length | 0 ;
	rnd2 = Math.random() * nm6.length | 0 ;
	rnd3 = Math.random() * nm7.length | 0 ;
	rnd4 = Math.random() * nm6.length | 0 ;
	rnd5 = Math.random() * nm10.length | 0 ;
	while(nm7[rnd3] === nm5[rnd] || nm7[rnd3] === nm10[rnd5]){
		rnd3 = Math.random() * nm7.length | 0 ;
	}
	if(ntp < 4){
		nSr = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm6[rnd4] + nm10[rnd5];
	}else{
		rnd6 = Math.random() * nm6.length | 0 ;
		rnd7 = Math.random() * nm8.length | 0 ;
		while(nm7[rnd3] === nm8[rnd7] || nm8[rnd7] === nm10[rnd5]){
			rnd7 = Math.random() * nm8.length | 0 ;
		}
		if(ntp < 7){
			nSr = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm6[rnd4] + nm8[rnd7] + nm6[rnd6] + nm10[rnd5];
		}else{
			rnd8 = Math.random() * nm6.length | 0 ;
			rnd9 = Math.random() * nm9.length | 0 ;
			while(nm9[rnd9] === nm8[rnd7] || nm9[rnd9] === nm10[rnd5]){
				rnd9 = Math.random() * nm9.length | 0 ;
			}
			nSr = nm5[rnd] + nm6[rnd2] + nm7[rnd3] + nm6[rnd4] + nm8[rnd7] + nm6[rnd6] + nm9[rnd9] + nm6[rnd8] + nm10[rnd5];
		}
	}
	testSwear(nSr);
}